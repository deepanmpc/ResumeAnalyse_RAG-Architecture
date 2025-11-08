import pandas as pd
from sentence_transformers import SentenceTransformer
from CHROMA_DB.collections import ChromaDBManager

def extract_churn_features(df: pd.DataFrame) -> pd.DataFrame:
    # Normalize columns
    df = df.rename(columns={
        'CustomerID': 'customer_id',
        'Usage Frequency': 'logins',
        'Support Calls': 'support_tickets',
        'Payment Delay': 'payment_delay',
        'Churn': 'churn',
    })
    if 'customer_id' not in df.columns:
        df['customer_id'] = df.index.astype(str)
    if 'logins' not in df.columns:
        df['logins'] = 0
    if 'support_tickets' not in df.columns:
        df['support_tickets'] = 0
    if 'payment_delay' not in df.columns:
        df['payment_delay'] = 0
    if 'churn' not in df.columns:
        df['churn'] = 0

    # Add engineered features
    df['login_frequency'] = df['logins'].rolling(window=7, min_periods=1).mean()
    df['support_ticket_spike'] = (df['support_tickets'] > df['support_tickets'].shift(1)).astype(int)

    return df

def store_features_in_chromadb(df: pd.DataFrame):
    # Initialize ChromaDBManager and embedding model
    chroma_manager = ChromaDBManager()
    embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    for _, row in df.iterrows():
        # Build customer summary
        summary = (
            f"Customer {row['customer_id']} | Churn: {row.get('churn', 0):.3f} | "
            f"Logins: {row.get('logins', 0)}, SupportTickets: {row.get('support_tickets', 0)}, "
            f"PaymentDelay: {row.get('payment_delay', 0)}"
        )

        # Generate embedding
        embedding = embedding_model.encode(summary).tolist()

        # Prepare record for ChromaDB
        record = {
            "id": row['customer_id'],
            "metadata": {
                "summary": summary,
                "logins": row.get('logins', 0),
                "support_tickets": row.get('support_tickets', 0),
                "payment_delay": row.get('payment_delay', 0),
                "churn_probability": row.get('churn', 0)
            },
            "embedding": embedding
        }

        # Add record to ChromaDB
        chroma_manager.add_record(record)

# Example usage
if __name__ == "__main__":
    # Example DataFrame
    data = {
        'CustomerID': ['C001', 'C002', 'C003'],
        'Usage Frequency': [10, 15, 5],
        'Support Calls': [1, 3, 0],
        'Payment Delay': [0, 5, 2],
        'Churn': [0.1, 0.5, 0.2]
    }
    df = pd.DataFrame(data)

    # Extract features
    processed_df = extract_churn_features(df)

    # Store in ChromaDB
    store_features_in_chromadb(processed_df)
