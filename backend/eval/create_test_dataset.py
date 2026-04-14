"""
Phase 6 - Step 1: Create Q&A Test Dataset
Generates a test dataset from your document corpus using an LLM.
Saves to eval/test_dataset.json for use in RAGAS evaluation.
"""

import json
import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from groq import Groq

load_dotenv()

DOCS_DIR = os.getenv("DOCS_DIR", "data/")          # folder with your source PDFs/txts
OUTPUT_PATH = "eval/test_dataset.json"
NUM_QA_PAIRS = int(os.getenv("NUM_QA_PAIRS", "20")) # how many Q&A pairs to generate


def load_documents(docs_dir: str) -> list:
    """Load documents from the data directory."""
    loader = DirectoryLoader(
        docs_dir,
        glob="**/*.pdf",
        loader_cls=PyPDFLoader,
        show_progress=True,
    )
    docs = loader.load()
    if not docs:
        # Fallback: try .txt files
        loader = DirectoryLoader(docs_dir, glob="**/*.txt")
        docs = loader.load()
    print(f"Loaded {len(docs)} document pages.")
    return docs


def chunk_documents(docs: list) -> list:
    """Split documents into evaluation-sized chunks."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
    )
    chunks = splitter.split_documents(docs)
    print(f"Created {len(chunks)} chunks.")
    return chunks


def generate_qa_pair(client: Groq, context: str) -> dict | None:
    """Ask Groq to generate a Q&A pair from a given context chunk."""
    prompt = f"""Given the following context, generate ONE clear question that can be answered 
directly from the context, and provide the correct answer.

Context:
{context}

Respond ONLY in this JSON format (no extra text):
{{
  "question": "...",
  "ground_truth": "..."
}}"""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=300,
        )
        text = response.choices[0].message.content.strip()
        # Strip markdown fences if present
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text.strip())
    except Exception as e:
        print(f"  [SKIP] Failed to generate Q&A: {e}")
        return None


def create_dataset(docs_dir: str = DOCS_DIR, num_pairs: int = NUM_QA_PAIRS) -> list:
    """Main function: load docs → chunk → generate Q&A pairs → save."""
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    docs = load_documents(docs_dir)
    if not docs:
        raise FileNotFoundError(
            f"No documents found in '{docs_dir}'. "
            "Set DOCS_DIR env var or add PDFs/TXTs to that folder."
        )

    chunks = chunk_documents(docs)

    # Sample evenly across the corpus
    step = max(1, len(chunks) // num_pairs)
    sampled = chunks[::step][:num_pairs]

    dataset = []
    print(f"\nGenerating {len(sampled)} Q&A pairs...")
    for i, chunk in enumerate(sampled):
        print(f"  [{i+1}/{len(sampled)}] ", end="", flush=True)
        qa = generate_qa_pair(client, chunk.page_content)
        if qa:
            qa["context"] = chunk.page_content
            qa["source"] = chunk.metadata.get("source", "unknown")
            dataset.append(qa)
            print("✓")

    # Save
    Path(OUTPUT_PATH).parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(dataset, f, indent=2)

    print(f"\nSaved {len(dataset)} Q&A pairs → {OUTPUT_PATH}")
    return dataset


if __name__ == "__main__":
    create_dataset()
