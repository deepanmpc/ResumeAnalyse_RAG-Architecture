from sentence_transformers import SentenceTransformer
import numpy as np

def get_customer_embedding(text: str, model: SentenceTransformer) -> np.ndarray:
    return model.encode(text, convert_to_numpy=True)

def build_customer_summary(row) -> str:
    return (
        f"Customer {row['customer_id']} | Churn: {row.get('churn_probability', 0):.3f} | "
        f"Logins: {row.get('logins', 0)}, SupportTickets: {row.get('support_tickets', 0)}, "
        f"PaymentDelay: {row.get('payment_delay', 0)}"
    )
