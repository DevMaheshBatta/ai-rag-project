from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.routers import upload, query, documents
from app.state import rag_state
from fastapi import HTTPException
import json
from pathlib import Path

from fastapi import UploadFile, File
from typing import List

# ─────────────────────────────────────────
# Startup / Shutdown (Lifespan)
# ─────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting RAG system...")

    # Initialize vector DB, embeddings, retriever
    rag_state.startup()

    print("✅ RAG system ready")
    yield

    print("🛑 Shutting down...")


# ─────────────────────────────────────────
# FastAPI App
# ─────────────────────────────────────────
app = FastAPI(
    title="RAG Document API",
    description="Upload PDFs and query using RAG (Groq + ChromaDB)",
    version="1.0.0",
    lifespan=lifespan,
)


# ─────────────────────────────────────────
# CORS (for frontend later)
# ─────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────
# Routers
# ─────────────────────────────────────────
app.include_router(upload.router, prefix="/upload", tags=["Upload"])
app.include_router(query.router, prefix="/query", tags=["Query"])
app.include_router(documents.router, prefix="/documents", tags=["Documents"])


# ─────────────────────────────────────────
# Health Check
# ─────────────────────────────────────────
@app.get("/health", tags=["Health"])
def health():
    return {
        "status": "ok",
        "indexed_docs": rag_state.document_count()
    }


@app.post("/test-upload")
async def test_upload(files: List[UploadFile] = File(...)):
    return {"message": "working"}

@app.get("/eval/latest", tags=["Evaluation"])
def eval_latest():
    """
    Serves eval/results/latest.json — written by run_ragas_eval.py.
    The frontend EvalPage reads this to show RAGAS scores.
    """
    p = Path("eval/results/latest.json")
    if not p.exists():
        raise HTTPException(404, "No eval results yet. Run: python eval/run_ragas_eval.py")
    return json.loads(p.read_text())
 
# ─────────────────────────────────────────
# Run Server
# ─────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)