import argparse
import json
from typing import List
from CHROMA_DB.collections import ChromaDBManager, load_job_description_pdf
from sentence_transformers import SentenceTransformer
from langchain_community.llms import Ollama

# Initialize
embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
chroma_manager = ChromaDBManager()
llm = Ollama(model="mistral:instruct", temperature=0.7)

def summarize_resume(resume_embedding: List[float], job_text: str):
    """Summarize the resume information using the LLM."""
    prompt = f"""
    You are an expert HR assistant. Your task is to analyze the following resume and provide a summary of the candidate's qualifications, key strengths and gaps, and overall ranking for the given job description.

    **Job Description:**
    {job_text}

    **Resume:**
    {resume_embedding}

    **Your Task:**
    Based on the job description and the provided resume, write a concise summary of the candidate's qualifications, key strengths and gaps, and overall ranking.
    """

    summary = llm.invoke(prompt)
    return summary

def main():
    parser = argparse.ArgumentParser(description="Summarize resume information using LLM.")
    parser.add_argument("--resume_file", type=str, help="Path to the JSON file containing the resume embeddings.")
    parser.add_argument("--job_description", type=str, help="Job description")
    args = parser.parse_args()

    if not args.resume_file:
        print("Please provide the path to the JSON file containing the resume embeddings.")
        return

    if not args.job_description:
        print("Please provide the job description.")
        return

    try:
        with open(args.resume_file, "r") as f:
            resume_data = json.load(f)
            resume_embedding = resume_data["embedding"]
    except Exception as e:
        print(f"Error loading resume file: {e}")
        return

    summary = summarize_resume(resume_embedding, args.job_description)
    print("\n--- LLM Summary ---")
    print(summary)

if __name__ == "__main__":
    main()
