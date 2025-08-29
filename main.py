"""
Resume Analysis and Matching System - Main Module
Handles document indexing, searching, and job matching operations.
"""

import os
import sys
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
    
    # Batch processing data
    batch_size = 10  # Process 10 resumes at a time
    batch_ids = []
    batch_embeddings = []
    batch_documents = []
    batch_metadatas = []
    
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
            existing = chroma_manager.collection.get(ids=[db_record["id"]])["ids"]
            if existing and len(existing) > 0:
                tqdm.write(f"⚠️ Duplicate skipped: {db_record['id']}")
                continue
        except Exception:
            pass  # If there's an error getting the record, assume it's not a duplicate

        # Prepare batch data
        batch_ids.append(db_record["id"])
        batch_embeddings.append(db_record["embedding"])
        document_text = "\n\n".join(
            f"{name.replace('_', ' ').title()}:\n{text}"
            for name, text in db_record["metadata"].get("sections", {}).items() if text
        ).strip()
        batch_documents.append(document_text)
        
        # Create simplified metadata that ChromaDB can handle
        simplified_metadata = {
            "filename": db_record["metadata"]["filename"],
            "full_text": db_record["metadata"]["full_text"],
            "section_count": len(db_record["metadata"]["sections"])
        }
        batch_metadatas.append(simplified_metadata)
        
        # When batch is full or this is the last item, add to ChromaDB
        if len(batch_ids) >= batch_size or file_path == resume_files[-1]:
            if batch_ids:  # Only add if we have items
                # Store records for batch processing
                processed_records = []
                for file_path in resume_files:
                    structured_data = extract_document_structured(file_path)
                    if not structured_data or not structured_data.get("success"):
                        tqdm.write(f"⚠️ Skipping (extract failed): {os.path.basename(file_path)}")
                        continue

                    db_record = process_extracted_data(structured_data, model)
                    if not db_record:
                        tqdm.write(f"⚠️ Skipping (embed failed): {os.path.basename(file_path)}")
                        continue

                    processed_records.append(db_record)
                
                # Add all records to ChromaDB
                for record in processed_records:
                    chroma_manager.add_record(record)
                print(f"\n✅ Added batch of {len(batch_ids)} resumes to ChromaDB")
                # Clear batches
                batch_ids = []
                batch_embeddings = []
                batch_documents = []
                batch_metadatas = []
    
    print("\nIndexing complete.")

def search_resumes(query: str, n_results: int, chroma_manager: ChromaDBManager, export_json: str = None):
    # Generate embedding for the query
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    query_embedding = model.encode(query, convert_to_tensor=False).tolist()
    results = chroma_manager.query_resumes(query_text=query, query_embedding=query_embedding, n_results=n_results)

    if not results or not results.get('ids', [[]])[0]:
        print("No matching resumes found.")
        return

    ids = results.get('ids', [[]])[0]
    distances = results.get('distances', [[]])[0]
    metadatas = results.get('metadatas', [[]])[0]
    documents = results.get('documents', [[]])[0]

    output = []
    print("\n--- 🏆 Top Resume Matches ---")
    for i, doc_id in enumerate(ids):
        similarity = 1 - distances[i]
        record = {
            "rank": i+1,
            "id": doc_id,
            "filename": metadatas[i].get("filename", "N/A"),
            "similarity": round(similarity, 4),
            "sections": {k: len(v) for k, v in metadatas[i].get("sections", {}).items()}
        }
        output.append(record)
        print(f"\n{i+1}. {record['filename']} | Similarity: {record['similarity']}")
        for section, length in record["sections"].items():
            print(f"   - {section}: {length} chars")

    if export_json:
        with open(export_json, "w") as f:
            json.dump(output, f, indent=4)
        print(f"\n✅ Results exported to {export_json}")

def extract_job_description(job_file_path: str, model: SentenceTransformer) -> Tuple[str, List[float]]:
    """
    Extract text and generate embeddings from a job description file.
    
    Args:
        job_file_path: Path to the job description PDF
        model: Loaded SentenceTransformer model
        
    Returns:
        Tuple of (job_text, job_embedding_vector)
    """
    print(f"\nExtracting job description from: {job_file_path}")
    
    job_data = extract_document_structured(job_file_path)
    if not job_data or not job_data.get("success"):
        raise ValueError(f"Failed to extract text from job description: {job_data.get('error', 'Unknown error')}")
    
    job_text = ""
    for section_name, section_text in job_data.get("sections", {}).items():
        if section_text:
            job_text += f"{section_name.replace('_', ' ').title()}:\n{section_text}\n\n"
    
    job_embedding = model.encode(job_text, convert_to_tensor=False).tolist()
    
    return job_text, job_embedding

def main():
    parser = argparse.ArgumentParser(description="Resume Parser + RAG Search")
    parser.add_argument("--index", type=str, help="Path to resumes directory to index")
    parser.add_argument("--job", type=str, help="Path to job description PDF file")
    parser.add_argument("--query", type=str, help="Direct text query (alternative to --job)")
    parser.add_argument("-n", "--n_results", type=int, default=3, help="Number of matching resumes to return")
    parser.add_argument("--export", type=str, help="Export results to JSON file")
    args = parser.parse_args()

    chroma_manager = ChromaDBManager()
    print("Loading embedding model...")
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    print("Model loaded.")

    if args.index:
        if not os.path.isdir(args.index):
            print(f"Invalid directory: {args.index}")
            return
        index_directory(args.index, model, chroma_manager)
        
        # Handle search/query
    if args.job:
        # Use job description file
        if not os.path.isfile(args.job):
            print(f"Job description file not found: {args.job}")
            return
        
        try:
            job_text, job_embedding = extract_job_description(args.job, model)
            print("\n=== Job Description ===")
            print(job_text[:500] + "..." if len(job_text) > 500 else job_text)
            print("\n=== Finding Matching Resumes ===")
            
            results = chroma_manager.query_resumes(
                query_text=job_text,
                query_embedding=job_embedding,
                n_results=args.n_results
            )
            
            if results and results.get('success'):
                print(f"\n📊 Found {results['total_matches']} matching resumes:")
                for i, result in enumerate(results['results'], 1):
                    print(f"\n📄 Match {i}:")
                    print(f"Filename: {result['filename']}")
                    print(f"Relevance: {result['similarity_percentage']}%")
                    
                    if result.get('sections'):
                        print("\n🎯 Relevant Sections:")
                        for section in sorted(result['sections'], 
                                           key=lambda x: x['similarity_percentage'], 
                                           reverse=True):
                            if section['name'] != 'contact_info':  # Skip contact info
                                print(f"\n  • {section['name'].replace('_', ' ').title()} "
                                      f"({section['similarity_percentage']}% match):")
                                print(f"    {section['text']}")
                    else:
                        print("\nNo highly relevant sections found.")
                    
                    # This section was causing duplicate output and referencing undefined variables
                    # Sections are now handled by the ChromaDB manager's query_resumes method
            else:
                print("No matching resumes found.")
                
            if args.export and results:
                output = []
                for i, doc_id in enumerate(results['ids'][0]):
                    similarity = 1 - results['distances'][0][i]
                    metadata = results['metadatas'][0][i]
                    record = {
                        "rank": i+1,
                        "id": doc_id,
                        "filename": metadata.get("filename", "N/A"),
                        "similarity": round(similarity, 4),
                        "full_text": metadata.get("full_text", ""),
                    }
                    output.append(record)
                
                with open(args.export, "w") as f:
                    json.dump(output, f, indent=2)
                print(f"\n✅ Results exported to {args.export}")
                
        except Exception as e:
            print(f"Error processing job description: {e}")
            return
            
    elif args.query:
        # Direct text query
        query_embedding = model.encode(args.query, convert_to_tensor=False).tolist()
        results = chroma_manager.query_resumes(
            query_text=args.query,
            query_embedding=query_embedding,
            n_results=args.n_results
        )
        
        if results and results.get('ids', [[]])[0]:
            print(f"\nFound {len(results['ids'][0])} matching resumes for query: {args.query}")
            for i, doc_id in enumerate(results['ids'][0]):
                # Convert distance to similarity score (0-1 range)
                distance = results['distances'][0][i]
                similarity = max(0, min(1, 1 - distance))
                metadata = results['metadatas'][0][i]
                print(f"\n📄 Match {i+1}:")
                print(f"Filename: {metadata.get('filename', 'N/A')}")
                # Convert similarity to percentage
                relevance_pct = round(similarity * 100, 1)
                print(f"Relevance: {relevance_pct}%")
                
                # Only show sections with good matches (similarity > 0.3)
                if doc_id in results.get('matching_sections', {}):
                    matching_sections = sorted(
                        [
                            section for section in results['matching_sections'][doc_id]
                            if (1 - section['distance']) > 0.3  # Only show relevant sections
                        ],
                        key=lambda x: x['distance']
                    )
                    
                    if matching_sections:
                        print("\n🎯 Matching Sections:")
                        for section_match in matching_sections:
                            section_similarity = max(0, min(1, 1 - section_match['distance']))
                            section_pct = round(section_similarity * 100, 1)
                            print(f"\n  • {section_match['section'].replace('_', ' ').title()} "
                                  f"({section_pct}% match):")
                            # Clean and format the section text
                            section_text = section_match['text']
                            if section_match['section'] != 'contact_info':  # Skip contact info in preview
                                print(f"    {section_text}")
                    else:
                        print("\nNo highly relevant sections found.")
        else:
            print("No matching resumes found.")
            
    elif not args.index:
        print("No command provided. Use --index to index resumes and/or --job/--query to search.")
            
    elif args.query:
        # Generate embedding for the query
        query_embedding = model.encode(args.query, convert_to_tensor=False).tolist()
        search_resumes(args.query, args.n_results, chroma_manager, export_json=args.export)
    else:
        print("No command provided. Use --index or --query.")

if __name__ == "__main__":
    main()