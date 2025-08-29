import os
import sys
from pathlib import Path
from typing import Dict, Any, List
import logging
import json
from sentence_transformers import SentenceTransformer

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add TEXT_EMBEDDING_MODEL to the python path
text_embedding_model_path = Path(__file__).parent.parent / "TEXT_EMBEDDING_MODEL"
sys.path.append(str(text_embedding_model_path))

try:
    from TEXT_EMBEDDING_MODEL.textEmbedding_model import process_extracted_data
    logger.info("Text embedding model available")
except ImportError:
    logger.warning("Text embedding model not available")

# Import specialized extractors
try:
    from .pdf_parser import extract_resume_text as pdf_extractor
    PDF_EXTRACTOR_AVAILABLE = True
    logger.info("PDF extractor available")
except ImportError:
    PDF_EXTRACTOR_AVAILABLE = False
    logger.warning("PDF extractor not available")

try:
    from .word_parser import extract_word_text as word_extractor
    WORD_EXTRACTOR_AVAILABLE = True
    logger.info("Word extractor available")
except ImportError:
    WORD_EXTRACTOR_AVAILABLE = False
    logger.warning("Word extractor not available")

# Try to import a sectionizer from word_parser for reuse; fallback to local
try:
    from .word_parser import extract_resume_sections as _external_sectionizer  # type: ignore
    SECTIONIZER_AVAILABLE = True
    logger.info("External sectionizer available")
except Exception:
    SECTIONIZER_AVAILABLE = False
    _external_sectionizer = None
    logger.warning("External sectionizer not available; will use local sectionizer")

# Import universal extractor (Tika-based)
try:
    from .universal_parser import extract_any_document as universal_extractor
    UNIVERSAL_EXTRACTOR_AVAILABLE = True
    logger.info("Universal extractor available")
except ImportError:
    UNIVERSAL_EXTRACTOR_AVAILABLE = False
    logger.warning("Universal extractor not available")

class DocumentRouter:
    """Smart document router that dispatches to appropriate extractors with fallbacks."""
    
    def __init__(self):
        self.extractors = {
            'pdf': self._extract_pdf,
            'docx': self._extract_word,
            'doc': self._extract_word,
            'universal': self._extract_universal
        }
        
        # File extension mappings
        self.extension_mapping = {
            '.pdf': 'pdf',
            '.docx': 'docx', 
            '.doc': 'doc',
            # All other extensions go to universal extractor
        }
    
    def _extract_pdf(self, file_path: str) -> Dict[str, Any]:
        """Extract text from PDF files."""
        if not PDF_EXTRACTOR_AVAILABLE:
            logger.warning("PDF extractor not available, falling back to universal")
            return self._extract_universal(file_path)
        
        try:
            logger.info(f"Using PDF extractor for: {file_path}")
            result = pdf_extractor(file_path)
            
            if result["success"]:
                result["method"] = "pdf_extractor"
                return result
            else:
                logger.warning(f"PDF extractor failed: {result['error']}, trying universal")
                return self._extract_universal(file_path)
                
        except Exception as e:
            logger.error(f"PDF extractor error: {e}, falling back to universal")
            return self._extract_universal(file_path)
    
    def _extract_word(self, file_path: str) -> Dict[str, Any]:
        """Extract text from Word documents."""
        if not WORD_EXTRACTOR_AVAILABLE:
            logger.warning("Word extractor not available, falling back to universal")
            return self._extract_universal(file_path)
        
        try:
            logger.info(f"Using Word extractor for: {file_path}")
            result = word_extractor(file_path)
            
            if result["success"]:
                result["method"] = "word_extractor"
                return result
            else:
                logger.warning(f"Word extractor failed: {result['error']}, trying universal")
                return self._extract_universal(file_path)
                
        except Exception as e:
            logger.error(f"Word extractor error: {e}, falling back to universal")
            return self._extract_universal(file_path)
    
    def _extract_universal(self, file_path: str) -> Dict[str, Any]:
        """Extract text using universal extractor (Tika)."""
        if not UNIVERSAL_EXTRACTOR_AVAILABLE:
            return {
                "success": False,
                "file_path": file_path,
                "error": "No extractors available",
                "method": "none"
            }
        
        try:
            logger.info(f"Using universal extractor for: {file_path}")
            result = universal_extractor(file_path)
            result["method"] = "universal_extractor"
            return result
            
        except Exception as e:
            logger.error(f"Universal extractor error: {e}")
            return {
                "success": False,
                "file_path": file_path,
                "error": str(e),
                "method": "universal_extractor"
            }
    
    def _get_extractor_type(self, file_path: str) -> str:
        """Determine which extractor to use based on file extension."""
        file_path = Path(file_path)
        extension = file_path.suffix.lower()  # Handle uppercase extensions
        
        # Check if we have a specific extractor for this extension
        if extension in self.extension_mapping:
            extractor_type = self.extension_mapping[extension]
            
            # Verify the extractor is available
            if extractor_type == 'pdf' and PDF_EXTRACTOR_AVAILABLE:
                return 'pdf'
            elif extractor_type in ['docx', 'doc'] and WORD_EXTRACTOR_AVAILABLE:
                return 'docx'
        
        # Fallback to universal extractor
        return 'universal'
    
    def extract_document(self, file_path: str) -> Dict[str, Any]:
        """
        Main router method - dispatches to appropriate extractor.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Dict containing extraction results with method used
        """
        if not os.path.exists(file_path):
            return {
                "success": False,
                "file_path": file_path,
                "error": "File not found",
                "method": "none"
            }
        
        # Determine which extractor to use
        extractor_type = self._get_extractor_type(file_path)
        logger.info(f"Routing {file_path} to {extractor_type} extractor")
        
        # Call the appropriate extractor
        return self.extractors[extractor_type](file_path)
    
    def process_batch(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        """
        Process multiple documents using the router.
        
        Args:
            file_paths: List of file paths to process
            
        Returns:
            List of extraction results for each file
        """
        results = []
        total_files = len(file_paths)
        
        logger.info(f"Starting batch processing of {total_files} files")
        
        for i, file_path in enumerate(file_paths, 1):
            logger.info(f"Processing file {i}/{total_files}: {file_path}")
            result = self.extract_document(file_path)
            results.append(result)
            
            if result["success"]:
                logger.info(f"✓ Successfully processed: {file_path} (method: {result['method']})")
            else:
                logger.warning(f"✗ Failed to process: {file_path} - {result['error']}")
        
        # Summary statistics
        successful = sum(1 for r in results if r["success"])
        failed = total_files - successful
        
        # Method breakdown
        methods = {}
        for r in results:
            method = r.get("method", "unknown")
            methods[method] = methods.get(method, 0) + 1
        
        logger.info(f"Batch processing complete: {successful} successful, {failed} failed")
        logger.info(f"Method breakdown: {methods}")
        
        return results

    # ==== Structured JSON (in-memory) helpers ==== 

    @staticmethod
    def _local_sectionizer(text: str) -> Dict[str, str]:
        """Lightweight sectionizer to split resume text into labeled sections."""
        sections = {
            "contact_info": "",
            "summary": "",
            "skills": "",
            "experience": "",
            "education": "",
            "projects": "",
            "certifications": "",
            "others": ""
        }
        current = "others"
        for raw_line in text.split("\n"):
            line = raw_line.strip()
            if not line:
                continue
            lower = line.lower()
            if any(k in lower for k in ["contact", "email", "phone", "linkedin", "github"]):
                current = "contact_info"
            elif any(k in lower for k in ["summary", "objective", "profile", "about"]):
                current = "summary"
            elif any(k in lower for k in ["skill", "tech", "tools", "stack"]):
                current = "skills"
            elif any(k in lower for k in ["experience", "employment", "work history", "professional experience", "internship"]):
                current = "experience"
            elif any(k in lower for k in ["education", "university", "college", "degree", "b.tech", "bachelors", "masters", "phd"]):
                current = "education"
            elif any(k in lower for k in ["project", "projects", "portfolio", "case study"]):
                current = "projects"
            elif any(k in lower for k in ["certification", "certifications", "awards", "achievements"]):
                current = "certifications"
            sections[current] += (line + "\n")
        for k in sections:
            sections[k] = sections[k].strip()
        return sections

    def extract_document_structured(self, file_path: str) -> Dict[str, Any]:
        """Extract and return structured JSON with labeled sections (in-memory only)."""
        result = self.extract_document(file_path)
        if not result.get("success"):
            return {
                "success": False,
                "file_path": file_path,
                "error": result.get("error", "Unknown extraction error"),
                "method": result.get("method", "unknown")
            }
        text = result.get("text", "") or ""
        if SECTIONIZER_AVAILABLE and _external_sectionizer is not None:
            sections = _external_sectionizer(text)
        else:
            sections = self._local_sectionizer(text)
        return {
            "success": True,
            "filename": str(Path(file_path).name),
            "file_path": str(file_path),
            "method": result.get("method", "unknown"),
            "sections": sections
        }

    def process_batch_structured(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        """Batch version of extract_document_structured, all in-memory."""
        outputs: List[Dict[str, Any]] = []
        for file_path in file_paths:
            outputs.append(self.extract_document_structured(file_path))
        return outputs

# Convenience functions
def extract_document(file_path: str) -> Dict[str, Any]:
    """Extract text from a single document using the router."""
    router = DocumentRouter()
    return router.extract_document(file_path)

def process_batch_documents(file_paths: List[str]) -> List[Dict[str, Any]]:
    """Process multiple documents using the router."""
    router = DocumentRouter()
    return router.process_batch(file_paths)

def extract_document_structured(file_path: str) -> Dict[str, Any]:
    """Convenience: structured JSON (sections) in-memory, no file writes."""
    router = DocumentRouter()
    return router.extract_document_structured(file_path)

def process_batch_structured(file_paths: List[str]) -> List[Dict[str, Any]]:
    """Convenience: structured JSON (sections) for multiple files."""
    router = DocumentRouter()
    return router.process_batch_structured(file_paths)

def main():
    """Main function for command line usage."""
    if len(sys.argv) > 1:
        file_path = sys.argv[1]

        # --- OPTIMIZATION: Load model once ---
        print("Loading embedding model...")
        model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        print("Model loaded.")

        # 1. Extract data
        extracted_data = extract_document_structured(file_path)

        # 2. Process for embeddings
        db_record = process_extracted_data(extracted_data, model)

        # 3. Now, you would insert `db_record` into your vector DB
        if db_record:
            print("\n--- Record ready for Vector DB ---")
            # Don't print the whole vector, just a summary
            print(f"ID: {db_record['id']}")
            print(f"Vector Dim: {len(db_record['embedding'])}")
            print(f"Metadata Sections: {list(db_record['metadata']['sections'].keys())}")

    else:
        print("Usage: python router.py <file_path>")


if __name__ == "__main__":
    main()
