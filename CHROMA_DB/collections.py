# collections.py
import os
from typing import Dict, Any, List
from sentence_transformers import SentenceTransformer
import chromadb

class ChromaDBManager:
    def __init__(self, db_path: str = "chroma_db", collection_name: str = "customers", in_memory: bool = False):
        if in_memory:
            self.client = chromadb.Client()
        else:
            if not os.path.exists(db_path):
                os.makedirs(db_path)
            self.client = chromadb.PersistentClient(path=db_path)

        # Customer collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=None,
            metadata={"hnsw:space": "cosine"}
        )

        if not in_memory:
            print(f"ChromaDB initialized at {db_path}")

    def add_record(self, db_record: Dict[str, Any]):
        """Add customer data into ChromaDB"""
        customer_id = db_record["id"]
        metadata = db_record["metadata"]

        # --- Store Customer embedding ---
        try:
            self.collection.delete(where={"customer_id": customer_id})
        except Exception:
            pass

        self.collection.add(
            ids=[customer_id],
            documents=[metadata["summary"]],
            embeddings=[db_record["embedding"]],
            metadatas=[{
                "customer_id": customer_id,
                "logins": metadata.get("logins", 0),
                "support_tickets": metadata.get("support_tickets", 0),
                "payment_delay": metadata.get("payment_delay", 0),
                "churn_probability": metadata.get("churn_probability", 0.0)
            }]
        )

        print(f"✅ Added customer {customer_id}")

    def query(self, query_text: str, query_embedding: List[float], top_k: int = 5, min_similarity: float = 0.3):
        """Query against customer embeddings"""
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=['documents', 'metadatas', 'distances']
        )

        if not results or not results.get("documents") or not results.get("distances"):
            return {"matches": [], "customer_scores": {}}

        matches, customer_scores = [], {}

        for doc, meta, dist in zip(results["documents"][0], results["metadatas"][0], results["distances"][0]):
            if doc is None or meta is None or dist is None:
                continue
            match_percentage = round((1 - dist) * 100, 2)
            if match_percentage >= (min_similarity * 100):
                match = {
                    "customer_id": meta["customer_id"],
                    "logins": meta["logins"],
                    "support_tickets": meta["support_tickets"],
                    "payment_delay": meta["payment_delay"],
                    "churn_probability": meta["churn_probability"],
                    "match_percentage": match_percentage,
                    "summary": doc,
                }
                matches.append(match)

                cid = meta["customer_id"]
                customer_scores.setdefault(cid, []).append(match_percentage)

        # Average per customer
        customer_scores = {cid: round(sum(scores)/len(scores), 2) for cid, scores in customer_scores.items()}

        return {
            "matches": matches,
            "customer_scores": customer_scores,
            "query": query_text
        }

# Example standalone usage
if __name__ == "__main__":
    embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    chroma_manager = ChromaDBManager()

    # Example customer data
    customer_data = {
        "id": "customer_123",
        "metadata": {
            "summary": "Customer 123 | Churn: 0.123 | Logins: 10, SupportTickets: 2, PaymentDelay: 5",
            "logins": 10,
            "support_tickets": 2,
            "payment_delay": 5,
            "churn_probability": 0.123
        },
        "embedding": embedding_model.encode("Customer 123 | Churn: 0.123 | Logins: 10, SupportTickets: 2, PaymentDelay: 5").tolist()
    }

    chroma_manager.add_record(customer_data)

    # Query example
    query_text = "Customer with high churn probability"
    query_embedding = embedding_model.encode(query_text).tolist()

    matches = chroma_manager.query(query_text, query_embedding, top_k=5, min_similarity=0.1)

    print("\nQuery Results:")
    for match in matches["matches"]:
        print(f"- {match['customer_id']} ({match['match_percentage']}%) → {match['summary']}")
