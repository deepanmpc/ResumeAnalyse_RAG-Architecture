"""
ChromaDB Manager for Resume Analysis System
Handles vector storage, querying, and similarity search operations.
"""

import os
from pathlib import Path
from typing import Dict, Any, List
from sentence_transformers import SentenceTransformer
from langchain_community.document_loaders import PyPDFLoader
import chromadb
from TEXT_EMBEDDING_MODEL.textEmbedding_model import process_extracted_data

class ChromaDBManager:
    def __init__(self, db_path: str = "resume_chroma_db"):
        """Initialize ChromaDB with section-level storage for resumes."""
        if not os.path.exists(db_path):
            os.makedirs(db_path)
        self.client = chromadb.PersistentClient(path=db_path)
        self.sections_collection = self.client.get_or_create_collection(
            name="resume_sections",
            embedding_function=None
        )
        print(f"ChromaDB initialized at {db_path}")

    def add_record(self, db_record: Dict[str, Any]):
        # Delete existing
        try:
            self.sections_collection.delete(where={"resume_id": db_record["id"]})
        except:
            pass

        sections = db_record["metadata"]["sections"]
        section_embeddings = db_record["metadata"]["section_embeddings"]

        ids = []
        docs = []
        embs = []
        metas = []

        for name, text in sections.items():
            if not text.strip():
                continue
            ids.append(f"{db_record['id']}_{name}")
            docs.append(text)
            embs.append(section_embeddings[name])
            metas.append({
                "resume_id": db_record["id"],
                "section_name": name,
                "filename": db_record["metadata"]["filename"]
            })

        if ids:
            self.sections_collection.add(
                ids=ids,
                documents=docs,
                embeddings=embs,
                metadatas=metas
            )
            print(f"Added resume {db_record['id']} with {len(ids)} sections")

    def query(self, query_text: str, query_embedding: List[float], top_k: int = 5, min_similarity: float = 0.3):
        # Use ChromaDB's built-in query functionality
        results = self.sections_collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=['documents', 'metadatas', 'distances']
        )

        if (not results or not results.get('documents') or not results.get('metadatas') or not results.get('distances')):
            return {"matches": [], "resume_scores": {}}
        if not results['documents'][0] or not results['metadatas'][0] or not results['distances'][0]:
            return {"matches": [], "resume_scores": {}}

        matches = []
        resume_scores = {}

        # Process results
        for idx, (doc, meta, distance) in enumerate(zip(results['documents'][0], results['metadatas'][0], results['distances'][0])):
            if doc is None or meta is None or distance is None:
                continue
            match_percentage = round((1 - distance) * 100, 2)  # Convert distance to similarity percentage
            if match_percentage >= (min_similarity * 100):
                reconstructed_id = f"{meta['resume_id']}_{meta['section_name']}"
                match = {
                    "resume_id": meta["resume_id"],
                    "section_name": meta["section_name"],
                    "match_percentage": match_percentage,
                    "text": doc,
                    "id": reconstructed_id
                }
                matches.append(match)
                rid = meta["resume_id"]
                if rid not in resume_scores:
                    resume_scores[rid] = []
                resume_scores[rid].append(match_percentage)

        # Average score per resume
        resume_scores = {rid: round(sum(scores)/len(scores),2) for rid, scores in resume_scores.items()}

        return {
            "matches": matches,
            "resume_scores": resume_scores,
            "query": query_text
        }

def load_job_description_pdf(file_path: str) -> str:
    loader = PyPDFLoader(file_path)
    pages = loader.load()
    return "\n".join(page.page_content for page in pages)

# Example usage
if __name__ == "__main__":
    embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    chroma_manager = ChromaDBManager()

    # Process resumes from embeddings (assume you already created db_record in textEmbedding_model)
    from TEXT_EMBEDDING_MODEL.textEmbedding_model import process_extracted_data
    resume_folder = "/Users/deepandee/Desktop/RAG/DATA_resume"
    for file in os.listdir(resume_folder):
        if file.endswith(".pdf"):
            file_path = os.path.join(resume_folder, file)
            try:
                import pdfplumber
                content = ""
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        text = page.extract_text()
                        if text:
                            content += text + "\n"
                print(f"\nResume Content for {file}:\n{'-'*50}\n{content[:500]}...\n{'-'*50}")
                if not content.strip():
                    print(f"Warning: No text content extracted from {file}")
                    # Fallback to PyPDF2
                    import PyPDF2
                    with open(file_path, 'rb') as pdf_file:
                        pdf_reader = PyPDF2.PdfReader(pdf_file)
                        for page in pdf_reader.pages:
                            content += page.extract_text() + "\n"
            except Exception as e:
                print(f"Error reading {file}: {str(e)}")
                content = ""
            
            extracted = process_extracted_data({
                "success": True,
                "filename": file,
                "file_path": file_path,
                "sections": {"content": content}
            }, embedding_model)
            if extracted:
                chroma_manager.add_record(extracted)

    # Query job descriptions
    job_desc_folder = "/Users/deepandee/Desktop/RAG/JOB_DESCRIPTIONS"
    for job_file in os.listdir(job_desc_folder):
        if job_file.endswith(".pdf"):
            job_path = os.path.join(job_desc_folder, job_file)
            job_text = load_job_description_pdf(job_path)
            print(f"\nJob Description Content:\n{'-'*50}\n{job_text}\n{'-'*50}\n")
            
            job_emb = embedding_model.encode(job_text).tolist()
            matches = chroma_manager.query(job_text, job_emb, top_k=5, min_similarity=0.1)  # Lower threshold to 10%
            print(f"\nMatches for job: {job_file}")
            print("\nResume Matches:")
            if matches["matches"]:
                for match in matches["matches"]:
                    print(f"\nResume: {match['resume_id']}")
                    print(f"Section: {match['section_name']}")
                    print(f"Match Score: {match['match_percentage']}%")
                    print("Content Preview:", match['text'][:200] + "..." if len(match['text']) > 200 else match['text'])
                print("\nOverall Resume Scores:")
                for rid, score in matches["resume_scores"].items():
                    print(f"{rid}: {score}%")
            else:
                print("No matches found")