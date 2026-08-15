# Smit Teaching Agent

An AI coding instructor built to match the spec: a **Socratic chat tutor** that reviews code, rates it on readability/performance/security, hunts bugs, and stays on-topic via guardrails — with RAG over course material.

```
┌──────────────┐   SSE stream    ┌─────────────────────────────┐
│  Next.js UI  │ ──────────────► │        FastAPI backend      │
│  (chat +     │                 │  /api/chat    (streaming)   │
│   Code Lab)  │ ◄────────────── │  /api/code/* (rate/analyze/ │
└──────────────┘                 │              bugs)          │
                                 │  /api/ingest (RAG docs)     │
                                 └──────────┬──────────┬───────┘
                                            │          │
                                  ┌─────────┴──┐  ┌────┴─────┐
                                  │ ChromaDB   │  │ SQLite   │
                                  │ (RAG docs) │  │ (history)│
                                  └────────────┘  └──────────┘
```

- **Frontend**: Next.js 14 (App Router), Tailwind, `react-markdown` + `react-syntax-highlighter`
- **Backend**: FastAPI, LangChain OpenAI provider (with an offline `mock` provider for no-key development)
- **RAG**: ChromaDB (persistent, cosine) with a dependency-free hashing embedding — swap in OpenAI/sentence-transformers embeddings later
- **Guardrails**: lightweight topic filter + prompt-injection detector (drop-in compatible with NVIDIA NeMo Guardrails / Llama Guard)
- **History**: SQLite per-session chat log

---

## 1. Backend

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
Copy-Item .env.example .env        # defaults to mock LLM — no key needed
uvicorn app.main:app --reload --port 8000
```

Check it: `http://localhost:8000/health` and interactive docs at `http://localhost:8000/docs`.

### Use a real LLM (optional)

Two OpenAI-compatible options:

```env
# Option A — OpenAI
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini

# Option B — OpenCode Zen (or any OpenAI-compatible endpoint)
LLM_PROVIDER=opencode
OPENCODE_API_KEY=your_opencode_zen_free_key_here
OPENCODE_BASE_URL=https://api.opencode.zen/v1   # your exact endpoint
OPENCODE_MODEL=gpt-4o-mini                       # your model name
```

Requires the `openai` package (already in `requirements.txt`). `opencode` is treated as an OpenAI-compatible endpoint — streaming, `response_format: json_object`, and fallback parsing all work through the same provider. If the key is missing or still a placeholder, the app falls back to the `mock` provider.

### Ingest course material into RAG

```powershell
python -m scripts.ingest_docs "docs/**/*.md" "README.md"
```

Retrieved chunks are injected into the tutor's system prompt on every message.

---

## 2. Frontend

```powershell
cd frontend
npm install
Copy-Item .env.example .env.local
npm run dev
```

Open `http://localhost:3000`.

---

## 3. API reference

| Method | Endpoint             | Body                                          | Purpose                              |
| ------ | -------------------- | --------------------------------------------- | ------------------------------------ |
| POST   | `/api/chat`          | `{ session_id, messages[] }`                  | Streaming (SSE) Socratic tutor       |
| POST   | `/api/code/rate`     | `{ code }`                                    | 1–10 scores: readability/perf/security|
| POST   | `/api/code/analyze`  | `{ code }`                                    | Time & space complexity estimate     |
| POST   | `/api/code/bugs`     | `{ code }`                                    | Heuristic bug report (why + hint)    |
| POST   | `/api/code/deep-review` | `{ code, language }`                       | LLM review: semantic bugs, rating, socratic hint (no corrected code) |
| POST   | `/api/ingest`        | `{ documents[], source }`                     | Add documents to the vector store    |
| GET    | `/api/ingest/count`  | —                                             | Number of indexed documents          |
| GET    | `/api/history/{id}`  | —                                             | Chat history for a session           |

The `/api/code/*` analyzers are **pure heuristics** (no LLM), so they work instantly and offline.

---

## 4. Feature → spec mapping

| Spec requirement                      | Implementation |
| ------------------------------------- | -------------- |
| Socratic tutor, digestible steps      | `app/core/prompts.py` + `app/services/agent.py` |
| Academic integrity / scaffold mode    | `SCAFFOLD_PATTERN` in `app/services/agent.py` injects a refuse+skeleton+TODO directive |
| Beginner empathy → analogy → snippet  | `_infer_beginner` in `app/services/agent.py` injects a 3-step directive |
| Code complexity analysis              | `app/services/analyzer.py` → `estimate_complexity` |
| 1–10 rating (readability/perf/security)| `app/services/analyzer.py` → `rate_code` |
| Bug hunting with why/how              | `app/services/analyzer.py` → `find_bugs` + LLM `/api/code/deep-review` |
| Topic restriction + prompt injection   | `app/services/guardrails.py` (fixed jailbreak response) |
| RAG over course material              | `app/services/rag.py` + `/api/ingest` |
| Chat history / progress               | `app/services/history.py` (SQLite) |
| Streaming responses                   | SSE via `StreamingResponse` + Next.js reader |

---
 
## 5. Extending
 
- **Better embeddings**: replace `embed()` in `app/services/rag.py` with `OpenAIEmbeddings` or a local sentence-transformer; signature stays the same.
- **Stronger guardrails**: swap the `Guardrails` class for NeMo Guardrails / Llama Guard, keeping the `guard(text) -> dict` interface.
- **Auth**: add OAuth/JWT middleware on the FastAPI app and store user sessions.
- **Production frontend**: proxy `/api` in `next.config.mjs` and drop the permissive CORS.
 
---
 
## 6. Deploy to Vercel
 
### Frontend (Next.js) — Deploy to Vercel
 
The frontend is a standard Next.js 14 App Router application and deploys natively to Vercel.
 
1. Push this repository to GitHub/GitLab/Bitbucket.
2. Import the project in Vercel.
3. Set **Root Directory** to `frontend`.
4. Add Environment Variable:
   - `NEXT_PUBLIC_API_URL` = your deployed backend URL (e.g., `https://your-backend.railway.app`)
5. Deploy.
 
The `vercel.json` in `frontend/` configures the build. No additional setup needed.
 
### Backend (FastAPI) — Deploy Separately
 
The backend uses **ChromaDB** (persistent vector store) and **SQLite** (chat history), which require persistent file storage. Vercel's serverless functions are ephemeral and not suitable for this backend.
 
**Recommended platforms:**
- **Railway** — `railway up` (supports persistent volumes)
- **Render** — Web Service with persistent disk
- **Fly.io** — `fly deploy` with volume mounts
- **VPS** (DigitalOcean, Hetzner, etc.) — systemd + nginx
 
**Backend deployment checklist:**
1. Set environment variables (see `backend/.env.example`):
   - `LLM_PROVIDER` = `openai` | `opencode` | `mock`
   - `OPENAI_API_KEY` / `OPENCODE_API_KEY` (if using real LLM)
   - `CHROMA_PERSIST_DIR` = `/data/chroma` (persistent volume path)
   - `DB_PATH` = `/data/chat.db` (persistent volume path)
2. Run `python -m scripts.ingest_docs "docs/**/*.md" "README.md"` after deploy to populate RAG.
3. Ensure the backend URL is accessible publicly (no auth on `/health`, `/api/*`).
4. Update frontend's `NEXT_PUBLIC_API_URL` to the backend URL.
 
### Local Development with Deployed Backend
 
```bash
# Frontend
cd frontend
echo "NEXT_PUBLIC_API_URL=https://your-backend.railway.app" > .env.local
npm run dev
```
