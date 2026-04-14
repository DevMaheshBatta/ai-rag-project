from langchain_core.documents import Document
import cohere

# ─────────────────────────────────────────────
# PHASE 2 — Reciprocal Rank Fusion
# ─────────────────────────────────────────────

def reciprocal_rank_fusion(
    vector_docs: list[Document],
    bm25_docs: list[Document],
    k: int = 60,
    top_n: int = 20
) -> list[Document]:
    """
    Merge two ranked lists (vector + BM25) into one using RRF.

    HOW RRF WORKS:
    Each document gets a score for each list it appears in:
        score += 1 / (rank + k)
    where rank is its 0-based position in that list.

    WHY k=60: The RRF paper (Cormack et al. 2009) found k=60 works well
    across many retrieval tasks. It dampens the impact of very high ranks
    vs very low ranks, making fusion robust.

    WHY this beats simple concatenation:
    A doc ranked #1 in BM25 but missing from vector results still gets
    a strong score. A doc in both lists gets combined scores — a natural
    signal of high relevance.
    """
    scores: dict[str, float] = {}
    doc_map: dict[str, Document] = {}

    def _doc_id(doc: Document) -> str:
        source = doc.metadata.get("source", "")
        page = str(doc.metadata.get("page", ""))
        return f"{source}::p{page}::{doc.page_content[:80]}"

    for rank, doc in enumerate(vector_docs):
        doc_id = _doc_id(doc)
        scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (rank + k)
        doc_map[doc_id] = doc

    for rank, doc in enumerate(bm25_docs):
        doc_id = _doc_id(doc)
        scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (rank + k)
        doc_map[doc_id] = doc

    ranked_ids = sorted(scores, key=lambda x: scores[x], reverse=True)
    return [doc_map[doc_id] for doc_id in ranked_ids[:top_n]]


# ─────────────────────────────────────────────
# PHASE 3 — Cohere Reranking
# ─────────────────────────────────────────────

def rerank_documents(
    query: str,
    docs: list[Document],
    cohere_api_key: str,
    top_n: int = 5
) -> list[Document]:
    """
    Rerank a list of documents using Cohere's rerank API.

    WHY reranking after RRF:
    RRF is a heuristic — it trusts rank position from two retrievers.
    Cohere's reranker is a cross-encoder: it reads BOTH the query AND
    each document together, giving a much more accurate relevance score.

    WHY cross-encoder > bi-encoder for final ranking:
    - Bi-encoder (what ChromaDB uses): embeds query and doc SEPARATELY,
      then compares vectors. Fast but loses nuance.
    - Cross-encoder (Cohere rerank): sees query+doc together, captures
      exact phrase matches, negations, and context. Slower but far more
      accurate — that's why we only run it on top-20, not the whole index.

    Flow: top-20 from RRF → Cohere rerank → top-5 returned to LLM
    """
    co = cohere.Client(api_key=cohere_api_key)

    # Cohere expects plain strings, not Document objects
    passages = [doc.page_content for doc in docs]

    response = co.rerank(
        model="rerank-english-v3.0",   # latest Cohere rerank model
        query=query,
        documents=passages,
        top_n=top_n
    )

    # Map reranked results back to original Document objects
    # WHY: we need to preserve metadata (source, page) for citations
    reranked_docs = []
    for result in response.results:
        doc = docs[result.index]

        # Attach rerank score to metadata for observability (Phase 5)
        doc.metadata["rerank_score"] = round(result.relevance_score, 4)
        reranked_docs.append(doc)

    return reranked_docs
