"""
app/state.py — shared RAG state, initialised once on startup

Holds:
  - embeddings model  (loaded once, reused for all uploads)
  - vector_db         (ChromaDB, grows as docs are uploaded)
  - llm               (Groq client)
  - _doc_registry     (in-memory list of indexed docs for GET /documents)
"""

from langchain_chroma import Chroma          # pip install langchain-chroma
from app.rag import create_embeddings, get_llm


class RAGState:
    def __init__(self):
        self.embeddings  = None
        self.vector_db   = None
        self.llm         = None
        self._doc_registry: list[dict] = []  # [{id, filename, path, pages, chunks}]

    # ── Called once by FastAPI lifespan ───────────────────────────────────────
    def startup(self):
        print("🚀 Starting RAG system...")

        print("[RAG] Loading embedding model...")
        self.embeddings = create_embeddings()

        print("[RAG] Connecting to ChromaDB...")
        # persist_directory keeps data between restarts
        self.vector_db = Chroma(
            persist_directory  = "db",
            embedding_function = self.embeddings,
        )

        print("[RAG] Connecting to Groq...")
        self.llm = get_llm()

        count = self.vector_db._collection.count()
        print(f"[RAG] Ready — {count} chunks in store ✅")
        print("✅ RAG system ready")

    # ── Called by upload router ───────────────────────────────────────────────
    def add_documents(self, doc_id: str, filename: str, path: str, chunks: list):
        """
        Embed and store chunks in ChromaDB.
        Tags every chunk with doc_id so we can delete by doc later.
        """
        if self.vector_db is None:
            raise RuntimeError("RAGState not initialised — call startup() first.")

        # Attach doc_id to every chunk's metadata so we can find+delete them later
        for chunk in chunks:
            chunk.metadata["doc_id"]  = doc_id
            chunk.metadata["doc_name"] = filename

        self.vector_db.add_documents(chunks)

        # Register in memory so GET /documents can list it
        self._doc_registry.append({
            "id":       doc_id,
            "filename": filename,
            "path":     path,
            "pages":    len(set(c.metadata.get("page", 0) for c in chunks)),
            "chunks":   len(chunks),
        })

    # ── Called by documents router ────────────────────────────────────────────
    def list_docs(self) -> list[dict]:
        return list(self._doc_registry)

    def remove_doc(self, doc_id: str) -> bool:
        """Delete all chunks with this doc_id from ChromaDB and the registry."""
        try:
            # ChromaDB: delete by metadata filter
            self.vector_db._collection.delete(
                where={"doc_id": {"$eq": doc_id}}
            )
            self._doc_registry = [
                d for d in self._doc_registry if d["id"] != doc_id
            ]
            return True
        except Exception as e:
            print(f"[RAG] remove_doc error: {e}")
            return False

    # ── Called by query router ────────────────────────────────────────────────
    def document_count(self) -> int:
        return len(self._doc_registry)


# Singleton — imported by all routers
rag_state = RAGState()
