"""
app/rag.py

Core RAG logic — used by:
  • app/routers/query.py   (FastAPI, uses shared rag_state)
  • eval/run_ragas_eval.py (RAGAS evaluation, uses answer_question())

CITATION_SYSTEM_PROMPT and build_context() are imported by the query router.
answer_question() is the standalone entry point for eval / testing.
"""

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
       # ✅ fixed deprecation
from langchain_community.vectorstores import Chroma
from groq import Groq
import os
from dotenv import load_dotenv
from langchain_community.embeddings import FastEmbedEmbeddings
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")


# ── Document helpers ──────────────────────────────────────────────────────────
def load_documents(file_path: str):
    return PyPDFLoader(file_path).load()


def chunk_documents(documents: list):
    return RecursiveCharacterTextSplitter(
        chunk_size=800, chunk_overlap=100
    ).split_documents(documents)




def create_embeddings():
    return FastEmbedEmbeddings(model_name="BAAI/bge-small-en-v1.5")

def create_vector_store(chunks: list, embeddings, persist_dir: str = "db"):
    if os.path.exists(persist_dir) and os.listdir(persist_dir):
        print("Loading existing ChromaDB ⚡")
        return Chroma(persist_directory=persist_dir, embedding_function=embeddings)
    if not chunks:
        # Empty init — no documents yet
        return Chroma(persist_directory=persist_dir, embedding_function=embeddings)
    print("Creating new ChromaDB 🔨")
    return Chroma.from_documents(
        documents=chunks, embedding=embeddings, persist_directory=persist_dir
    )


def get_retriever(vector_db, k: int = 5):
    return vector_db.as_retriever(search_kwargs={"k": k})


def get_llm():
    return Groq(api_key=GROQ_API_KEY)


# ── Phase 4: Citation Enforcement ─────────────────────────────────────────────
CITATION_SYSTEM_PROMPT = """You are a precise document assistant. You follow these rules without exception:

RULE 1 — GROUNDING:
  You MUST answer ONLY using the provided context.
  If ANY part of your answer is not directly supported by the context, return:
  "The provided documents do not contain enough information to answer this question."
  Do NOT infer. Do NOT use prior knowledge. Never guess.
  You MUST copy exact phrases from the context.
  Do NOT paraphrase. Do NOT reword. Do NOT add any new words.

RULE 2 — CITATIONS:
  Every factual claim MUST end with its source number in square brackets, e.g. [1] or [2].
  If a claim is supported by multiple sources, list all: [1][3].
  No claim is allowed without a citation.

RULE 3 — UNANSWERABLE:
  If the context does not contain enough information, respond with EXACTLY:
  "The provided documents do not contain enough information to answer this question."
  Do not add anything else. Do not apologise. Do not guess.

RULE 4 — NO FABRICATION:
  Do not rephrase or combine information in a way that changes its meaning.
  Quote directly when precision matters.

RULE 5 — FORMAT:
  Write your answer as plain prose with inline citations.
  Then add a "Sources:" section at the end listing:
    [number]: <filename>, page <page>
  Only list sources you actually cited."""


def build_context(docs: list) -> str:
    """Build a numbered context block from retrieved Document chunks."""
    parts = []
    for i, doc in enumerate(docs):
        source = doc.metadata.get("source", "unknown")
        page   = doc.metadata.get("page", "?")
        parts.append(f"[{i+1}] Source: {source} | Page: {page}\n{doc.page_content}")
    return "\n\n---\n\n".join(parts)


def generate_answer(query: str, retriever, llm) -> dict:
    """
    Core RAG step: retrieve → build context → generate cited answer.
    Called by answer_question() (eval) and directly by the query router (API).
    """
    docs     = retriever.invoke(query)
    docs     = [d for d in docs if len(d.page_content.strip()) > 50][:3]
    context  = build_context(docs)

    response = llm.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": CITATION_SYSTEM_PROMPT},
            {"role": "user",   "content": f"Context:\n{context}\n\nQuestion: {query}"},
        ],
        temperature=0.0,
    )
    usage = response.usage

    return {
        "answer":            response.choices[0].message.content,
        "contexts":          [d.page_content for d in docs],
        "prompt_tokens":     usage.prompt_tokens,
        "completion_tokens": usage.completion_tokens,
        "total_tokens":      usage.total_tokens,
        "sources": [
            {
                "index":        i + 1,
                "source":       d.metadata.get("source", "unknown"),
                "page":         d.metadata.get("page", "?"),
                "rerank_score": d.metadata.get("rerank_score", "n/a"),
                "snippet":      d.page_content[:200],
            }
            for i, d in enumerate(docs)
        ],
    }


# ── Lazy singleton (used by eval / standalone runs only) ──────────────────────
# The FastAPI app uses rag_state (app/state.py) instead.
_retriever = None
_llm       = None


def _init_pipeline(pdf_path: str = "data/sample.pdf", persist_dir: str = "db"):
    global _retriever, _llm
    if _retriever is not None:
        return
    pdf_path   = os.getenv("RAG_PDF_PATH", pdf_path)
    print(f"[RAG] Initialising from: {pdf_path}")
    docs       = load_documents(pdf_path)
    chunks     = chunk_documents(docs)
    embeddings = create_embeddings()
    vector_db  = create_vector_store(chunks, embeddings, persist_dir)
    _retriever = get_retriever(vector_db)
    _llm       = get_llm()
    print("[RAG] Pipeline ready ✅")


def answer_question(query: str) -> dict:
    """
    Standalone entry point for RAGAS eval and testing.
    The FastAPI query router does NOT call this — it uses rag_state directly.

    Returns: {"answer": str, "contexts": list[str]}
    """
    _init_pipeline()
    result = generate_answer(query, _retriever, _llm)
    return {"answer": result["answer"], "contexts": result["contexts"]}


