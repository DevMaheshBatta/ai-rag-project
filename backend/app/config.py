import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY        = os.getenv("GROQ_API_KEY")
COHERE_API_KEY      = os.getenv("COHERE_API_KEY")
LANGSMITH_API_KEY   = os.getenv("LANGSMITH_API_KEY")
LANGSMITH_PROJECT   = os.getenv("LANGSMITH_PROJECT", "rag-system")

# ── Groq pricing for cost tracking (Phase 5) ──────────────────────────────────
# llama-3.1-8b-instant as of 2024. Update if you change models.
# Source: https://console.groq.com/docs/models
GROQ_COST_PER_1K_INPUT_TOKENS  = 0.00005   # $0.05 per 1M input tokens
GROQ_COST_PER_1K_OUTPUT_TOKENS = 0.00008   # $0.08 per 1M output tokens

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found. Check your .env file.")
if not COHERE_API_KEY:
    raise ValueError("COHERE_API_KEY not found. Check your .env file.")
# LangSmith is optional — observability degrades gracefully if not set
