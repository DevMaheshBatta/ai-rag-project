"""
app/routers/documents.py

GET    /documents          — list all indexed documents
DELETE /documents/{doc_id} — remove a document and all its chunks
"""

from pathlib import Path
from fastapi import APIRouter, HTTPException
from app.state import rag_state

router = APIRouter()


@router.get(
    "/",
    summary="List indexed documents",
)
def list_documents():
    """Returns all documents currently indexed in ChromaDB."""
    docs = rag_state.list_docs()
    return {
        "total":     len(docs),
        "documents": docs,
    }


@router.delete(
    "/{doc_id}",
    summary="Delete a document",
)
def delete_document(doc_id: str):
    """
    Removes all chunks belonging to this doc_id from ChromaDB
    and deletes the saved PDF from disk.
    """
    # Find doc metadata before removing
    docs = {d["id"]: d for d in rag_state.list_docs()}
    if doc_id not in docs:
        raise HTTPException(404, f"Document '{doc_id}' not found.")

    doc_info = docs[doc_id]

    # Remove from ChromaDB + state
    removed = rag_state.remove_doc(doc_id)
    if not removed:
        raise HTTPException(500, "Failed to remove document from index.")

    # Delete file from disk
    file_path = Path(doc_info.get("path", ""))
    if file_path.exists():
        file_path.unlink()

    return {
        "status":   "deleted",
        "doc_id":   doc_id,
        "filename": doc_info.get("filename"),
    }
