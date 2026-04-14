# RAG System — Frontend

React frontend for the Production RAG System.

## Setup

```bash
npm install
npm run dev       # starts on http://localhost:3000
```

Vite proxies `/api/*` → `http://localhost:8000` automatically.
No CORS config needed in dev.

## Production build

```bash
npm run build     # outputs to dist/
```

Serve `dist/` with any static host, or add FastAPI to serve it:

```python
# In app/main.py
from fastapi.staticfiles import StaticFiles
app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="frontend")
```

## Pages

| Page | Route | What it does |
|------|-------|-------------|
| Query | `/` | Ask questions, see pipeline steps, citations, traces |
| Documents | `/documents` | Upload PDFs, view indexed docs, delete |
| Evaluation | `/eval` | RAGAS scores, CI gate status |
| Traces | `/traces` | Per-request latency, tokens, cost history |

## Backend endpoints used

| Method | Path | File |
|--------|------|------|
| GET | `/health` | `app/main.py` |
| POST | `/upload` | `app/routers/upload.py` |
| POST | `/query` | `app/routers/query.py` |
| GET | `/documents` | `app/routers/documents.py` |
| DELETE | `/documents/{id}` | `app/routers/documents.py` |
| GET | `/eval/latest` | Add to `app/main.py` — see BACKEND_ADDITIONS.md |
