from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
from pathlib import Path
from typing import List

from app.routers import upload, query, documents
from app.state import rag_state


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting RAG system...")
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, rag_state.startup)
    print("✅ RAG system ready")
    yield
    print("🛑 Shutting down...")


app = FastAPI(
    title="RAG Document API",
    description="Upload PDFs and query using RAG (Groq + ChromaDB)",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router, prefix="/upload", tags=["Upload"])
app.include_router(query.router, prefix="/query", tags=["Query"])
app.include_router(documents.router, prefix="/documents", tags=["Documents"])


@app.get("/health", tags=["Health"])
def health():
    return {
        "status": "ok",
        "indexed_docs": rag_state.document_count(),
    }


@app.post("/test-upload")
async def test_upload(files: List[UploadFile] = File(...)):
    return {"message": "working"}


@app.get("/eval/latest", tags=["Evaluation"])
def eval_latest():
    p = Path("eval/results/latest.json")
    if not p.exists():
        raise HTTPException(404, "No eval results yet. Run: python eval/run_ragas_eval.py")
    return json.loads(p.read_text())


if __name__ == "__main__":
    pass