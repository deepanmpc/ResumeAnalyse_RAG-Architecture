from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import numpy as np
from chromadb import Client as ChromaClient
from sentence_transformers import SentenceTransformer
import requests
import json
import time

# Ensure project root is on the Python path so local packages resolve
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Assuming these modules exist in the project structure
try:
    from SLM_manager.churn_predictor import load_churn_model, predict_churn
    from KNOWLEDGE_EXTRACTOR.churn_feature_extractor import extract_churn_features
except ImportError:
    print("Could not import custom modules. Running without internal model/extractor functionality.")
    def load_churn_model(): return None
    def predict_churn(df, model):
        return df.assign(
            churn_probability=np.random.rand(len(df)),
            logins=np.random.randint(10, 500, len(df)),
            support_tickets=np.random.randint(0, 10, len(df)),
            payment_delay=np.random.randint(0, 30, len(df))
        )
    def extract_churn_features(df):
        return df.assign(logins=100, support_tickets=5, payment_delay=0)

load_dotenv()

app = FastAPI()

# CORS middleware to allow requests from the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Adjust this to your React app's URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Initial Setup and Caching ---

# Cache the embedding model
# @st.cache_resource is Streamlit specific, so we'll use a global variable or a simple function call
_embedder = None
def get_embedder():
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedder

# Cache the churn model
_churn_model = None
def get_churn_model():
    global _churn_model
    if _churn_model is None:
        _churn_model = load_churn_model()
    return _churn_model

# --- Gemini API Call Function ---

def call_gemini_for_explanation(prompt: str, context: str, history: list[dict] | None = None) -> str:
    """Send prompt + retrieved context + chat history to Gemini for churn explanation."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "Gemini API key not found. Please set the GEMINI_API_KEY environment variable."

    model_name = "gemini-2.5-flash-preview-09-2025"
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"

    headers = {
        "Content-Type": "application/json",
    }

    rag_prompt_text = (
        f"User question: {prompt}\n\n"
        f"Context from top similar customers:\n{context}\n\n"
        f"Analyze the context and history. Based on the customer data provided in the context, explain why the user's inquiry is relevant to churn prediction and suggest proactive steps. Use a conversational and supportive tone."
    )

    contents: list[dict] = []
    for message in history or []:
        gemini_role = "model" if message.get("role") == "assistant" else "user"
        contents.append({"role": gemini_role, "parts": [{"text": message.get("content", "")}]})

    contents.append({"role": "user", "parts": [{"text": rag_prompt_text}]})

    request_body = {
        "contents": contents,
        "generationConfig": {
            "temperature": 0.75
        }
    }

    last_error = None
    for attempt in range(3):
        try:
            response = requests.post(api_url, headers=headers, json=request_body, timeout=30)
            response.raise_for_status()
            result = response.json()

            text = result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()

            if text:
                return text
            else:
                last_error = f"API returned no text content: {result.get('promptFeedback', {}).get('blockReason', 'Unknown')}"
                break

        except requests.exceptions.HTTPError as http_err:
            last_error = f"HTTP Error ({response.status_code}) at {api_url}: {http_err.response.text}"
            if response.status_code == 429:
                time.sleep(2 ** attempt)
            else:
                break
        except Exception as e:
            last_error = str(e)
            break

    return f"Gemini API error: {last_error or 'No suitable endpoint responded successfully.'}"

# --- API Endpoints ---

class ChatMessage(BaseModel):
    message: str
    history: list[dict] = []

@app.post("/chat")
async def chat_with_ai(chat_message: ChatMessage):
    try:
        chroma_client = ChromaClient()
        collection = chroma_client.get_or_create_collection("customer_churn")
        embedder = get_embedder()

        query_embedding = embedder.encode(chat_message.message).tolist()

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=5,
            include=['documents']
        )

        context_lines = []
        if results and results.get('documents'):
            for doc in results['documents'][0]:
                context_lines.append(doc)

        context = "\n---\n".join(context_lines) if context_lines else "No highly relevant customer data found in the knowledge base. Proceeding without specific context."

        explanation = call_gemini_for_explanation(
            prompt=chat_message.message,
            context=context,
            history=chat_message.history,
        )
        return {"response": explanation}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

@app.post("/predict_churn")
async def predict_churn_endpoint(file: UploadFile = File(...)):
    try:
        df = pd.read_csv(file.file)
        df_featured = extract_churn_features(df.copy())
        model = get_churn_model()

        df_predictions = predict_churn(df_featured, model)

        # Convert DataFrame to a list of dictionaries for JSON serialization
        predictions_list = df_predictions.to_dict(orient="records")
        return {"predictions": predictions_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during churn prediction: {e}")

@app.post("/update_knowledge_base")
async def update_knowledge_base_endpoint(predictions: list[dict]):
    try:
        df_predictions = pd.DataFrame(predictions)

        chroma_client = ChromaClient()
        collection = chroma_client.get_or_create_collection("customer_churn")
        embedder = get_embedder()

        documents = []
        metadatas = []
        ids = []

        for _, row in df_predictions.iterrows():
            summary = (
                f"Customer ID: {row['customer_id']}. Churn Probability: {row['churn_probability']:.2f}. "
                f"Key Activities: Logins={row.get('logins', 'N/A')}, "
                f"Support Tickets={row.get('support_tickets', 'N/A')}, "
                f"Payment Delay (days)={row.get('payment_delay', 'N/A')}."
            )
            documents.append(summary)
            metadatas.append({
                "customer_id": str(row['customer_id']),
                "churn_probability": float(row['churn_probability']),
            })
            ids.append(str(row['customer_id']))

        if ids:
            collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
        return {"message": "Knowledge base updated successfully!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating knowledge base: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
