"""
app/routers/upload.py

POST /upload  — accept one or more PDFs, chunk + embed + index into ChromaDB
"""

import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import List

from app.state import rag_state
from app.rag import load_documents, chunk_documents

router = APIRouter()

UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post(
    "/",
    summary="Upload and index PDF documents",
)
async def upload_files(files: List[UploadFile] = File(...)):
    """
    For each uploaded PDF:
      1. Save to disk (data/uploads/)
      2. Load pages with PyPDFLoader
      3. Chunk with RecursiveCharacterTextSplitter
      4. Embed + store in ChromaDB via rag_state
    """
    if not files:
        raise HTTPException(400, "No files provided.")

    results = []

    for upload in files:
        # ── Validate ──────────────────────────────────────────────────────────
        if not upload.filename.lower().endswith(".pdf"):
            results.append({
                "filename": upload.filename,
                "status":   "skipped",
                "reason":   "Only PDF files are supported",
            })
            continue

        # ── Save to disk ──────────────────────────────────────────────────────
        # Use a UUID prefix so re-uploads of the same file don't collide
        doc_id   = str(uuid.uuid4())[:8]
        safe_name = f"{doc_id}_{upload.filename}"
        save_path = UPLOAD_DIR / safe_name

        try:
            with open(save_path, "wb") as f:
                shutil.copyfileobj(upload.file, f)
        except Exception as e:
            results.append({
                "filename": upload.filename,
                "status":   "error",
                "reason":   f"Could not save file: {e}",
            })
            continue

        # ── Load + chunk ──────────────────────────────────────────────────────
        try:
            docs   = load_documents(str(save_path))
            chunks = chunk_documents(docs)
        except Exception as e:
            save_path.unlink(missing_ok=True)
            results.append({
                "filename": upload.filename,
                "status":   "error",
                "reason":   f"Could not parse PDF: {e}",
            })
            continue

        if not chunks:
            save_path.unlink(missing_ok=True)
            results.append({
                "filename": upload.filename,
                "status":   "error",
                "reason":   "PDF appears to be empty or unreadable",
            })
            continue

        # ── Index into ChromaDB via rag_state ─────────────────────────────────
        try:
            rag_state.add_documents(
                doc_id   = doc_id,
                filename = upload.filename,
                path     = str(save_path),
                chunks   = chunks,
            )
        except Exception as e:
            save_path.unlink(missing_ok=True)
            results.append({
                "filename": upload.filename,
                "status":   "error",
                "reason":   f"Indexing failed: {e}",
            })
            continue

        results.append({
            "doc_id":   doc_id,
            "filename": upload.filename,
            "pages":    len(docs),
            "chunks":   len(chunks),
            "status":   "indexed",
        })

    # Return 400 only if EVERY file failed
    all_failed = all(r["status"] != "indexed" for r in results)
    if all_failed:
        raise HTTPException(400, detail=results)

    return {
        "uploaded": len([r for r in results if r["status"] == "indexed"]),
        "results":  results,
    }
