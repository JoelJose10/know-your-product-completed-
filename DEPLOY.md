# Deploy Know Your Product on Render (polylane-demo)

Branch: **`polylane-demo`**  
Repo: `JoelJose10/know-your-product-completed-`

Do **not** put KeyValue `LITE_LLM_KEY` on Render.

**LLM:** use **OpenRouter** (`OPENROUTER_API_KEY`).

## What this branch already includes

- OpenRouter via OpenAI-compatible client (`OPENAI_BASE_URL=https://openrouter.ai/api/v1`)
- CORS from `ALLOWED_ORIGINS` + `*.onrender.com` regex
- Frontend `VITE_API_BASE_URL` for the API URL
- [`render.yaml`](render.yaml) Blueprint (free API + static site)
- API image built from [`backend/Dockerfile`](backend/Dockerfile) with the `tesseract-ocr` OS package, so PNG/JPG screenshot OCR works

## Accounts / secrets you need

| Service | Free? | Values for Render |
|---------|-------|-------------------|
| [Render](https://render.com) | Yes | GitHub connected |
| [Qdrant Cloud](https://cloud.qdrant.io) | Yes | `QDRANT_URL`, `QDRANT_API_KEY` |
| [OpenRouter](https://openrouter.ai) | Credits on their side | `OPENROUTER_API_KEY` |
| [LangSmith](https://smith.langchain.com) | Developer free tier | `LANGCHAIN_API_KEY` (optional) |

## Deploy with Blueprint

1. Push is already on `origin/polylane-demo` (pull latest if needed).
2. [Render Dashboard](https://dashboard.render.com) → **New** → **Blueprint**.
3. Select repo **`know-your-product-completed-`**, branch **`polylane-demo`**.
4. Apply services:
   - `know-your-product-api` (Free web service, built from `backend/Dockerfile`)
   - `know-your-product-web` (static site)
5. When prompted, set backend env vars:

| Variable | Value |
|----------|--------|
| `OPENROUTER_API_KEY` | Your OpenRouter key |
| `OPENAI_BASE_URL` | `https://openrouter.ai/api/v1` |
| `CHAT_MODEL` | `openai/gpt-4o-mini` (or any OpenRouter chat model) |
| `EMBEDDING_MODEL` | `openai/text-embedding-3-small` |
| `QDRANT_URL` | Qdrant Cloud HTTPS URL |
| `QDRANT_API_KEY` | Qdrant Cloud API key |
| `ALLOWED_ORIGINS` | e.g. `https://know-your-product-web-b1pr.onrender.com` |
| `LANGCHAIN_API_KEY` | LangSmith key (optional) |

`VITE_API_BASE_URL` is wired from the API’s `RENDER_EXTERNAL_URL`. If the static site built before the API existed, **Manual Deploy** the static site once.

## Smoke test

1. `https://<api>.onrender.com/health` → `"llm": "openrouter"`, healthy.
2. Open the static site → upload **PDF/MD/DOCX**, then a **PNG/JPG screenshot** (the image runs OCR inside the Docker image).
3. Chat once; confirm a LangSmith trace under `know-your-product-polylane-demo`.

Free API sleeps after ~15 minutes idle (~1 minute cold start). Jobs/uploads reset on restart.

## Connect Polylane (after live)

Polylane Free = **1 cloud account** → use **Render**.

1. Polylane → connect **GitHub** (this repo).
2. Connect **Render** with API key `rnd_…` ([docs](https://docs.polylane.com/integrations/render)).
3. Keep **LangSmith** connected.
4. Confirm both services on the [topology](https://console.polylane.com/keyvalue/topology).

## Controlled failure (optional)

Set `DEMO_FORCE_CHAT_ERROR=true` on the API service, call `/chat`, let Polylane investigate Render logs, then set it back to `false`.
