import os
import sys
import subprocess
import platform
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import specialized parsers
try:
    from .pdf_parser import extract_resume_text as extract_pdf_text
    PDF_PARSER_AVAILABLE = True
except ImportError:
    PDF_PARSER_AVAILABLE = False
    logger.warning("PDF parser not available")

try:
    from .word_parser import extract_word_text as extract_docx_text
    WORD_PARSER_AVAILABLE = True
except ImportError:
    WORD_PARSER_AVAILABLE = False
    logger.warning("Word parser not available")

# Tika imports
try:
    import tika
    from tika import parser
    TIKA_AVAILABLE = True
    logger.info("Tika is available")
except ImportError:
    TIKA_AVAILABLE = False
    logger.warning("Tika not available. Install with: pip install tika")

class JavaChecker:
    """Check and install Java for Tika."""
    
    @staticmethod
    def check_java_installed() -> bool:
        """Check if Java is installed and accessible."""
        try:
            result = subprocess.run(['java', '-version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                logger.info("Java is already installed")
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        logger.warning("Java not found or not accessible")
        return False
    
    @staticmethod
    def install_java() -> bool:
        """Install Java based on the operating system."""
        system = platform.system().lower()
        
        try:
            if system == "darwin":  # macOS
                logger.info("Installing Java on macOS...")
                result = subprocess.run(['brew', 'install', 'openjdk@11'], 
                                      capture_output=True, text=True, timeout=300)
                if result.returncode == 0:
                    # Create symlink for system-wide access
                    subprocess.run(['sudo', 'ln', '-sfn', 
                                  '/opt/homebrew/opt/openjdk@11/libexec/openjdk.jdk', 
                                  '/Library/Java/JavaVirtualMachines/openjdk-11.jdk'])
                    logger.info("Java installed successfully on macOS")
                    return True
                else:
                    logger.error(f"Failed to install Java: {result.stderr}")
                    return False
                    
            elif system == "linux":
                logger.info("Installing Java on Linux...")
                # Try different package managers
                package_managers = [
                    ['sudo', 'apt-get', 'update', '&&', 'sudo', 'apt-get', 'install', '-y', 'openjdk-11-jdk'],
                    ['sudo', 'yum', 'install', '-y', 'java-11-openjdk'],
                    ['sudo', 'dnf', 'install', '-y', 'java-11-openjdk']
                ]
                
                for cmd in package_managers:
                    try:
                        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
                        if result.returncode == 0:
                            logger.info("Java installed successfully on Linux")
                            return True
                    except subprocess.TimeoutExpired:
                        continue
                
                logger.error("Failed to install Java on Linux")
                return False
                
            elif system == "windows":
                logger.info("Please install Java manually on Windows:")
                logger.info("Download from: https://adoptium.net/")
                return False
                
            else:
                logger.error(f"Unsupported operating system: {system}")
                return False
                
        except Exception as e:
            logger.error(f"Error installing Java: {e}")
            return False
    
    @staticmethod
    def ensure_java_available() -> bool:
        """Ensure Java is available, install if needed."""
        if JavaChecker.check_java_installed():
            return True
        
        logger.info("Java not found. Attempting to install...")
        return JavaChecker.install_java()

class UniversalParser:
    """Universal document parser with fallback to Tika."""
    
    def __init__(self):
        self.java_available = False
        self.tika_available = TIKA_AVAILABLE
        
        # Ensure Java is available if Tika is needed
        if self.tika_available:
            self.java_available = JavaChecker.ensure_java_available()
    
    def extract_with_tika(self, file_path: str) -> Dict[str, Any]:
        """Extract text using Apache Tika."""
        if not self.tika_available:
            return {
                "success": False,
                "file_path": file_path,
                "error": "Tika not available",
                "method": "tika"
            }
        
        if not self.java_available:
            return {
                "success": False,
                "file_path": file_path,
                "error": "Java not available for Tika",
                "method": "tika"
            }
        
        try:
            logger.info(f"Extracting with Tika: {file_path}")
            
            # Parse document with Tika
            raw = parser.from_file(file_path)
            
            if raw and raw.get("content"):
                return {
                    "success": True,
                    "file_path": file_path,
                    "text": raw["content"].strip(),
                    "metadata": raw.get("metadata", {}),
                    "content_type": raw.get("metadata", {}).get("Content-Type", ""),
                    "method": "tika"
                }
            else:
                return {
                    "success": False,
                    "file_path": file_path,
                    "error": "Tika returned no content",
                    "method": "tika"
                }
                
        except Exception as e:
            logger.error(f"Tika extraction failed: {e}")
            return {
                "success": False,
                "file_path": file_path,
                "error": str(e),
                "method": "tika"
            }
    
    def extract_document(self, file_path: str) -> Dict[str, Any]:
        """
        Extract text from document using specialized parsers first,
        then fallback to Tika if needed.
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            return {
                "success": False,
                "file_path": str(file_path),
                "error": "File not found",
                "method": "none"
            }
        
        # Try specialized parsers first
        if file_path.suffix.lower() == '.pdf' and PDF_PARSER_AVAILABLE:
            logger.info(f"Trying PDF parser: {file_path}")
            result = extract_pdf_text(str(file_path))
            if result["success"]:
                result["method"] = "pdf_parser"
                return result
            else:
                logger.warning(f"PDF parser failed, trying Tika: {result['error']}")
        
        elif file_path.suffix.lower() in ['.docx', '.doc'] and WORD_PARSER_AVAILABLE:
            logger.info(f"Trying Word parser: {file_path}")
            result = extract_docx_text(str(file_path))
            if result["success"]:
                result["method"] = "word_parser"
                return result
            else:
                logger.warning(f"Word parser failed, trying Tika: {result['error']}")
        
        # Fallback to Tika for any format
        logger.info(f"Falling back to Tika: {file_path}")
        return self.extract_with_tika(str(file_path))
    
    def process_batch_documents(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        """
        Process multiple documents with fallback strategy.
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

def extract_any_document(file_path: str) -> Dict[str, Any]:
    """
    Universal document extraction function.
    
    Args:
        file_path: Path to the document file
        
    Returns:
        Dict containing extraction results with method used
    """
    parser = UniversalParser()
    return parser.extract_document(file_path)

def process_batch_any_documents(file_paths: List[str]) -> List[Dict[str, Any]]:
    """
    Process multiple documents of any format.
    
    Args:
        file_paths: List of file paths to process
        
    Returns:
        List of extraction results for each file
    """
    parser = UniversalParser()
    return parser.process_batch_documents(file_paths)

def main():
    """Main function for command line usage."""
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        result = extract_any_document(file_path)
        
        if result["success"]:
            print(f"✓ Successfully extracted text from: {file_path}")
            print(f"Method used: {result['method']}")
            print(f"Text length: {len(result['text'])} characters")
            print(f"Content type: {result.get('content_type', 'N/A')}")
        else:
            print(f"✗ Failed to extract text: {result['error']}")
            print(f"Method attempted: {result.get('method', 'N/A')}")
    else:
        print("Usage: python universal_parser.py <file_path>")
        print("Supports: PDF, Word, PowerPoint, Excel, Text, and many more formats")

if __name__ == "__main__":
    main()
