from app.rag import get_llm, create_embeddings, create_vector_store, get_retriever

class RAGState:
    def __init__(self):
        self.embeddings = None
        self.vector_db  = None
        self.llm        = None
        self._doc_registry: list[dict] = []

    def startup(self):
        print("[RAG] Loading embeddings model...")
        self.embeddings = create_embeddings()
        print("[RAG] Connecting to ChromaDB...")
        self.vector_db = create_vector_store([], self.embeddings, persist_dir="db")
        print("[RAG] Connecting to Groq...")
        self.llm = get_llm()
        print("✅ RAG system ready")

    def get_retriever(self, k: int = 5):
        if self.vector_db is None:
            raise RuntimeError("RAGState not initialised.")
        return self.vector_db.as_retriever(search_kwargs={"k": k})

    def add_documents(self, doc_id: str, filename: str, path: str, chunks: list):
        if self.vector_db is None:
            raise RuntimeError("RAGState not initialised.")
        for chunk in chunks:
            chunk.metadata["doc_id"]   = doc_id
            chunk.metadata["doc_name"] = filename
        self.vector_db.add_documents(chunks)
        self._doc_registry.append({
            "id":       doc_id,
            "filename": filename,
            "path":     path,
            "pages":    len(set(c.metadata.get("page", 0) for c in chunks)),
            "chunks":   len(chunks),
        })

    def list_docs(self) -> list[dict]:
        return list(self._doc_registry)

    def remove_doc(self, doc_id: str) -> bool:
        try:
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

    def document_count(self) -> int:
        return len(self._doc_registry)


rag_state = RAGState()