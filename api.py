"""FastAPI server for the Resume Analysis and Matching System."""

import os
import re
import subprocess
import json
import shutil
import subprocess
import json
import tempfile
import uvicorn
import ollama
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sentence_transformers import SentenceTransformer
from typing import List

# Adjust imports to use the existing project structure
from CHROMA_DB.collections import ChromaDBManager
from main import extract_job_description, index_directory


# --- App Initialization & Global Objects ---

os.environ["TOKENIZERS_PARALLEILLISM"] = "false"
print("Loading embedding model...")
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
print("Model loaded.")
main_chroma_manager = ChromaDBManager()


app = FastAPI(
    title="Resume Analysis and Matching System",
    description="An API for matching resumes to job descriptions using a RAG architecture.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Business Logic ---

def extract_structured_data(resume_text: str) -> dict:
    """
    Extracts name, skills, and years of experience from resume text using regex.
    """
    # Attempt to extract name from the first few lines
    # This is a simple pattern and might need refinement for various resume formats.
    name_pattern = r"^[A-Z][a-z]+(?: [A-Z][a-z]+(?: [A-Z][a-z]+)?)?"
    name_match = re.search(name_pattern, resume_text.split('\n')[0])
    name = name_match.group(0) if name_match else "Unknown Candidate"

    skills_list = [
        "python", "java", "c++", "c#", "javascript", "typescript", "react", "angular", "vue",
        "nodejs", "express", "django", "flask", "fastapi", "ruby", "rails", "php", "laravel",
        "sql", "mysql", "postgresql", "mongodb", "redis", "docker", "kubernetes", "aws",
        "azure", "gcp", "terraform", "ansible", "jenkins", "git", "jira", "scrum", "agile",
        "machine learning", "deep learning", "tensorflow", "pytorch", "scikit-learn",
        "pandas", "numpy", "data analysis", "data science", "natural language processing",
        "computer vision", "html", "css", "tailwind", "bootstrap"
    ]
    
    extracted_skills = []
    for skill in skills_list:
        if re.search(r'\b' + re.escape(skill) + r'\b', resume_text, re.IGNORECASE):
            extracted_skills.append(skill.capitalize())

    experience_pattern = r'(\d+\+?)\s*years? of experience'
    match = re.search(experience_pattern, resume_text, re.IGNORECASE)
    experience = match.group(1) + "+ years" if match else "Not specified"

    return {
        "name": name,
        "skills": list(set(extracted_skills)),
        "experience": experience
    }

def summarize_matches_with_llm_api(job_text: str, matches: dict) -> str:
    """
    Uses a local LLM via Ollama to generate a summary and returns it.
    If it fails, it returns a user-friendly error message.
    """
    print("\n\n🤖 Generating AI Summary for Top Matches...")

    context = ""
    for i, (fname, match) in enumerate(matches.items(), 1):
        context += f"--- Resume {i}: {fname} ---\n"
        context += f"Relevance: {match['match_percentage']}%\n"
        context += f"Matching Section ({match['section_name']}):\n{match['text']}\n\n"

    prompt = f"""
    You are an expert HR assistant. Your task is to analyze the following resumes and provide a summary of why they are a good fit for the given job description.

    **Job Description:**
    {job_text}

    **Top Matching Resumes:**
    {context}

    **Your Task:**
    Based on the job description and the provided resume snippets, write a concise summary for each of the top 2-3 candidates.
    
    **Guidelines:**
    - Highlight their key qualifications, relevant experience, and skills that align with the job requirements.
    - Use bullet points for readability.
    - Structure your response clearly.
    - Keep it brief, professional, and to the point.
    """

    try:
        response = ollama.chat(
            model='qwen2.5:0.5b',
            #model='mistral:instruct',
            messages=[{'role': 'user', 'content': prompt}]
        )
        summary_content = response['message']['content']
        
        # Clean and format the summary content
        cleaned_lines = []
        for line in summary_content.split('\n'):
            stripped_line = line.strip()
            if stripped_line:
                # Remove any leading non-alphanumeric characters and add a bullet point
                cleaned_line = re.sub(r'^\W*', '• ', stripped_line)
                cleaned_lines.append(cleaned_line)
        
        return "\n".join(cleaned_lines)
    except Exception as e:
        error_message = f"⚠️ Could not generate AI summary. Ensure the 'qwen2.5:0.5b' model is available in Ollama.\nError: {e}"
        print(error_message)
        return error_message


from pydantic import BaseModel

class ChatRequest(BaseModel):
    messages: List[dict]
    context: str = None # Optional context

@app.post("/api/chat", tags=["Chat"])
async def chat_endpoint(request: ChatRequest):
    """
    Endpoint for general chat using the local Ollama model.
    """
    try:
        messages = request.messages
        if request.context:
            # Prepend context as a system message
            system_msg = {
                "role": "system",
                "content": (
                    f"You are an expert HR assistant. Your goal is to provide clear, concise, and structured answers based on the provided context.\n"
                    f"Context:\n{request.context}\n\n"
                    f"Guidelines for your response:\n"
                    f"- Use bullet points (•) for lists, comparisons, or key takeaways.\n"
                    f"- Use emojis to make the response engaging and readable (e.g., ✅ for strengths, ⚠️ for gaps, 💼 for experience, 💡 for insights).\n"
                    f"- Keep paragraphs short and use line breaks between points.\n"
                    f"- If comparing candidates, use a structured format (e.g., Candidate A vs. Candidate B).\n"
                    f"- Be professional and direct.\n"
                    f"Answer the user's question based on the above context."
                )
            }
            messages.insert(0, system_msg)

        response = ollama.chat(
            model='qwen2.5:0.5b',
            messages=messages
        )
        return {"response": response['message']['content']}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- API Endpoints ---

@app.get("/api/status", tags=["Monitoring"])
async def get_status():
    """A simple endpoint to confirm the API is running."""
    return {"status": "ok", "message": "API is running."}


@app.post("/api/match-resumes", tags=["Matching"])
async def match_resumes(
    job_description: UploadFile = File(...), 
    resumes: List[UploadFile] = File(...)
):
    """
    Upload a job description and resumes, perform on-the-fly indexing and matching, and return results.
    """
    temp_dir = tempfile.mkdtemp()
    try:
        jd_path = os.path.join(temp_dir, job_description.filename)
        with open(jd_path, "wb") as buffer:
            shutil.copyfileobj(job_description.file, buffer)

        resumes_dir = os.path.join(temp_dir, "resumes")
        os.makedirs(resumes_dir)
        
        resume_full_texts = {} # Dictionary to store full text of each resume
        for resume in resumes:
            resume_path = os.path.join(resumes_dir, resume.filename)
            with open(resume_path, "wb") as buffer:
                shutil.copyfileobj(resume.file, buffer)
            
            # Read full text of the resume using the universal parser from KNOWLEDGE_EXTRACTOR
            # This assumes the universal_parser can handle various document types.
            # I need to import universal_parser from KNOWLEDGE_EXTRACTOR.universal_parser
            from KNOWLEDGE_EXTRACTOR.universal_parser import UniversalParser
            parser = UniversalParser()
            try:
                parsed_data = parser.parse_file(resume_path)
                if parsed_data and parsed_data.get("text"): # Assuming 'text' key holds the full content
                    resume_full_texts[resume.filename] = parsed_data["text"]
                else:
                    print(f"Warning: Could not extract text from {resume.filename} using UniversalParser.")
                    resume_full_texts[resume.filename] = ""
            except Exception as e:
                print(f"Error parsing {resume.filename} with UniversalParser: {e}")
                resume_full_texts[resume.filename] = ""


        temp_collection_name = f"temp_collection_{os.urandom(8).hex()}"
        temp_sections_collection_name = f"temp_sections_collection_{os.urandom(8).hex()}"
        temp_chroma_manager = ChromaDBManager(
            in_memory=True,
            collection_name=temp_collection_name,
            sections_collection_name=temp_sections_collection_name
        )
        
        print(f"Starting on-the-fly indexing for {len(resumes)} resumes into collection '{temp_collection_name}'...")
        index_directory(resumes_dir, model, temp_chroma_manager)
        print("On-the-fly indexing complete.")

        job_text, job_embedding = extract_job_description(jd_path, model)

        results = temp_chroma_manager.query(
            query_text=job_text,
            query_embedding=job_embedding,
            top_k=10,
            min_similarity=0.1,
        )

        if not results or not results.get("matches"):
            return {"matches": {}, "summary": "No matching resumes found in the uploaded files."}

        best_matches = {}
        for match in results["matches"]:
            fname = match["filename"]
            if fname not in best_matches or match["match_percentage"] > best_matches[fname]["match_percentage"]:
                # Get full text for structured data extraction
                full_resume_text = resume_full_texts.get(fname, "")
                structured_data = extract_structured_data(full_resume_text)
                
                match['name'] = structured_data['name'] # Add extracted name
                match['skills'] = structured_data['skills']
                match['experience'] = structured_data['experience']
                match['full_text'] = full_resume_text # Add full text for context
                best_matches[fname] = match
        
        sorted_matches = dict(sorted(best_matches.items(), key=lambda item: item[1]['match_percentage'], reverse=True))

        summary = summarize_matches_with_llm_api(job_text, sorted_matches)

        return {"matches": sorted_matches, "summary": summary}

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        shutil.rmtree(temp_dir)


@app.post("/api/index-resumes", tags=["Indexing"])
async def index_resumes_endpoint(resumes_path: str = "DATA_resume"):
    """
    Triggers the indexing of resumes from the specified directory.
    """
    if not os.path.isdir(resumes_path):
        raise HTTPException(status_code=404, detail=f"Directory not found: {resumes_path}")
    
    try:
        print(f"Starting indexing for directory: {resumes_path} into main database.")
        index_directory(resumes_path, model, main_chroma_manager)
        return {"status": "success", "message": f"Indexing complete for {resumes_path}."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Indexing failed: {e}")

@app.get("/api/resume-embedding/{resume_id}", tags=["Resumes"])
async def get_resume_embedding(resume_id: str):
    """Retrieve the full resume text embedding given a resume ID."""
    embedding = main_chroma_manager.get_resume_embedding(resume_id)
    if not embedding:
        raise HTTPException(status_code=404, detail=f"Resume with ID '{resume_id}' not found.")
    return {"embedding": embedding}

@app.post("/api/summarize-resume", tags=["Resumes"])
async def summarize_resume(resume_embedding: dict, job_description: str):
    """Summarize the resume information using the LLM."""
    try:
        # Create a temporary file to store the resume embedding
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            json.dump(resume_embedding, f)
            temp_file_path = f.name

        # Run the SLM_manager/augemented_generation.py script with the temporary file
        command = [
            "python",
            "/Users/deepandee/Desktop/RAG/SLM_manager/augemented_generation.py",
            "--resume_file",
            temp_file_path,
            "--job_description",
            job_description,
        ]
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        # Check for errors
        if stderr:
            print(f"Error summarizing resume: {stderr.decode()}")
            raise HTTPException(status_code=500, detail=f"Error summarizing resume: {stderr.decode()}")

        # Extract the summary from the output
        summary = stdout.decode().strip()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up the temporary file
        os.remove(temp_file_path)

    return {"summary": summary}

# --- Server Startup ---
if __name__ == "__main__":

    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
