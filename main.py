from chromadb import Client as ChromaClient
import numpy as np
import argparse
import os
import pickle
import pandas as pd
import lightgbm as lgb
import requests
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

# -------------------------------
# Helper imports (your own modules)
# -------------------------------
from KNOWLEDGE_EXTRACTOR.churn_feature_extractor import extract_churn_features
from SLM_manager.churn_predictor import load_churn_model, predict_churn
from TEXT_EMBEDDING_MODEL.customer_embedding import get_customer_embedding, build_customer_summary


# -------------------------------
# Gemini API call
# -------------------------------
def call_gemini_for_explanation(prompt: str, api_key: str) -> str:
    """Send prompt to Gemini API for churn driver summarization."""
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 512}
    }
    params = {"key": api_key}
    try:
        response = requests.post(url, headers=headers, params=params, json=data, timeout=30)
        response.raise_for_status()
        result = response.json()
        return result["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return f"Gemini API error: {e}"


# -------------------------------
# Main entry point
# -------------------------------
def main():
    parser = argparse.ArgumentParser(description="SaaS Churn RAG Pipeline")
    parser.add_argument('--csv', type=str, help='Path to customer activity CSV')
    parser.add_argument('--topk', type=int, default=5, help='Number of top risk customers to show')
    parser.add_argument('--gemini_api_key', type=str, required=False, help='Gemini API key for summarization (optional if in .env)')
    parser.add_argument('--train_model', action='store_true', help='Train and save churn model from labeled data')
    parser.add_argument('--train_csv', type=str, default='data/customer_churn_dataset-training-master.csv', help='Path to labeled training CSV')
    args = parser.parse_args()

    # Require --csv only if not training
    if not args.train_model and not args.csv:
        parser.error('--csv is required unless --train_model is specified')

    # Load Gemini API key from .env if not provided
    load_dotenv()
    api_key = args.gemini_api_key or os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("Gemini API key not provided. Set --gemini_api_key or add GEMINI_API_KEY to .env.")
        return

    # -------------------------------
    # TRAIN MODEL MODE
    # -------------------------------
    if args.train_model:
        print(f"Training churn model from {args.train_csv} ...")
        train_df = pd.read_csv(args.train_csv)
        train_df = extract_churn_features(train_df)

        features = ['logins', 'support_tickets', 'payment_delay', 'login_frequency', 'support_ticket_spike']

        target = None
        for col in ['churn', 'Churn']:
            if col in train_df.columns:
                target = col
                break

        if not target:
            print('No churn label provided in the training data; cannot train model.')
            return

        # Drop rows with missing target values
        train_df = train_df[train_df[target].notna()]
        X = train_df[features].fillna(0)
        y = train_df[target]

        model = lgb.LGBMClassifier(random_state=42)
        model.fit(X, y)

        os.makedirs('models', exist_ok=True)
        with open('models/churn_model.pkl', 'wb') as f:
            pickle.dump(model, f)

        print('✅ Model trained and saved to models/churn_model.pkl')
        return

    # -------------------------------
    # PREDICTION MODE
    # -------------------------------
    print("Loading data...")
    df = pd.read_csv(args.csv)
    print(f"Loaded {len(df)} records.")

    print("Extracting features...")
    df = extract_churn_features(df)

    print("Loading churn model...")
    model = load_churn_model()
    if model is None:
        print("No pretrained model found. Use --train_model to train one.")
        return

    print("Predicting churn risk...")
    df = predict_churn(df, model)

    print("Generating customer embeddings...")
    embedder = SentenceTransformer("all-MiniLM-L6-v2")
    df['summary'] = df.apply(build_customer_summary, axis=1)
    df['embedding'] = df['summary'].apply(lambda x: get_customer_embedding(x, embedder))

    # -------------------------------
    # Store embeddings in ChromaDB
    # -------------------------------
    print("Indexing customer embeddings in ChromaDB...")
    chroma_client = ChromaClient()
    collection = chroma_client.create_collection("customer_churn")
    # Store: id, embedding, metadata (summary, customer_id, churn_probability, etc)
    for idx, row in df.iterrows():
        collection.add(
            ids=[str(row['customer_id'])],
            embeddings=[row['embedding'].tolist() if isinstance(row['embedding'], np.ndarray) else row['embedding']],
            metadatas=[{
                'summary': row['summary'],
                'customer_id': row['customer_id'],
                'churn_probability': float(row['churn_probability']),
                'logins': row['logins'],
                'support_tickets': row['support_tickets'],
                'payment_delay': row.get('payment_delay', 0)
            }]
        )
    print("ChromaDB indexing complete.")

    print("\n--- Top Churn Risk Customers ---")
    top = df.sort_values('churn_probability', ascending=False).head(args.topk)
    for i, row in enumerate(top.itertuples(), 1):
        print(f"[{i}] Customer: {row.customer_id} | Churn: {row.churn_probability:.2f} | "
              f"Logins: {row.logins} | SupportTickets: {row.support_tickets} | "
              f"PaymentDelay: {getattr(row, 'payment_delay', 'N/A')}")
        print(f"    Summary: {row.summary}")

    # -------------------------------
    # RAG + GEMINI SUMMARIZATION
    # -------------------------------
    print("\n--- Gemini Summaries for Top Customers ---")
    for i, row in enumerate(top.itertuples(), 1):
        prompt = (
            f"Customer {row.customer_id} summary: {row.summary}\n"
            f"Churn probability: {row.churn_probability:.2f}\n"
            f"Explain the likely drivers of churn for this customer in bullet points."
            
        )
        gemini_summary = call_gemini_for_explanation(prompt, api_key)
        print(f"[{i}] Gemini Summary:\n{gemini_summary}\n")

    # -------------------------------
    # CLI Chat Mode for Interactive RAG
    # -------------------------------
    print("\n--- Interactive Chat Mode (type 'exit' to quit) ---")
    while True:
        user_query = input("\nAsk a question about churn risk, or type a customer ID for details: ")
        if user_query.strip().lower() == 'exit':
            break
        # Embed the query
        query_embedding = get_customer_embedding(user_query, embedder)
        # Retrieve top 3 similar customers
        results = collection.query(
            query_embeddings=[query_embedding.tolist() if isinstance(query_embedding, np.ndarray) else query_embedding],
            n_results=3
        )
        # Prepare context for Gemini
        context = "\n".join([
            f"Customer {meta['customer_id']} | Churn: {meta['churn_probability']:.2f} | Logins: {meta['logins']} | SupportTickets: {meta['support_tickets']} | PaymentDelay: {meta['payment_delay']}\nSummary: {meta['summary']}"
            for meta in results['metadatas'][0]
        ])
        prompt = (
            f"User question: {user_query}\n"
            f"Context from top similar customers:\n{context}\n"
            f"Answer the user's question using the context above."
        )
        gemini_answer = call_gemini_for_explanation(prompt, api_key)
        print(f"Gemini: {gemini_answer}\n")
    print("✅ Done.")


if __name__ == "__main__":
    main()