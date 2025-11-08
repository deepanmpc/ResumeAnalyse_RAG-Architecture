import streamlit as st
import pandas as pd
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import numpy as np
from chromadb import Client as ChromaClient
from sentence_transformers import SentenceTransformer
import requests
import html
import re
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
    st.warning("Could not import custom modules. Running without internal model/extractor functionality.")
    def load_churn_model(): return None
    def predict_churn(df, model): 
        # Mock prediction for demonstration
        return df.assign(
            churn_probability=np.random.rand(len(df)),
            logins=np.random.randint(10, 500, len(df)),
            support_tickets=np.random.randint(0, 10, len(df)),
            payment_delay=np.random.randint(0, 30, len(df))
        )
    def extract_churn_features(df): 
        # Mock feature extraction
        return df.assign(logins=100, support_tickets=5, payment_delay=0)


load_dotenv()

# --- Initial Setup and Caching ---

# Cache the embedding model
@st.cache_resource
def load_embedder():
    return SentenceTransformer("all-MiniLM-L6-v2")

# Cache the churn model
@st.cache_resource
def get_model():
    return load_churn_model()

# Initialize session state for page navigation and chat
if 'page' not in st.session_state:
    st.session_state['page'] = 'main' # 'main', 'results', or 'chatbot'
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'df_predictions' not in st.session_state:
    st.session_state['df_predictions'] = None
if 'uploaded_file' not in st.session_state:
    st.session_state['uploaded_file'] = None
if 'df' not in st.session_state:
    st.session_state['df'] = None


# --- Gemini API Call Function ---

def call_gemini_for_explanation(prompt: str, context: str, history: list[dict] | None = None) -> str:
    """Send prompt + retrieved context + chat history to Gemini for churn explanation."""
    # Use empty string as placeholder for API key
    api_key = os.getenv("GEMINI_API_KEY", "")

    # Define the primary model for RAG tasks
    model_name = "gemini-2.5-flash-preview-09-2025"
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"

    headers = {
        "Content-Type": "application/json",
    }

    # 1. Construct the RAG prompt for the final message
    rag_prompt_text = (
        f"User question: {prompt}\n\n"
        f"Context from top similar customers:\n{context}\n\n"
        f"Analyze the context and history. Based on the customer data provided in the context, explain why the user's inquiry is relevant to churn prediction and suggest proactive steps. Use a conversational and supportive tone."
    )

    # 2. Build conversation history in Gemini format
    contents: list[dict] = []
    
    # Append historical messages
    for message in history or []:
        role = message.get("role", "user")
        # Map Streamlit role 'assistant' to Gemini role 'model'
        gemini_role = "model" if role == "assistant" else "user"
        contents.append({"role": gemini_role, "parts": [{"text": message.get("content", "")}]})

    # Append the current RAG prompt as the last user turn
    contents.append({"role": "user", "parts": [{"text": rag_prompt_text}]})

    request_body = {
        "contents": contents,
        # --- FIX: Renamed 'config' to 'generationConfig' as required by the API ---
        "generationConfig": { 
            "temperature": 0.75
        }
        # --------------------------------------------------------------------------
    }

    last_error = None
    
    # Exponential backoff mechanism (simplified retry loop)
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
            if response.status_code == 429: # Too many requests, retry
                time.sleep(2 ** attempt)
            else:
                break
        except Exception as e:
            last_error = str(e)
            break

    return f"Gemini API error: {last_error or 'No suitable endpoint responded successfully.'}"

# --- Custom Styling for Chatbot Page ---

CHATBOT_CSS = """
<style>
/* 1. Main container for the chat interface */
.chatbot-container {
    max-width: 800px;
    margin: 1rem auto;
    border-radius: 12px;
    background: #e5ddd5; /* WhatsApp-like background */
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    display: flex;
    flex-direction: column;
    height: 80vh; 
    overflow: hidden;
}

/* 2. Header styling */
.chatbot-header {
    background: #075e54; /* WhatsApp/Telegram-like header color */
    color: white;
    padding: 15px 20px;
    border-radius: 12px 12px 0 0;
    font-size: 1.25rem;
    font-weight: 600;
    margin-bottom: -15px; /* Pull header down over the chat area */
}


/* 3. Streamlit Chat Component Overrides */

/* Target the container holding the messages and apply themed background */
div[data-testid="stVerticalBlock"] > div:first-child > div:nth-child(2) {
    background-color: #e5ddd5 !important;
    padding-top: 20px; /* Add padding below the custom header */
}

/* User Message Bubble */
.stChatMessage:has([data-testid="stMarkdownContainer"] h6:contains("user")) {
    background-color: #dcf8c6 !important; /* Light green for user */
    margin-left: auto !important;
    margin-right: 0 !important;
    border-bottom-right-radius: 0 !important;
    border-top-right-radius: 12px !important;
    border-top-left-radius: 12px !important;
    border-bottom-left-radius: 12px !important;
}

/* Assistant Message Bubble */
.stChatMessage:has([data-testid="stMarkdownContainer"] h6:contains("assistant")) {
    background-color: #ffffff !important; /* White for assistant */
    margin-right: auto !important;
    margin-left: 0 !important;
    border-bottom-left-radius: 0 !important;
    border-top-right-radius: 12px !important;
    border-top-left-radius: 12px !important;
    border-bottom-right-radius: 12px !important;
}

/* Fix for chat input placement */
.stChatInput {
    margin-top: 10px;
    padding-top: 10px;
    padding-bottom: 0px;
    border-top: 1px solid #ccc;
    background-color: #f7f7f7;
    margin-bottom: -20px;
    padding: 15px;
    border-radius: 0 0 12px 12px;
}
</style>
"""

# --- Chatbot Rendering Function ---

def render_chatbot_page():
    """Renders the dedicated, themed chatbot interface."""
    st.markdown(CHATBOT_CSS, unsafe_allow_html=True)
    
    # Use a container to hold the chat interface with specific dimensions and styling
    # This replaces the blank container that was causing issues.
    with st.container():
        st.markdown('<div class="chatbot-header">🤖 AI Customer Success Analyst</div>', unsafe_allow_html=True)

        # The core chat window (using Streamlit's native chat messages)
        # Set height on this inner container for scroll control
        chat_history_placeholder = st.container(height=500, border=False) 

        with chat_history_placeholder:
            for msg in st.session_state.get("messages", []):
                # Using the native chat component handles layout and avatars better
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
        
        # 2. Chat Input and Logic
        chat_input = st.chat_input("How can I help you analyze churn risk?")

        if chat_input:
            # Add user message to state and display it immediately
            st.session_state.messages.append({"role": "user", "content": chat_input})
            
            # RAG and LLM call logic
            explanation = ""
            context = ""
            
            try:
                # RAG Retrieval
                with st.spinner("Retrieving customer context..."):
                    # Mock initialization for deployment without actual local services
                    chroma_client = ChromaClient()
                    collection = chroma_client.get_collection("customer_churn")
                    embedder = load_embedder()

                    # Use the user's latest message as the query for context retrieval
                    query_embedding = embedder.encode(chat_input).tolist()
                    
                    # Retrieve top 5 most similar customer summaries
                    results = collection.query(
                        query_embeddings=[query_embedding],
                        n_results=5,
                        include=['documents']
                    )

                    context_lines = []
                    if results and results.get('documents'):
                        for doc in results['documents'][0]:
                            context_lines.append(doc)
                    
                    if context_lines:
                        context = "\n---\n".join(context_lines)
                    else:
                        context = "No highly relevant customer data found in the knowledge base. Proceeding without specific context."
                
                # Call Gemini
                with st.spinner("Generating explanation with Gemini..."):
                    conversation_history = [
                        {"role": msg["role"], "content": msg["content"]}
                        for msg in st.session_state.messages
                        if msg["role"] in ("user", "assistant")
                    ]
                    
                    explanation = call_gemini_for_explanation(
                        prompt=chat_input,
                        context=context,
                        history=conversation_history,
                    )

                    if not explanation.strip():
                        explanation = "I wasn't able to generate a helpful answer this time. (API returned empty response)."
                
            except Exception as e:
                explanation = f"Sorry, an internal error occurred during RAG or LLM call: {e}"
                st.error(explanation)

            # 3. Add assistant response to state and display it
            st.session_state.messages.append({"role": "assistant", "content": explanation})
            # Rerun to update the chat history with the new messages
            st.rerun() 
            


# --- Streamlit Application Layout (Page Management) ---

st.set_page_config(layout="wide")
st.title("SaaS Churn Predictor & RAG Explainer")

# Add a simple back button if not on the main page
if st.session_state.page != 'main':
    # Use a distinct key to prevent widget collision on re-run
    if st.sidebar.button("⬅️ Back to Upload / Home", key="back_button"): 
        st.session_state.page = 'main'
        st.session_state.messages = [] # Clear messages on navigation
        st.rerun() 

# ----------------------------------------------------
# MAIN PAGE: File Upload & Preview
# ----------------------------------------------------
if st.session_state.page == 'main':
    st.sidebar.header("Customer Data")
    uploaded_file = st.sidebar.file_uploader("Upload your customer data (CSV)", type=["csv"], key="uploader")

    # Handle file upload change
    if uploaded_file is not None and uploaded_file != st.session_state.uploaded_file:
        try:
            st.session_state.df = pd.read_csv(uploaded_file)
            st.session_state.uploaded_file = uploaded_file # Store the new file object
            st.session_state.page = 'main' # Stay on main page to view preview
            st.sidebar.success("Data loaded successfully! Click 'Predict Churn' to analyze.")
            st.rerun() 
        except Exception as e:
            st.sidebar.error(f"Error loading data: {e}")
            st.stop()
    elif st.session_state.df is not None:
        st.subheader("Customer Data Preview")
        st.dataframe(st.session_state.df.head())

        st.subheader("Churn Prediction")
        if st.button("Predict Churn"): 
            st.session_state.page = 'results'
            st.rerun() 
    else:
        st.info("Please upload a CSV file with customer data in the sidebar to begin.")


# ----------------------------------------------------
# RESULTS PAGE: Prediction Stats and Chatbot Entry
# ----------------------------------------------------
elif st.session_state.page == 'results':
    # This block executes prediction and database update only once per file upload/button press
    if st.session_state.df_predictions is None:
        with st.spinner("Running Churn Model and updating Knowledge Base..."):
            try:
                df = st.session_state.df.copy()
                df_featured = extract_churn_features(df)
                model = get_model()

                df_predictions = predict_churn(df_featured, model)
                st.session_state['df_predictions'] = df_predictions

                # --- ChromaDB Update for RAG ---
                chroma_client = ChromaClient()
                collection = chroma_client.get_or_create_collection("customer_churn")
                embedder = load_embedder()

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
                    st.toast("AI knowledge base updated!")

            except Exception as e:
                st.error(f"Error during churn prediction or ChromaDB update: {e}")
                # Fallback to main page if prediction failed
                st.session_state.page = 'main'
                st.rerun() 

    
    # Display Results (Only if successful)
    if st.session_state.df_predictions is not None:
        df_predictions = st.session_state.df_predictions
        st.success("Churn prediction complete.")

        st.subheader("Churn Prediction Results")

        st.write("Distribution of Churn Probabilities")
        st.bar_chart(df_predictions['churn_probability'])

        st.subheader("Top 5 High-Risk Customers")
        high_risk_customers = df_predictions.sort_values(by='churn_probability', ascending=False).head(5)
        st.dataframe(high_risk_customers[['customer_id', 'churn_probability']])
        
        st.markdown("---")
        
        # AI Mode Button - Now redirects to a dedicated page
        if st.button("Start AI Chatbot Conversation", type="primary"):
            st.session_state.page = 'chatbot'
            st.session_state.messages = [] # Clear chat history for a fresh start
            st.rerun() 


# ----------------------------------------------------
# CHATBOT PAGE: Dedicated UI
# ----------------------------------------------------
elif st.session_state.page == 'chatbot':
    render_chatbot_page()