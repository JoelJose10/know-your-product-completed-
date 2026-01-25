# Know Your Product

A web application where users upload PRDs, Figma files, or screenshots, and an AI pipeline extracts a concise product summary with RAG-enabled chat functionality.

## Tech Stack

- **Frontend**: Vite + React + Tailwind CSS
- **Backend**: FastAPI
- **Vector Database**: Qdrant Cloud
- **AI/ML**: OpenAI Embeddings + GPT-4
- **Orchestration**: LangGraph
- **Observability**: LangSmith

## Project Structure

```
know-your-product/
├── frontend/               # React + Tailwind frontend
│   ├── src/
│   │   ├── components/    # UI components
│   │   ├── App.jsx        # Main app component
│   │   └── main.jsx       # Entry point
│   └── package.json
├── backend/               # FastAPI backend
│   ├── app/
│   │   ├── main.py       # FastAPI app entry
│   │   ├── api/          # API endpoints
│   │   ├── services/     # Business logic
│   │   └── workflows/    # LangGraph pipelines
│   └── requirements.txt
├── infra/                 # Infrastructure configs
│   └── docker-compose.yml
└── .env.example          # Environment variables template
```

## Setup Instructions

### Prerequisites

- Node.js 18+
- Python 3.10+
- Tesseract OCR (for image text extraction)

### 1. Clone and Setup Environment

```bash
# Clone the repository
git clone <repo-url>
cd know-your-product

# Copy environment variables
cp .env.example .env
# Edit .env with your API keys
```

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend will be available at `http://localhost:5173`

### 3. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend API will be available at `http://localhost:8000`

### 4. Install Tesseract (for OCR)

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr
```

**macOS:**
```bash
brew install tesseract
```

**Windows:**
Download installer from https://github.com/UB-Mannheim/tesseract/wiki

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/upload` | POST | Upload files (PDF, DOCX, MD, PNG, JPG) |
| `/summary/{job_id}` | GET | Get product summary for a job |
| `/chat` | POST | RAG-enabled chat with context |
| `/search` | GET | Search vector database |
| `/job/{job_id}/status` | GET | Check job processing status |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key for embeddings and chat |
| `QDRANT_URL` | Qdrant Cloud cluster URL |
| `QDRANT_API_KEY` | Qdrant Cloud API key |
| `LANGCHAIN_API_KEY` | LangSmith API key for tracing |
| `LANGCHAIN_TRACING_V2` | Enable LangSmith tracing (true/false) |
| `LANGCHAIN_PROJECT` | LangSmith project name |

## Features

- **File Upload**: Drag-and-drop support for PRDs, Figma exports, and screenshots
- **Text Extraction**: Automatic extraction from PDF, DOCX, Markdown, and images (OCR)
- **AI Summarization**: GPT-4 powered product summaries
- **RAG Chat**: Context-aware chat using vector search
- **Real-time Progress**: Upload progress and processing status indicators

## License

MIT
