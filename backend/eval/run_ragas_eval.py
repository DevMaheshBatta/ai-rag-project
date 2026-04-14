"""
Phase 6 - Step 2: RAGAS Evaluation Pipeline (Groq + HuggingFace Embeddings)

Fixes applied:
  - Removed `from ragas.metrics.collections import ...` (wrong module path)
  - Use Faithfulness(), AnswerRelevancy() instances — NOT modules
  - Removed deprecated LangchainLLMWrapper / LangchainEmbeddingsWrapper
  - Use EvaluationDataset instead of HuggingFace Dataset
  - get_rag_chain() now imports answer_question (not generate_answer)
  - Removed duplicate HuggingFaceEmbeddings import

Usage:
    python eval/run_ragas_eval.py
    python eval/run_ragas_eval.py --threshold 0.7
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

# ── Modern RAGAS imports (v0.2+) ──────────────────────────────────────────────
from ragas import evaluate, EvaluationDataset
from ragas.metrics import Faithfulness, AnswerRelevancy
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper

# ── LLM + Embeddings ──────────────────────────────────────────────────────────
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings

load_dotenv()

DEFAULT_THRESHOLD = float(os.getenv("RAGAS_THRESHOLD", "0.70"))
RESULTS_DIR = Path("eval/results")


# ─────────────────────────────────────────────────────────────────────────────
# 1.  Groq LLM judge + HuggingFace embeddings
# ─────────────────────────────────────────────────────────────────────────────
def get_judge():
    """
    Returns (ragas_llm, ragas_embeddings).
    - LLM judge : Groq  llama-3.1-8b-instant
    - Embeddings: HuggingFace all-MiniLM-L6-v2  (free, local)
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "GROQ_API_KEY not set. Add it to your .env file."
        )

    lc_llm = ChatGroq(
        model="llama-3.1-8b-instant",
        api_key=api_key,
        temperature=0,
        max_retries=2,
    )

    lc_emb = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    # LangchainLLMWrapper / LangchainEmbeddingsWrapper are still present in
    # recent RAGAS builds — use them here since llm_factory doesn't support
    # Groq natively yet.
    return LangchainLLMWrapper(lc_llm), LangchainEmbeddingsWrapper(lc_emb)


# ─────────────────────────────────────────────────────────────────────────────
# 2.  Load your RAG pipeline
# ─────────────────────────────────────────────────────────────────────────────
def get_rag_chain():
    """
    Imports answer_question() from app/rag.py.
    That function must return: {"answer": str, "contexts": list[str]}
    """
    try:
        project_root = str(Path(__file__).resolve().parent.parent)
        if project_root not in sys.path:
            sys.path.insert(0, project_root)

        from app.rag import answer_question          # ✅ correct function name
        print("[OK] Loaded RAG pipeline from app/rag.py → answer_question()")
        return answer_question

    except ImportError as e:
        print(f"\n[WARN] Could not import app.rag: {e}")
        print("       Running with STUB answers — scores will be meaningless.\n")

        def stub(question: str) -> dict:
            return {
                "answer": f"Stub answer for: {question}",
                "contexts": ["Placeholder context for testing."],
            }
        return stub


# ─────────────────────────────────────────────────────────────────────────────
# 3.  Run RAG over every question in the dataset
# ─────────────────────────────────────────────────────────────────────────────
def run_rag_on_dataset(dataset: list, answer_fn) -> list:
    """
    Returns a list of sample dicts in RAGAS EvaluationDataset format:
      user_input / response / retrieved_contexts / reference
    """
    samples = []
    print(f"\nRunning RAG pipeline on {len(dataset)} questions...")

    for i, item in enumerate(dataset):
        print(f"  [{i+1}/{len(dataset)}] {item['question'][:72]}...")
        try:
            result = answer_fn(item["question"])
            samples.append({
                "user_input":         item["question"],
                "response":           result["answer"],
                "retrieved_contexts": result["contexts"],   # list[str]
                "reference":          item["ground_truth"],
            })
        except Exception as e:
            print(f"    [ERROR] {e} — skipping")

    return samples


# ─────────────────────────────────────────────────────────────────────────────
# 4.  RAGAS evaluation — metric INSTANCES, not modules
# ─────────────────────────────────────────────────────────────────────────────
def evaluate_with_ragas(samples: list) -> dict:
    """
    KEY FIX: Faithfulness() and AnswerRelevancy() must be instantiated.
    Calling the imported module directly → TypeError: 'module' not callable.
    """
    ragas_llm, ragas_emb = get_judge()

    # ✅ Instantiate — do NOT call the module itself
    faithfulness_metric = Faithfulness(llm=ragas_llm)
    relevancy_metric    = AnswerRelevancy(llm=ragas_llm, embeddings=ragas_emb)

    eval_dataset = EvaluationDataset.from_list(samples)

    print("\nRunning RAGAS evaluation (Groq judge + HF embeddings)...")
    result = evaluate(
        dataset=eval_dataset,
        metrics=[faithfulness_metric, relevancy_metric],
    )

    df = result.to_pandas()
    return {
        "faithfulness":     float(df["faithfulness"].mean()),
        "answer_relevancy": float(df["answer_relevancy"].mean()),
    }


# ─────────────────────────────────────────────────────────────────────────────
# 5.  Save results
# ─────────────────────────────────────────────────────────────────────────────
def save_results(scores: dict, samples: list, dataset_path: str) -> Path:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    out_path  = RESULTS_DIR / f"ragas_{timestamp}.json"

    with open(out_path, "w") as f:
        json.dump({
            "timestamp":   timestamp,
            "dataset":     dataset_path,
            "scores":      scores,
            "num_samples": len(samples),
            "samples":     samples,
        }, f, indent=2)

    latest = RESULTS_DIR / "latest.json"
    with open(latest, "w") as f:
        json.dump({"timestamp": timestamp, "scores": scores}, f, indent=2)

    print(f"\nResults  → {out_path}")
    print(f"Latest   → {latest}")
    return out_path


def print_summary(scores: dict, threshold: float) -> bool:
    print("\n" + "=" * 52)
    print("         RAGAS EVALUATION SUMMARY")
    print("=" * 52)
    passed = True
    for metric, score in scores.items():
        status = "✅ PASS" if score >= threshold else "❌ FAIL"
        if score < threshold:
            passed = False
        print(f"  {metric:<26} {score:.4f}   {status}")
    print(f"\n  Threshold : {threshold}   Judge: Groq llama-3.1-8b-instant")
    print("=" * 52)
    print("  🎉 All metrics PASSED" if passed else "  🚨 One or more metrics FAILED")
    print("=" * 52 + "\n")
    return passed


# ─────────────────────────────────────────────────────────────────────────────
# 6.  Entry point
# ─────────────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="RAGAS eval — Groq judge.")
    parser.add_argument("--dataset",   default="eval/test_dataset.json")
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    parser.add_argument("--no-fail",   action="store_true")
    args = parser.parse_args()

    if not Path(args.dataset).exists():
        print(f"[ERROR] Dataset not found: {args.dataset}")
        print("Run `python eval/create_test_dataset.py` first.")
        sys.exit(1)

    with open(args.dataset) as f:
        dataset = json.load(f)
    print(f"Loaded {len(dataset)} Q&A pairs from {args.dataset}")

    answer_fn = get_rag_chain()
    samples   = run_rag_on_dataset(dataset, answer_fn)

    if not samples:
        print("[ERROR] No questions processed.")
        sys.exit(1)

    scores = evaluate_with_ragas(samples)
    save_results(scores, samples, args.dataset)
    passed = print_summary(scores, args.threshold)

    if not passed and not args.no_fail:
        sys.exit(1)


if __name__ == "__main__":
    main()
