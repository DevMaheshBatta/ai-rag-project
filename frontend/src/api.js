/**
 * api.js — all calls to your FastAPI backend
 *
 * Base URL: /api  (Vite proxies this to http://localhost:8000 in dev)
 * In production set VITE_API_BASE in .env
 *
 * Your router structure:
 *   POST   /upload          — app/routers/upload.py
 *   POST   /query           — app/routers/query.py
 *   GET    /documents       — app/routers/documents.py
 *   DELETE /documents/{id}  — app/routers/documents.py
 *   GET    /health          — app/main.py
 *   GET    /eval/latest     — eval/run_ragas_eval.py results
 */

const BASE = import.meta.env.VITE_API_BASE ?? '/api'

async function request(method, path, body, isFormData = false) {
  const headers = isFormData ? {} : { 'Content-Type': 'application/json' }
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers,
    body: isFormData ? body : body ? JSON.stringify(body) : undefined,
  })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error(data.detail ?? `HTTP ${res.status}`)
  return data
}

// ── Health ────────────────────────────────────────────────────────────────────
export const getHealth = () => request('GET', '/health')

// ── Upload ────────────────────────────────────────────────────────────────────
export function uploadPDF(file) {
  const fd = new FormData()
  fd.append('file', file)
  return request('POST', '/upload', fd, true)
}

// ── Query ─────────────────────────────────────────────────────────────────────
// POST /query  body: { question: string }
// Returns: { answer, sources, trace: { run_id, latencies_ms, tokens, cost_usd } }
export const askQuestion = (question) =>
  request('POST', '/query', { question })

// ── Documents ─────────────────────────────────────────────────────────────────
// GET /documents  → [{ id, filename, pages, chunks, uploaded_at }]
export const getDocuments = () => request('GET', '/documents')

// DELETE /documents/{id}
export const deleteDocument = (id) => request('DELETE', `/documents/${id}`)

// ── RAGAS Eval results ────────────────────────────────────────────────────────
// GET /eval/latest  → { timestamp, scores: { faithfulness, answer_relevancy } }
// This reads eval/results/latest.json — add a simple endpoint in your FastAPI:
//
//   @app.get("/eval/latest")
//   def eval_latest():
//       p = Path("eval/results/latest.json")
//       if not p.exists(): raise HTTPException(404, "No eval results yet")
//       return json.loads(p.read_text())
//
export const getEvalResults = () => request('GET', '/eval/latest')
