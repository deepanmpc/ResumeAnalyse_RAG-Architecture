"""
PDF Parser Module for Resume Analysis
Provides advanced text extraction with OCR support for PDF documents.
"""

import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging

try:
    from PyPDF2 import PdfReader
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False
    print("PyPDF2 not found. Install with: pip install PyPDF2")

try:
    import pytesseract
    from pdf2image import convert_from_path
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    print("OCR libraries not found. Install with: pip install pytesseract pdf2image")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PDFExtractor:
    """Advanced PDF text extractor with OCR support and error handling."""
    
    def __init__(self, pdf_path: str):
        self.pdf_path = Path(pdf_path)
        self.reader = None
        self.is_encrypted = False
        self.text_content = {}
        
    def validate_file(self) -> bool:
        """Validate PDF file exists and is accessible."""
        if not self.pdf_path.exists():
            logger.error(f"PDF file not found: {self.pdf_path}")
            return False
        
        if not self.pdf_path.is_file():
            logger.error(f"Path is not a file: {self.pdf_path}")
            return False
            
        if self.pdf_path.stat().st_size == 0:
            logger.error(f"PDF file is empty: {self.pdf_path}")
            return False
            
        return True
    
    def load_pdf(self) -> bool:
        """Load PDF with error handling."""
        try:
            self.reader = PdfReader(self.pdf_path)
            
            # Check if PDF is encrypted
            if self.reader.is_encrypted:
                self.is_encrypted = True
                logger.warning("PDF is encrypted. Text extraction may be limited.")
                
            logger.info(f"PDF loaded successfully. Pages: {len(self.reader.pages)}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load PDF: {e}")
            return False
    
    def extract_text_from_page(self, page, page_num: int) -> str:
        """Extract text from a single page using multiple methods."""
        text = ""
        
        # Method 1: Direct text extraction
        try:
            text = page.extract_text()
            if text and text.strip():
                logger.info(f"Page {page_num + 1}: Text extracted successfully")
                return text
        except Exception as e:
            logger.warning(f"Page {page_num + 1}: Text extraction failed - {e}")
        
        # Method 2: OCR for scanned PDFs (if available)
        if not text and OCR_AVAILABLE:
            try:
                text = self._extract_text_with_ocr(page_num)
                if text and text.strip():
                    logger.info(f"Page {page_num + 1}: Text extracted via OCR")
                    return text
            except Exception as e:
                logger.warning(f"Page {page_num + 1}: OCR failed - {e}")
        
        # Method 3: Try alternative extraction methods
        try:
            # Try to get text from annotations
            if hasattr(page, 'annotations'):
                for annotation in page.annotations:
                    if hasattr(annotation, 'get_text'):
                        text += annotation.get_text() + "\n"
            
            # Try to get text from form fields
            if hasattr(page, 'get_form_text_fields'):
                form_fields = page.get_form_text_fields()
                for field_name, field_value in form_fields.items():
                    if field_value:
                        text += f"{field_name}: {field_value}\n"
                        
        except Exception as e:
            logger.debug(f"Alternative extraction methods failed: {e}")
        
        return text.strip() if text else ""
    
    def _extract_text_with_ocr(self, page_num: int) -> str:
        """Extract text from scanned PDF using OCR."""
        try:
            # Convert PDF page to image
            images = convert_from_path(
                self.pdf_path, 
                first_page=page_num + 1, 
                last_page=page_num + 1,
                dpi=300  # Higher DPI for better OCR accuracy
            )
            
            if images:
                # Extract text using OCR
                text = pytesseract.image_to_string(images[0], lang='eng')
                return text
                
        except Exception as e:
            logger.error(f"OCR processing failed: {e}")
            
        return ""
    
    def extract_all_text(self) -> Dict[str, Any]:
        """Extract text from all pages with comprehensive metadata."""
        if not self.validate_file():
            return {"error": "Invalid PDF file"}
        
        if not self.load_pdf():
            return {"error": "Failed to load PDF"}
        
        result = {
            "file_path": str(self.pdf_path),
            "total_pages": len(self.reader.pages),
            "is_encrypted": self.is_encrypted,
            "pages": {},
            "full_text": "",
            "metadata": {}
        }
        
        # Extract metadata
        try:
            if self.reader.metadata:
                result["metadata"] = {
                    "title": self.reader.metadata.get('/Title', ''),
                    "author": self.reader.metadata.get('/Author', ''),
                    "subject": self.reader.metadata.get('/Subject', ''),
                    "creator": self.reader.metadata.get('/Creator', ''),
                    "producer": self.reader.metadata.get('/Producer', ''),
                    "creation_date": self.reader.metadata.get('/CreationDate', ''),
                    "modification_date": self.reader.metadata.get('/ModDate', '')
                }
        except Exception as e:
            logger.warning(f"Failed to extract metadata: {e}")
        
        # Extract text from each page
        for page_num, page in enumerate(self.reader.pages):
            page_text = self.extract_text_from_page(page, page_num)
            
            result["pages"][page_num + 1] = {
                "text": page_text,
                "has_text": bool(page_text.strip()),
                "extraction_method": "direct" if page_text else "none"
            }
            
            result["full_text"] += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
        
        return result
    
    def save_extracted_text(self, output_path: Optional[str] = None) -> str:
        """Save extracted text to a file."""
        result = self.extract_all_text()
        
        if "error" in result:
            logger.error(f"Cannot save: {result['error']}")
            return ""
        
        if not output_path:
            output_path = self.pdf_path.with_suffix('.txt')
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(f"PDF Text Extraction Results\n")
                f.write(f"File: {result['file_path']}\n")
                f.write(f"Pages: {result['total_pages']}\n")
                f.write(f"Encrypted: {result['is_encrypted']}\n")
                f.write(f"Extracted on: {result.get('extraction_date', 'Unknown')}\n")
                f.write("=" * 50 + "\n\n")
                f.write(result['full_text'])
            
            logger.info(f"Text saved to: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Failed to save text: {e}")
            return ""

def extract_resume_text(file_path: str) -> Dict[str, Any]:
    """
    Extract text from a single resume file.
    
    Args:
        file_path: Path to the resume file
        
    Returns:
        Dict containing extraction results with keys:
        - success: Boolean indicating if extraction was successful
        - file_path: Original file path
        - text: Extracted text content
        - metadata: PDF metadata if available
        - pages: Page-by-page extraction details
        - error: Error message if extraction failed
    """
    try:
        extractor = PDFExtractor(file_path)
        result = extractor.extract_all_text()
        
        if "error" in result:
            return {
                "success": False,
                "file_path": file_path,
                "error": result["error"]
            }
        
        return {
            "success": True,
            "file_path": file_path,
            "text": result["full_text"],
            "metadata": result["metadata"],
            "pages": result["pages"],
            "total_pages": result["total_pages"],
            "is_encrypted": result["is_encrypted"]
        }
        
    except Exception as e:
        logger.error(f"Failed to extract text from {file_path}: {e}")
        return {
            "success": False,
            "file_path": file_path,
            "error": str(e)
        }

def process_batch_resumes(file_paths: List[str]) -> List[Dict[str, Any]]:
    """
    Process multiple resume files in batch.
    
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
        result = extract_resume_text(file_path)
        results.append(result)
        
        if result["success"]:
            logger.info(f"✓ Successfully processed: {file_path}")
        else:
            logger.warning(f"✗ Failed to process: {file_path} - {result['error']}")
    
    # Summary statistics
    successful = sum(1 for r in results if r["success"])
    failed = total_files - successful
    
    logger.info(f"Batch processing complete: {successful} successful, {failed} failed")
    
    return results

def extract_resume_sections(text: str) -> Dict[str, str]:
    """
    Extract structured sections from resume text.
    
    Args:
        text: Raw resume text
        
    Returns:
        Dict with structured sections (skills, experience, education, etc.)
    """
    sections = {
        "contact_info": "",
        "skills": "",
        "experience": "",
        "education": "",
        "summary": "",
        "other": ""
    }
    
    # Simple section extraction using keywords
    lines = text.split('\n')
    current_section = "other"
    
    for line in lines:
        line_lower = line.lower().strip()
        
        # Detect sections based on keywords
        if any(keyword in line_lower for keyword in ['skill', 'technology', 'programming', 'framework']):
            current_section = "skills"
        elif any(keyword in line_lower for keyword in ['experience', 'work', 'employment', 'job']):
            current_section = "experience"
        elif any(keyword in line_lower for keyword in ['education', 'degree', 'university', 'college', 'school']):
            current_section = "education"
        elif any(keyword in line_lower for keyword in ['summary', 'profile', 'objective', 'about']):
            current_section = "summary"
        elif any(keyword in line_lower for keyword in ['email', 'phone', '@', 'linkedin', 'github']):
            current_section = "contact_info"
        
        # Add line to current section
        if line.strip():
            sections[current_section] += line + "\n"
    
    # Clean up sections
    for key in sections:
        sections[key] = sections[key].strip()
    
    return sections

def main():
    """Main function for command line usage (kept for backward compatibility)."""
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        result = extract_resume_text(pdf_path)
        
        if result["success"]:
            print(f"✓ Successfully extracted text from: {pdf_path}")
            print(f"Text length: {len(result['text'])} characters")
            print(f"Pages: {result['total_pages']}")
        else:
            print(f"✗ Failed to extract text: {result['error']}")
    else:
        print("Usage: python pdf_parser.py <file_path>")
        print("For batch processing, use the programmatic functions directly.")

if __name__ == "__main__":
    main()