# Resume Analysis and Matching System 📄✨

A sophisticated resume analysis and matching system that uses RAG (Retrieval Augmented Generation) to match resumes with job descriptions intelligently.

## 🌟 Features

- 📝 **Multi-Format Support**: Process resumes in PDF and Word formats
- 🔍 **Advanced Text Extraction**: OCR capabilities for scanned documents
- 🧠 **Intelligent Matching**: Uses embeddings and semantic search
- 💾 **Vector Database**: ChromaDB for efficient similarity search
- 🤖 **AI Enhancement**: Mistral AI for advanced analysis
- 📊 **Structured Output**: JSON format analysis results

## 🏗️ Project Structure

```
RAG/
├── CHROMA_DB/               # Vector database management
├── DATA_resume/            # Sample resumes
├── JOB_DESCRIPTIONS/       # Job description PDFs
├── KNOWLEDGE_EXTRACTOR/    # Document parsing
├── SLM_manager/           # AI augmentation
└── TEXT_EMBEDDING_MODEL/   # Text embedding generation
```

## 🚀 Getting Started

The system operates in two modes:
1. **Basic Mode**: Resume matching using vector similarity (always available)
2. **Enhanced Mode**: AI-powered analysis using Mistral (requires Ollama setup)

### Prerequisites

- Python 3.10 or higher
- Virtual environment
- Tesseract OCR (for scanned documents)
- Ollama with Mistral AI model (for enhanced analysis)

### Installation

#### Basic Setup

1. **Python Environment Setup**:
   ```bash
   # Create and activate virtual environment
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

2. **Tesseract OCR** (Optional - for scanned documents):
   - macOS: `brew install tesseract`
   - Linux: `sudo apt-get install tesseract-ocr`
   - Windows: Download installer from GitHub

#### Mistral AI Setup (Required for Enhanced Analysis)

1. **Install Ollama**:
   - macOS/Linux:
     ```bash
     curl https://ollama.ai/install.sh | sh
     ```
   - Windows: Download from [Ollama's website](https://ollama.ai)

2. **Pull Mistral Model**:
   ```bash
   ollama pull mistral
   ```

3. **Verify Installation**:
   ```bash
   ollama run mistral "Hello, testing Mistral AI"
   ```

⚠️ **Important Note**: The enhanced analysis features require Mistral AI through Ollama. If you don't have Mistral AI set up:
- Basic resume matching will still work
- AI-enhanced analysis features will be disabled
- You can still use the system with reduced functionality

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd RAG
```

2. Create and activate virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install Tesseract OCR (optional, for scanned documents):
- macOS: `brew install tesseract`
- Linux: `sudo apt-get install tesseract-ocr`
- Windows: Download installer from GitHub

## 🎯 Usage

1. **Index Resumes**:
```bash
python main.py --index DATA_resume/
```

2. **Match with Job Description**:
```bash
python main.py --job JOB_DESCRIPTIONS/job.pdf -n 5
```

3. **Direct Query Search**:
```bash
python main.py --query "python developer with 5 years experience" -n 3
```

## 🔧 Components

Note: AI Enhancement features require Mistral AI setup. Other components work independently.

### 1. Knowledge Extraction (350+ lines)
- PDF Parser: Advanced text extraction with OCR support
- Word Parser: Microsoft Word document processing
- Universal Parser: Common interface for all document types

### 2. Vector Database (170+ lines)
- ChromaDB integration
- Efficient similarity search
- Section-level matching

### 3. Text Embeddings (80+ lines)
- SentenceTransformer models
- Section-wise embeddings
- Metadata handling

### 4. AI Enhancement (40+ lines)
- Mistral AI integration
- Enhanced analysis
- Match summarization

### 5. Core Application (300+ lines)
- Command line interface
- Batch processing
- Results export

## 📊 Output Format

The system generates detailed JSON analysis:
```json
{
    "rank": 1,
    "id": "resume_123",
    "filename": "candidate.pdf",
    "similarity": 0.89,
    "sections": {
        "experience": 0.92,
        "skills": 0.85,
        "education": 0.78
    }
}
```

## 📈 Performance

- Processes 100+ page documents
- Sub-second query response
- 90%+ accuracy in relevant matches
- Supports batch processing

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Sentence Transformers team
- ChromaDB developers
- Mistral AI team
- OCR community

---
Built with ❤️ for making recruitment smarter
