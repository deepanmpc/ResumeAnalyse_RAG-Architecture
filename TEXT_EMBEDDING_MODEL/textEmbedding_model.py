"""
Text Embedding Model for Resume Analysis
Handles the generation of document and section-level embeddings.
"""

import json
import os
import hashlib
from sentence_transformers import SentenceTransformer
from typing import Dict, Any

def process_extracted_data(
    extracted_data: Dict[str, Any],
    model: SentenceTransformer
) -> Dict[str, Any] | None:
    """
    Generate embeddings for document content and individual sections.
    
    Args:
        extracted_data: Dictionary containing document text and metadata
        model: Pre-loaded SentenceTransformer model
        
    Returns:
        Dictionary containing document ID, embeddings, and metadata
    """

    if not (extracted_data and extracted_data.get("success")):
        print("\n❌ Failed to extract text from the resume.")
        print("Error:", extracted_data.get("error", "Unknown error"))
        return None

    sections = extracted_data.get("sections", {})
    # Reconstruct the full text and also keep section text for metadata
    full_text = "\n".join(sections.values()).strip()

    filename = extracted_data.get("filename")
    file_path = extracted_data.get("file_path")
    
    # Create deterministic ID based on file path and last modified time
    import os
    import hashlib
    
    last_modified = str(os.path.getmtime(file_path))
    id_string = f"{file_path}_{last_modified}"
    hash_id = hashlib.md5(id_string.encode()).hexdigest()[:8]
    record_id = f"{filename}_{hash_id}"
    
    print(f"\nProcessing embeddings for: {filename}")
    print(f"Assigned record ID: {record_id}")

    if not full_text:
        print("⚠️ Skipping embedding generation as no text was extracted.")
        return None

    # 1. Full Text Embedding
    full_embedding = model.encode(full_text, convert_to_tensor=False).tolist()
    print(f"\n✅ Full-text embedding generated (length: {len(full_embedding)})")

    # 2. Section Embeddings
    section_embeddings = {}
    section_texts = {}
    for section_name, section_text in sections.items():
        clean_text = section_text.strip()
        if clean_text:
            emb = model.encode(clean_text, convert_to_tensor=False).tolist()
            section_texts[section_name] = clean_text
            section_embeddings[section_name] = emb
            print(f"  Section: {section_name} | Length: {len(emb)}")

    # 3. Prepare DB record
    db_record = {
        "id": record_id,
        "embedding": full_embedding,
        "metadata": {
            "filename": filename,
            "full_text": full_text,
            "sections": section_texts,
            "section_embeddings": section_embeddings
        }
    }

    # Pretty print final object (without flooding vectors)
    print("\n--- Final DB Record Preview ---")
    preview = {
        "id": db_record["id"],
        "embedding_shape": len(db_record["embedding"]),
        "metadata_keys": list(db_record["metadata"].keys()),
        "section_names": list(db_record["metadata"]["sections"].keys())
    }
    print(json.dumps(preview, indent=4))

    return db_record