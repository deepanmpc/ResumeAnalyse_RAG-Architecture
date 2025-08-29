from CHROMA_DB.collections import ChromaDBManager, load_job_description_pdf
from sentence_transformers import SentenceTransformer
from langchain_community.llms import Ollama

# Initialize
embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
chroma_manager = ChromaDBManager()
llm = Ollama(model="mistral:instruct", temperature=0.7)

# Query job description
job_path = "/Users/deepandee/Desktop/RAG/JOB_DESCRIPTIONS/online_exam_developer_job.pdf"
job_text = load_job_description_pdf(job_path)
job_emb = embedding_model.encode(job_text).tolist()

matches = chroma_manager.query(job_text, job_emb, top_k=10, min_similarity=0.1)

# Deduplicate matches
seen = set()
unique_matches = []
for m in matches['matches']:
    key = (m['resume_id'], m['section_name'])
    if key not in seen:
        seen.add(key)
        unique_matches.append(m)

# Prepare prompt for LLM
prompt = f"""
Summarize the following unique candidate matches for the job:

{unique_matches}

For each candidate, provide:
1. Qualifications summary
2. Key strengths and gaps
3. Overall ranking
"""

summary = llm.invoke(prompt)
print("\n--- LLM Summary ---")
print(summary)