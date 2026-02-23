"""
Resume Analysis and Matching System - Main Module
Handles document indexing, searching, and job matching operations.
"""

import os
import argparse
import json
from typing import List, Tuple
from pathlib import Path

os.environ["TOKENIZERS_PARALLELISM"] = "false"
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
from KNOWLEDGE_EXTRACTOR.router import extract_document_structured
from TEXT_EMBEDDING_MODEL.textEmbedding_model import process_extracted_data
from CHROMA_DB.collections import ChromaDBManager


SUPPORTED_EXTENSIONS = [".pdf", ".docx", ".doc"]


def index_directory(resumes_path: str, model: SentenceTransformer, chroma_manager: ChromaDBManager):
    resume_files = []
    for root, _, files in os.walk(resumes_path):
        for file in files:
            if any(file.lower().endswith(ext) for ext in SUPPORTED_EXTENSIONS):
                resume_files.append(os.path.join(root, file))

    if not resume_files:
        print(f"No resumes found in {resumes_path}")
        return

    print(f"Found {len(resume_files)} resumes to process.")

    for file_path in tqdm(resume_files, desc="Processing Resumes"):
        structured_data = extract_document_structured(file_path)
        if not structured_data or not structured_data.get("success"):
            tqdm.write(f"⚠️ Skipping (extract failed): {os.path.basename(file_path)}")
            continue

        db_record = process_extracted_data(structured_data, model)
        if not db_record:
            tqdm.write(f"⚠️ Skipping (embed failed): {os.path.basename(file_path)}")
            continue

        try:
            existing = chroma_manager.sections_collection.get(
                ids=[db_record["id"]]
            )["ids"]
            if existing and len(existing) > 0:
                tqdm.write(f"⚠️ Duplicate skipped: {db_record['id']}")
                continue
        except Exception:
            pass

        chroma_manager.add_record(db_record)

    print("\nIndexing complete.")


def extract_job_description(job_file_path: str, model: SentenceTransformer) -> Tuple[str, List[float]]:
    """
    Extract text and generate embeddings from a job description file.
    """
    print(f"\nExtracting job description from: {job_file_path}")

    job_data = extract_document_structured(job_file_path)
    if not job_data or not job_data.get("success"):
        raise ValueError(
            f"Failed to extract text from job description: {job_data.get('error', 'Unknown error')}"
        )

    job_text = ""
    for section_name, section_text in job_data.get("sections", {}).items():
        if section_text:
            job_text += f"{section_name.replace('_', ' ').title()}:\n{section_text}\n\n"

    job_embedding = model.encode(job_text, convert_to_tensor=False).tolist()

    return job_text, job_embedding


def summarize_matches_with_llm(job_text: str, matches: dict):
    """
    Uses a local LLM via Ollama to generate a summary for the top matches.
    """
    print("\n\n🤖 Generating AI Summary for Top Matches...")

    try:
        import ollama
        # Prepare the context from the top matches
        context = ""
        for i, (fname, match) in enumerate(matches.items(), 1):
            context += f"--- Resume {i}: {fname} ---\n"
            context += f"Relevance: {match['match_percentage']}%\n"
            context += f"Matching Section ({match['section_name']}):\n{match['text']}\n\n"

        # Create the prompt for the LLM
        prompt = f"""
        You are an expert HR assistant. Your task is to analyze the following resumes and provide a summary of why they are a good fit for the given job description.
        **Job Description:**
        {job_text}

        **Top Matching Resumes:**
        {context}

        **Your Task:**
        Based on the job description and the provided resume snippets, write a concise summary for each of the top 2-3 candidates. Highlight their key qualifications, relevant experience, and skills that align with the job requirements. Keep it brief and to the point.
        """

        response = ollama.chat(
            model='qwen2.5:0.5b',
            #model='mistral',
            messages=[{'role': 'user', 'content': prompt}]
        )
        print("--- AI Summary ---")
        print(response['message']['content'])
    except (ImportError, ModuleNotFoundError):
        print("\n⚠️ Ollama is not installed. Skipping AI summary.")
        print("To enable summaries, run: pip install ollama")
    except Exception as e:
        print(f"\n⚠️ Could not generate summary. Ensure Ollama is running and the 'qwen2.5:0.5b' model is installed.")
        print(f"Error: {e}")


def main():
    parser = argparse.ArgumentParser(description="Resume Parser + RAG Search")
    parser.add_argument("--index", type=str, help="Path to resumes directory to index")
    parser.add_argument("--job", type=str, help="Path to job description PDF file")
    parser.add_argument("--query", type=str, help="Direct text query (alternative to --job)")
    parser.add_argument("-n", "--n_results", type=int, default=5, help="Number of matching resumes to return")
    parser.add_argument("--export", type=str, help="Export results to JSON file")
    args = parser.parse_args()

    chroma_manager = ChromaDBManager()
    print("Loading embedding model...")
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    print("Model loaded.")

    if args.index:
        if not os.path.isdir(args.index):
            print(f"Invalid directory: {args.index}")
            return
        index_directory(args.index, model, chroma_manager)

    if args.job:
        if not os.path.isfile(args.job):
            print(f"Job description file not found: {args.job}")
            return

        try:
            job_text, job_embedding = extract_job_description(args.job, model)
            print("\n=== Job Description ===")
            print(job_text[:500] + "..." if len(job_text) > 500 else job_text)
            print("\n=== Finding Matching Resumes ===")


            results = chroma_manager.query(
                query_text=job_text,
                query_embedding=job_embedding,
                top_k=args.n_results,
                min_similarity=0.0,  # Lower threshold for debug
            )

            # Debug: Print all section matches and their similarity scores
            print("\n--- Debug: All Section Matches and Similarity Scores ---")
            if results and results.get("matches"):
                for i, match in enumerate(results["matches"], 1):
                    print(f"[{i}] Resume: {match['filename']} | Section: {match['section_name']} | Score: {match['match_percentage']}% | Text: {match['text'][:100]}...")

                # Deduplicate by resume_id (pick best section per resume)
                best_matches = {}
                for match in results["matches"]:
                    fname = match["filename"]
                    if fname not in best_matches or match["match_percentage"] > best_matches[fname]["match_percentage"]:
                        best_matches[fname] = match

                print("\n" + "="*50)
                print("Matching Results:")
                print("  The system now ranks the candidates as follows:\n")
                
                rank_emojis = ["🥇", "🥈", "🥉"]
                
                for i, (fname, match) in enumerate(best_matches.items(), 1):
                    emoji = rank_emojis[i-1] if i <= 3 else "📄"
                    display_name = fname.replace("_", " ").replace(".docx", "").replace(".pdf", "").title()
                    
                    print(f"   {i}. {emoji} {display_name} ({fname})")
                    print(f"       * Relevance: {match['match_percentage']}%")
                    
                    # Simple logic-based 'Why' if LLM summary isn't available yet
                    why_text = f"Strong match in the '{match['section_name']}' section."
                    if "skills" in match['section_name']:
                        why_text = "Highly relevant technical skills found in the profile."
                    elif "experience" in match['section_name']:
                        why_text = "Strong professional experience matching the job requirements."
                    
                    print(f"       * Why: {why_text}")
                    
                    # Show content snippet for context
                    if match["section_name"] != "contact_info":
                        snippet = match['text'][:150].replace('\n', ' ').strip()
                        print(f"       * Snippet: {snippet}...")
                    print()

                # Export if requested
                if args.export:
                    with open(args.export, "w") as f:
                        json.dump(best_matches, f, indent=2)
                    print(f"✅ Results exported to {args.export}")

                # Generate LLM Summary
                summarize_matches_with_llm(job_text, best_matches)
            else:
                print("No section matches found at any similarity score.")

        except Exception as e:
            print(f"Error processing job description: {e}")
            return

    elif args.query:
        query_embedding = model.encode(args.query, convert_to_tensor=False).tolist()
        results = chroma_manager.query(
            query_text=args.query,
            query_embedding=query_embedding,
            top_k=args.n_results,
            min_similarity=0.1,
        )

        if results and results.get("matches"):
            best_matches = {}
            for match in results["matches"]:
                fname = match["filename"]
                if fname not in best_matches or match["match_percentage"] > best_matches[fname]["match_percentage"]:
                    best_matches[fname] = match

            print(f"\n📊 Found {len(best_matches)} unique matching resumes:")
            for i, (fname, match) in enumerate(best_matches.items(), 1):
                print(f"\n📄 Match {i}:")
                print(f"File: {fname}")
                print(f"Best Section: {match['section_name']}")
                print(f"Relevance: {match['match_percentage']}%")
                if match["section_name"] != "contact_info":
                    print(f"Content: {match['text'][:300]}...")

        else:
            print("No matching resumes found.")

    elif not args.index:
        print("No command provided. Use --index to index resumes and/or --job/--query to search.")


if __name__ == "__main__":
    main()