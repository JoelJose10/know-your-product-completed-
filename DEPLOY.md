# Polylane Free-Tier Demo Deploy Guide

Deploy a demo copy of Know Your Product on **free tiers only**, then connect Polylane.

Use branch **`polylane-demo`**. Do not put KeyValue `LITE_LLM_KEY` (or company VPN-only credentials) on Render.

## Free accounts (Milestone 0)

| Service | Signup | What you need |
|---------|--------|----------------|
| [Render](https://render.com) | Free workspace | GitHub connected; later API key `rnd_…` for Polylane |
| [Qdrant Cloud](https://cloud.qdrant.io) | Free cluster (no card) | Cluster URL + API key |
| [LangSmith](https://smith.langchain.com) | Developer ($0 / 5k traces) | API key; stay under free quota |
| [Polylane](https://console.polylane.com/signup) | Free forever | Connect GitHub + Render + LangSmith after deploy |
| OpenAI | Personal key | `OPENAI_API_KEY` (usage-based; keep demo traffic light) |

## Free-tier caveats

- **Render web service** sleeps after ~15 minutes idle and cold-starts in ~1 minute. Job state and uploaded files on disk are lost on sleep/restart (in-memory job store).
- **No persistent disk** on free web services — uploads are ephemeral.
- **Tesseract OCR** is usually **not** installed on Render’s Python runtime. Prefer **PDF / DOCX / Markdown** for demo uploads (skip PNG/JPG OCR).
- **Qdrant free** clusters suspend after ~1 week idle; wake them before a demo.
- **LangSmith** Developer includes ~5k traces/month — avoid attaching a payment method if you want zero risk of overage charges.

## 1. Push and open the Blueprint

```bash
git push -u origin polylane-demo
```

1. Open [Render Dashboard](https://dashboard.render.com) → **New** → **Blueprint**.
2. Connect the GitHub repo and select branch **`polylane-demo`**.
3. Confirm services from [`render.yaml`](render.yaml):
   - `know-your-product-api` (Free web service)
   - `know-your-product-web` (static site)

## 2. Backend environment variables

Set these on **know-your-product-api** (Blueprint will prompt for `sync: false` keys):

| Variable | Value |
|----------|--------|
| `OPENAI_API_KEY` | Your personal OpenAI key |
| `OPENAI_BASE_URL` | Leave **empty** for api.openai.com |
| `QDRANT_URL` | Qdrant Cloud cluster URL |
| `QDRANT_API_KEY` | Qdrant Cloud API key |
| `ALLOWED_ORIGINS` | Static site origin, e.g. `https://know-your-product-web.onrender.com` (update after first static deploy if the hostname differs) |
| `LANGCHAIN_API_KEY` | LangSmith API key |
| `LANGCHAIN_TRACING_V2` | `true` |
| `LANGCHAIN_PROJECT` | `know-your-product-polylane-demo` |
| `DEMO_FORCE_CHAT_ERROR` | `false` until the controlled-failure step |

`VITE_API_BASE_URL` for the static site is wired from the API service’s `RENDER_EXTERNAL_URL` in the Blueprint. After the API URL is known, trigger a **manual static-site rebuild** if the first frontend build ran before the API existed.

## 3. Smoke test

1. Wait for both services to show **Live**.
2. Open `https://<api>.onrender.com/health` — expect `"status": "healthy"` and `"openai": "configured"`.
3. Open the static site URL, upload a small PDF/MD, wait for summary, ask a chat question.
4. Confirm a trace appears in LangSmith for the project above.

If the first request after idle hangs, wait ~60s for cold start.

## 4. Connect Polylane (Milestone 4)

Polylane Free allows **1 cloud account** — use Render as that connection.

1. Sign up at [console.polylane.com/signup](https://console.polylane.com/signup) (no card).
2. **GitHub**: connect the repo that contains `polylane-demo` ([Polylane + GitHub](https://docs.polylane.com/integrations/github)).
3. **Render**: create an API key under Render → Account Settings → API Keys (`rnd_…`), then connect in Polylane ([Polylane + Render](https://docs.polylane.com/integrations/render)) or CLI:
   ```bash
   polylane cloud connect --provider render
   ```
4. **LangSmith**: connect your LangSmith workspace so agents can see AI latency/errors ([Polylane + LangSmith](https://docs.polylane.com/integrations/langsmith)).
5. Wait for the first sync until the Render account status is **ready**. Confirm `know-your-product-api` and `know-your-product-web` appear in the topology.

## 5. Controlled failure for the live demo (Milestone 5)

Reversible fault is already in code: [`backend/app/api/chat.py`](backend/app/api/chat.py) checks `DEMO_FORCE_CHAT_ERROR`.

1. In Render → `know-your-product-api` → Environment, set `DEMO_FORCE_CHAT_ERROR=true` and save (triggers redeploy).
2. From the UI (or `curl`), call `/chat` — expect HTTP **500** with `Demo fault: forced /chat failure…`.
3. In Polylane, open an investigation / check service **logs** and **metrics** for the API service around that time.
4. **Revert**: set `DEMO_FORCE_CHAT_ERROR=false`, save, confirm `/chat` works again.

Optional alternate fault (no code change): temporarily set a bad `QDRANT_URL` to break upload/search, then restore the real URL.

## Local development on this branch

```bash
# backend/.env
OPENAI_API_KEY=...
# optional KV gateway locally only:
# OPENAI_BASE_URL=https://llm.keyvalue.systems
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
QDRANT_URL=...
```

Frontend defaults to `http://localhost:8000` when `VITE_API_BASE_URL` is unset.
