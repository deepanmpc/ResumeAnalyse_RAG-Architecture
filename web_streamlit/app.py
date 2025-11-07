import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
import numpy as np
from chromadb import Client as ChromaClient
from sentence_transformers import SentenceTransformer
import requests
from SLM_manager.churn_predictor import load_churn_model, predict_churn
from KNOWLEDGE_EXTRACTOR.churn_feature_extractor import extract_churn_features

load_dotenv()


# Cache the embedding model
@st.cache_resource
def load_embedder():
    return SentenceTransformer("all-MiniLM-L6-v2")

# Cache the churn model
@st.cache_resource
def get_model():
    return load_churn_model()

# Gemini API call function from main.py
def call_gemini_for_explanation(prompt: str, api_key: str) -> str:
    """Send prompt to Gemini API for churn driver summarization."""
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent"
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key
    }
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 512}
    }
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        result = response.json()
        # Check if 'candidates' exists and has content
        if result.get("candidates") and result["candidates"][0].get("content", {}).get("parts"):
            return result["candidates"][0]["content"]["parts"][0]["text"]
        else:
            # Handle cases where the response is valid but doesn't contain the expected text
            return "No content generated or response format is different."
    except Exception as e:
        return f"Gemini API error: {e}" 
# Function to get embedding
def get_customer_embedding(text: str, embedder):
    return embedder.encode(text)

st.set_page_config(layout="wide")

st.title("SaaS Churn Predictor & RAG Explainer")

# Get Gemini API Key
gemini_api_key = st.sidebar.text_input("Gemini API Key", type="password")

st.sidebar.header("Customer Data")

# File uploader
uploaded_file = st.sidebar.file_uploader("Upload your customer data (CSV)", type=["csv"])

# Load data
if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        st.sidebar.success("Data loaded successfully!")
    except Exception as e:
        st.sidebar.error(f"Error loading data: {e}")
else:
    st.info("Awaiting for a CSV file to be uploaded.")
    st.stop()


st.subheader("Customer Data Preview")
st.dataframe(df.head())

st.subheader("Churn Prediction")
if st.button("Predict Churn"):
    if df is not None:
        try:
            # Feature Engineering
            df_featured = extract_churn_features(df.copy())

            # Load Model
            model = get_model()

            if model:
                # Prediction
                df_predictions = predict_churn(df_featured, model)

                st.success("Churn prediction complete.")

                # Display Results
                st.subheader("Churn Prediction Results")

                # Chart of Churn Probabilities
                st.write("Distribution of Churn Probabilities")
                st.bar_chart(df_predictions['churn_probability'])

                # Top 5 High-Risk Customers
                st.subheader("Top 5 High-Risk Customers")
                high_risk_customers = df_predictions.sort_values(by='churn_probability', ascending=False).head(5)
                st.dataframe(high_risk_customers[['customer_id', 'churn_probability']])

                # Update ChromaDB for RAG
                with st.spinner("Updating AI assistant knowledge..."):
                    try:
                        chroma_client = ChromaClient()
                        collection = chroma_client.get_or_create_collection("customer_churn")
                        embedder = load_embedder()

                        # Prepare data for ChromaDB
                        documents = []
                        metadatas = []
                        ids = []

                        for i, row in df_predictions.iterrows():
                            summary = f"Customer {row['customer_id']} has a churn probability of {row['churn_probability']:.2f}. They logged in {row['logins']} times, created {row['support_tickets']} support tickets, and had a payment delay of {row['payment_delay']} days."
                            documents.append(summary)
                            metadatas.append({
                                "customer_id": str(row['customer_id']),
                                "churn_probability": float(row['churn_probability']),
                                "logins": int(row['logins']),
                                "support_tickets": int(row['support_tickets']),
                                "payment_delay": int(row['payment_delay']),
                                "summary": summary
                            })
                            ids.append(str(row['customer_id']))
                        
                        # Upsert data into ChromaDB
                        collection.upsert(
                            ids=ids,
                            documents=documents,
                            metadatas=metadatas
                        )
                        st.success("AI assistant knowledge updated.")
                    except Exception as e:
                        st.error(f"Error updating ChromaDB: {e}")

            else:
                st.error("Churn model not found. Please make sure 'models/churn_model.pkl' exists.")

        except Exception as e:
            st.error(f"An error occurred during prediction: {e}")
    else:
        st.warning("Please upload a CSV file first.")

st.subheader("AI Chatbot Area")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("Ask a question about customer churn"):
    if not gemini_api_key:
        st.warning("Please enter your Gemini API key in the sidebar.")
        st.stop()

    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        try:
            embedder = load_embedder()
            chroma_client = ChromaClient()
            collection = chroma_client.get_collection("customer_churn")

            # Embed the query
            query_embedding = get_customer_embedding(prompt, embedder)

            # Retrieve top 3 similar customers
            results = collection.query(
                query_embeddings=[query_embedding.tolist() if isinstance(query_embedding, np.ndarray) else query_embedding],
                n_results=3
            )

            if not results['metadatas'] or not results['metadatas'][0]:
                st.warning("Could not find relevant customer data to answer your question.")
                explanation = "I do not have enough information to answer that question."
            else:
                # Prepare context for Gemini
                context = "\n".join([
                    f"Customer {meta['customer_id']} | Churn: {meta['churn_probability']:.2f} | Logins: {meta['logins']} | SupportTickets: {meta['support_tickets']} | PaymentDelay: {meta['payment_delay']}\nSummary: {meta['summary']}"
                    for meta in results['metadatas'][0]
                ])

                rag_prompt = (
                    f"User question: {prompt}\n"
                    f"Context from top similar customers:\n{context}\n"
                    f"Answer the user's question using the context above."
                )

                st.info(f"**Context sent to Gemini:**\n```\n{rag_prompt}```")

                explanation = call_gemini_for_explanation(rag_prompt, gemini_api_key)
            
            st.markdown(explanation)

        except Exception as e:
            st.error(f"An error occurred: {e}")
            explanation = "Sorry, I encountered an error. Please check the logs."
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": explanation})