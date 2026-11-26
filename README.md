# Know Your Product

Upload PRDs, docs, or screenshots and get an AI-generated product summary plus RAG chat over the uploaded content.

## Tech Stack

- **Frontend**: Vite + React + Tailwind CSS
- **Backend**: FastAPI
- **Vector Database**: Qdrant (local or Cloud)
- **AI/ML**: GPT-4o-mini + `text-embedding-3-small` via KeyValue LiteLLM
- **Orchestration**: LangGraph
- **Observability**: LangSmith (optional)

## Project Structure

```
know-your-product/
├── frontend/                 # React + Tailwind
│   ├── src/
│   │   ├── components/
│   │   ├── App.jsx           # UI; API base defaults to /api (Vite proxy)
│   │   └── main.jsx
│   ├── vite.config.js        # Dev server, allowedHosts, /api → :8000 proxy
│   └── package.json
├── backend/                  # FastAPI
│   ├── app/
│   │   ├── main.py           # App entry, CORS, /health
│   │   ├── api/              # upload, summary, chat, search
│   │   ├── services/         # extraction, embeddings, RAG, Qdrant
│   │   └── workflows/        # LangGraph pipeline
│   ├── requirements.txt
│   └── .env                  # Local secrets (not committed)
├── infra/
│   └── docker-compose.yml    # Optional local Qdrant
├── .env.example
└── README.md
```

## Prerequisites

- Node.js 18+
- Python 3.10+
- Qdrant (local Docker or [Qdrant Cloud](https://cloud.qdrant.io))
- Tesseract OCR (only if you upload images)
- KeyValue LiteLLM access (`LITE_LLM_KEY`; VPN if off-office network)

## Setup

### 1. Clone and env

```bash
git clone https://github.com/JoelJose10/know-your-product-completed-.git
cd know-your-product-completed-

cp .env.example backend/.env
# Edit backend/.env — set LITE_LLM_KEY and Qdrant settings
```

### 2. Qdrant (local example)

```bash
docker compose -f infra/docker-compose.yml --profile local-qdrant up -d
```

Or point `QDRANT_URL` / `QDRANT_API_KEY` at Qdrant Cloud in `backend/.env`.

### 3. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API: `http://localhost:8000` — check `GET /health`.

### 4. Frontend

```bash
cd frontend
npm install
npm run dev
```

UI: `http://localhost:5173`

By default the app calls **`/api`**, and Vite proxies that to `http://localhost:8000`. You usually do **not** need to set a backend URL for local or ngrok-frontend setups.

Optional override:

```bash
# frontend only — skip proxy and call a public API URL directly
VITE_API_BASE_URL=https://your-api.example.com npm run dev
```

### 5. Tesseract (optional, for PNG/JPG OCR)

```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract
```

Prefer PDF / DOCX / Markdown if OCR is not installed.

## Public access with ngrok (one tunnel)

Free ngrok allows **one** public endpoint. Tunnel the **frontend** only; keep the backend on localhost and use the Vite `/api` proxy.

```bash
# terminals: Qdrant + uvicorn :8000 + npm run dev :5173
ngrok http 5173
```

Open the ngrok HTTPS URL. Requests go:

`browser → ngrok → Vite (:5173) → proxy /api → FastAPI (:8000)`

CORS already allows `*.ngrok-free.dev` / `*.ngrok.dev`. You can also set:

```bash
ALLOWED_ORIGINS=http://localhost:5173,https://your-frontend.ngrok-free.dev
```

in `backend/.env` if you want an explicit allowlist.

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Basic health |
| `/health` | GET | Detailed health (Qdrant, LiteLLM, LangSmith) |
| `/upload` | POST | Upload files (PDF, DOCX, MD, PNG, JPG) |
| `/summary/{job_id}` | GET | Product summary for a job |
| `/chat` | POST | RAG chat with document context |
| `/search` | GET | Vector search |
| `/job/{job_id}/status` | GET | Processing status |

## Environment Variables

Set these in **`backend/.env`** (see `.env.example`):

| Variable | Description |
|----------|-------------|
| `LITE_LLM_KEY` | KeyValue LiteLLM API key |
| `QDRANT_URL` | Qdrant URL (`http://localhost:6333` or Cloud URL) |
| `QDRANT_API_KEY` | Required for Qdrant Cloud |
| `ALLOWED_ORIGINS` | Comma-separated frontend origins (optional; ngrok regex also applies) |
| `LANGCHAIN_API_KEY` | LangSmith API key (optional) |
| `LANGCHAIN_TRACING_V2` | `true` / `false` |
| `LANGCHAIN_PROJECT` | LangSmith project name |

Frontend (optional):

| Variable | Description |
|----------|-------------|
| `VITE_API_BASE_URL` | Override API base; default is `/api` (Vite proxy) |

## Features

- Drag-and-drop upload for PRDs and related docs
- Text extraction from PDF, DOCX, Markdown, and images (OCR)
- LangGraph pipeline: extract → chunk → embed → Qdrant → summary
- RAG chat grounded in uploaded documents
- Upload progress and job status polling

## Notes

- Job state is **in-memory**; it resets when the backend restarts.
- Uploads and local Qdrant data are gitignored — do not commit `.env`, `.venv`, `uploads/`, or `qdrant_storage/`.

## License

MIT
