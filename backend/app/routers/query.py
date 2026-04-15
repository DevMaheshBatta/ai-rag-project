"""
app/routers/query.py

POST /query
  Body: {"question": "...", "k": 5}
  Returns: answer with citations + retrieved sources + token usage
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.state import rag_state
from app.rag import CITATION_SYSTEM_PROMPT, build_context

router = APIRouter()


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=3, example="What is the main topic of the document?")
    k:        int = Field(5, ge=1, le=20, description="Number of chunks to retrieve")


class Source(BaseModel):
    index:   int
    source:  str
    page:    int | str
    snippet: str


class QueryResponse(BaseModel):
    question:          str
    answer:            str
    sources:           list[Source]
    prompt_tokens:     int
    completion_tokens: int
    total_tokens:      int


@router.post(
    "/",
    summary="Ask a question",
    response_model=QueryResponse,
)
def ask_question(body: QueryRequest):
    if rag_state.document_count() == 0:
        raise HTTPException(400, "No documents indexed yet. Upload a PDF first via POST /upload.")

    # ── Retrieve ──────────────────────────────────────────────────────────────
    retriever = rag_state.get_retriever(k=body.k)
    docs      = retriever.invoke(body.question)
    docs      = [d for d in docs if len(d.page_content.strip()) > 50][:3]

    if not docs:
        raise HTTPException(404, "No relevant content found for this question.")

    # ── Generate ──────────────────────────────────────────────────────────────
    context  = build_context(docs)
    response = rag_state.llm.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": CITATION_SYSTEM_PROMPT},
            {"role": "user",   "content": f"Context:\n{context}\n\nQuestion: {body.question}"},
        ],
        temperature=0.0,
    )

    usage  = response.usage
    answer = response.choices[0].message.content

    sources = [
        Source(
            index   = i + 1,
            source  = d.metadata.get("source", "unknown"),
            page    = d.metadata.get("page", "?"),
            snippet = d.page_content[:200],
        )
        for i, d in enumerate(docs)
    ]

    return QueryResponse(
        question          = body.question,
        answer            = answer,
        sources           = sources,
        prompt_tokens     = usage.prompt_tokens,
        completion_tokens = usage.completion_tokens,
        total_tokens      = usage.total_tokens,
    )
