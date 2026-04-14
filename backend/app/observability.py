"""
observability.py — Phase 5: Tracing, latency, token usage, cost tracking

WHY a dedicated module instead of scattering logging in main.py:
Every production system separates observability from business logic.
This module owns all timing, cost, and tracing concerns so rag.py
and main.py stay clean and testable.

Two backends supported:
  1. LangSmith  — set LANGSMITH_API_KEY in .env (recommended, free tier)
  2. Local JSON  — always runs, even without LangSmith, writes to logs/traces.jsonl

WHY JSONL (JSON Lines) for local logs:
Each query appends one JSON object on its own line. The file never needs
to be loaded fully to read recent entries — just tail it. JSONL is also
directly ingestable by tools like DuckDB, BigQuery, and Pandas.
"""

import time
import json
import os
import uuid
from datetime import datetime, timezone
from contextlib import contextmanager
from dataclasses import dataclass, field, asdict
from typing import Optional

from app.config import (
    LANGSMITH_API_KEY,
    LANGSMITH_PROJECT,
    GROQ_COST_PER_1K_INPUT_TOKENS,
    GROQ_COST_PER_1K_OUTPUT_TOKENS,
)

# ── LangSmith setup ───────────────────────────────────────────────────────────
# LangSmith is optional. If the key is missing, tracing is skipped silently.
# WHY os.environ instead of passing to client: LangSmith's SDK reads these
# env vars automatically when you call langsmith.Client() anywhere.

_langsmith_enabled = False

if LANGSMITH_API_KEY:
    os.environ["LANGCHAIN_TRACING_V2"]  = "true"
    os.environ["LANGCHAIN_API_KEY"]     = LANGSMITH_API_KEY
    os.environ["LANGCHAIN_PROJECT"]     = LANGSMITH_PROJECT
    _langsmith_enabled = True
    print(f"  LangSmith tracing enabled → project: '{LANGSMITH_PROJECT}'")
else:
    print("  LangSmith not configured — local JSONL logging only")

# ── Local log file ────────────────────────────────────────────────────────────
LOG_DIR  = "logs"
LOG_FILE = os.path.join(LOG_DIR, "traces.jsonl")
os.makedirs(LOG_DIR, exist_ok=True)


# ─────────────────────────────────────────────────────────────────────────────
# Data structures
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class StepTrace:
    """Latency record for a single pipeline step."""
    name:       str
    latency_ms: float


@dataclass
class QueryTrace:
    """
    Complete trace for one user query through the RAG pipeline.

    WHY track per-step latency (not just total):
    In production you need to know WHICH step is slow.
    If p95 latency spikes, is it ChromaDB? Elasticsearch? Cohere? The LLM?
    Without per-step data you're flying blind.
    """
    trace_id:          str   = field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp:         str   = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    query:             str   = ""

    # Per-step latencies
    steps:             list  = field(default_factory=list)   # list of StepTrace

    # Token usage (from Groq response.usage)
    prompt_tokens:     int   = 0
    completion_tokens: int   = 0
    total_tokens:      int   = 0

    # Cost (calculated from token counts + pricing constants)
    cost_usd:          float = 0.0

    # Quality signals (populated after answer generated)
    answer_length:     int   = 0
    num_sources:       int   = 0
    rerank_scores:     list  = field(default_factory=list)

    # Computed totals
    total_latency_ms:  float = 0.0


# ─────────────────────────────────────────────────────────────────────────────
# Timer context manager
# ─────────────────────────────────────────────────────────────────────────────

@contextmanager
def timer(trace: QueryTrace, step_name: str):
    """
    Context manager that times a code block and records it on the trace.

    Usage:
        with timer(trace, "vector_retrieval"):
            docs = retriever.invoke(query)

    WHY a context manager: clean syntax, guaranteed timing even if the
    block raises an exception (finally block runs either way).
    """
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed_ms = (time.perf_counter() - start) * 1000
        trace.steps.append(StepTrace(name=step_name, latency_ms=round(elapsed_ms, 2)))


# ─────────────────────────────────────────────────────────────────────────────
# Cost calculation
# ─────────────────────────────────────────────────────────────────────────────

def calculate_cost(prompt_tokens: int, completion_tokens: int) -> float:
    """
    Compute USD cost from token counts.

    WHY track cost per query: in production a RAG system can easily cost
    $50–200/day if prompts are large. Per-query cost tracking lets you
    set budgets, alert on spikes, and optimise prompt length.
    """
    input_cost  = (prompt_tokens  / 1000) * GROQ_COST_PER_1K_INPUT_TOKENS
    output_cost = (completion_tokens / 1000) * GROQ_COST_PER_1K_OUTPUT_TOKENS
    return round(input_cost + output_cost, 6)


# ─────────────────────────────────────────────────────────────────────────────
# Finalise and log a trace
# ─────────────────────────────────────────────────────────────────────────────

def finalise_trace(trace: QueryTrace, result: dict) -> QueryTrace:
    """
    Populate remaining fields from the LLM result, then log to JSONL.
    Call this after generate_answer() returns.
    """
    trace.prompt_tokens     = result.get("prompt_tokens", 0)
    trace.completion_tokens = result.get("completion_tokens", 0)
    trace.total_tokens      = result.get("total_tokens", 0)
    trace.cost_usd          = calculate_cost(trace.prompt_tokens, trace.completion_tokens)
    trace.answer_length     = len(result.get("answer", ""))
    trace.num_sources       = len(result.get("sources", []))
    trace.rerank_scores     = [
        s.get("rerank_score", "n/a")
        for s in result.get("sources", [])
    ]
    trace.total_latency_ms  = round(
        sum(s.latency_ms for s in trace.steps), 2
    )

    _write_jsonl(trace)

    if _langsmith_enabled:
        _send_to_langsmith(trace, result)

    return trace


def _write_jsonl(trace: QueryTrace):
    """Append one JSON line to logs/traces.jsonl."""
    record = asdict(trace)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def _send_to_langsmith(trace: QueryTrace, result: dict):
    """
    Log a run to LangSmith manually.

    WHY manual logging instead of LangChain callbacks:
    We're using Groq directly (not a LangChain LLM wrapper), so
    automatic callback tracing doesn't fire. We use the LangSmith
    REST client directly to log the full run.

    WHY 'chain' run_type: our pipeline is a multi-step chain
    (retrieve → fuse → rerank → generate), not a single LLM call.
    """
    try:
        from langsmith import Client

        client = Client()
        client.create_run(
            name        = "rag_query",
            run_type    = "chain",
            project_name= LANGSMITH_PROJECT,
            inputs      = {"query": trace.query},
            outputs     = {
                "answer":  result.get("answer", ""),
                "sources": result.get("sources", []),
            },
            extra = {
                "latency_ms":   trace.total_latency_ms,
                "steps":        [asdict(s) for s in trace.steps],
                "tokens":       {
                    "prompt":     trace.prompt_tokens,
                    "completion": trace.completion_tokens,
                    "total":      trace.total_tokens,
                },
                "cost_usd":     trace.cost_usd,
            },
        )
    except Exception as e:
        # Never crash the main pipeline because observability failed
        print(f"  ⚠️  LangSmith logging failed (non-fatal): {e}")


# ─────────────────────────────────────────────────────────────────────────────
# Console display
# ─────────────────────────────────────────────────────────────────────────────

def print_trace_summary(trace: QueryTrace):
    """
    Print a human-readable observability summary after each query.
    This is what you'd show in a dev dashboard.
    """
    print(f"\n{'─'*60}")
    print(f"  📊 Observability Summary  [trace: {trace.trace_id}]")
    print(f"{'─'*60}")

    # Per-step latencies
    print(f"  Latency breakdown:")
    for step in trace.steps:
        bar_len  = int(step.latency_ms / 20)   # 1 char = 20ms
        bar      = "█" * min(bar_len, 40)
        print(f"    {step.name:<22} {step.latency_ms:>8.1f} ms  {bar}")
    print(f"    {'TOTAL':<22} {trace.total_latency_ms:>8.1f} ms")

    # Tokens + cost
    print(f"\n  Token usage:")
    print(f"    Prompt tokens:          {trace.prompt_tokens:>6}")
    print(f"    Completion tokens:      {trace.completion_tokens:>6}")
    print(f"    Total tokens:           {trace.total_tokens:>6}")
    print(f"    Estimated cost:         ${trace.cost_usd:.6f}")

    # Rerank scores
    if trace.rerank_scores:
        scores_str = "  ".join(
            f"[{i+1}] {s}" for i, s in enumerate(trace.rerank_scores)
        )
        print(f"\n  Rerank scores:  {scores_str}")

    if _langsmith_enabled:
        print(f"\n  LangSmith: https://smith.langchain.com/projects/{LANGSMITH_PROJECT}")

    print(f"{'─'*60}\n")
