# collections.py
import os
from typing import Dict, Any, List
from sentence_transformers import SentenceTransformer
from langchain_community.document_loaders import PyPDFLoader
import chromadb

class ChromaDBManager:
    def __init__(self, db_path: str = "resume_chroma_db", collection_name: str = "resumes", sections_collection_name: str = "resume_sections", in_memory: bool = False):
        if in_memory:
            self.client = chromadb.Client()
        else:
            if not os.path.exists(db_path):
                os.makedirs(db_path)
            self.client = chromadb.PersistentClient(path=db_path)

        # Full-resume collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=None
        )

        # Section-level collection
        self.sections_collection = self.client.get_or_create_collection(
            name=sections_collection_name,
            embedding_function=None
        )

        if not in_memory:
            print(f"ChromaDB initialized at {db_path}")

    def add_record(self, db_record: Dict[str, Any]):
        """Add both full resume and its sections into ChromaDB"""
        resume_id = db_record["id"]
        filename = db_record["metadata"]["filename"]

        # --- Store FULL RESUME embedding ---
        try:
            self.collection.delete(where={"filename": filename})
        except Exception:
            pass

        self.collection.add(
            ids=[resume_id],
            documents=[db_record["metadata"]["full_text"]],
            embeddings=[db_record["embedding"]],
            metadatas=[{"resume_id": resume_id, "filename": filename}]
        )

        # --- Store SECTION embeddings ---
        try:
            self.sections_collection.delete(where={"filename": filename})
        except Exception:
            pass

        sections = db_record["metadata"]["sections"]
        section_embeddings = db_record["metadata"]["section_embeddings"]

        ids, docs, embs, metas = [], [], [], []

        for name, text in sections.items():
            if not text.strip():
                continue
            ids.append(f"{resume_id}_{name}")
            docs.append(text)
            embs.append(section_embeddings[name])
            metas.append({
                "resume_id": resume_id,
                "section_name": name,
                "filename": filename
            })

        if ids:
            self.sections_collection.add(
                ids=ids,
                documents=docs,
                embeddings=embs,
                metadatas=metas
            )

        print(f"✅ Added resume {resume_id} with {len(ids)} sections")

    def query(self, query_text: str, query_embedding: List[float], top_k: int = 5, min_similarity: float = 0.3):
        """Query against section-level embeddings"""
        results = self.sections_collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=['documents', 'metadatas', 'distances']
        )

        if not results or not results.get("documents") or not results.get("distances"):
            return {"matches": [], "resume_scores": {}}

        matches, resume_scores = [], {}

        for doc, meta, dist in zip(results["documents"][0], results["metadatas"][0], results["distances"][0]):
            if doc is None or meta is None or dist is None:
                continue
            match_percentage = round((1 - dist) * 100, 2)
            if match_percentage >= (min_similarity * 100):
                match = {
                    "resume_id": meta["resume_id"],
                    "filename": meta["filename"],
                    "section_name": meta["section_name"],
                    "match_percentage": match_percentage,
                    "text": doc,
                }
                matches.append(match)

                rid = meta["resume_id"]
                resume_scores.setdefault(rid, []).append(match_percentage)

        # Average per resume
        resume_scores = {rid: round(sum(scores)/len(scores), 2) for rid, scores in resume_scores.items()}

        return {
            "matches": matches,
            "resume_scores": resume_scores,
            "query": query_text
        }

    def get_resume_embedding(self, resume_id: str) -> List[float]:
        """Retrieve the full resume text embedding given a resume ID."""
        results = self.collection.get(
            ids=[resume_id],
            include=['embeddings']
        )

        if not results or not results.get("embeddings") or not results["embeddings"][0]:
            return None

        return results["embeddings"][0]


def load_job_description_pdf(file_path: str) -> str:
    """Extracts text from a job description PDF"""
    loader = PyPDFLoader(file_path)
    pages = loader.load()
    return "\n".join(page.page_content for page in pages)


# Example standalone usage
if __name__ == "__main__":
    embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    chroma_manager = ChromaDBManager()

    resume_folder = "/Users/deepandee/Desktop/RAG/DATA_resume"
    from TEXT_EMBEDDING_MODEL.textEmbedding_model import process_extracted_data

    for file in os.listdir(resume_folder):
        if file.endswith(".pdf"):
            file_path = os.path.join(resume_folder, file)

            # Extract text safely
            import pdfplumber
            content = ""
            try:
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        text = page.extract_text()
                        if text:
                            content += text + "\n"
            except Exception as e:
                print(f"⚠️ Error reading {file}: {e}")
                continue

            extracted = process_extracted_data({
                "success": True,
                "filename": file,
                "file_path": file_path,
                "sections": {"content": content}
            }, embedding_model)

            if extracted:
                chroma_manager.add_record(extracted)

    # Query job description
    job_desc_folder = "/Users/deepandee/Desktop/RAG/JOB_DESCRIPTIONS"
    for job_file in os.listdir(job_desc_folder):
        if job_file.endswith(".pdf"):
            job_path = os.path.join(job_desc_folder, job_file)
            job_text = load_job_description_pdf(job_path)
            job_emb = embedding_model.encode(job_text).tolist()

            matches = chroma_manager.query(job_text, job_emb, top_k=5, min_similarity=0.1)

            print(f"\nMatches for job: {job_file}")
            for match in matches["matches"]:
                print(f"- {match['resume_id']} ({match['match_percentage']}%) → {match['text'][:100]}...")
