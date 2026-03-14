"""
AEDI Workflow — Configuration & Client Setup
Loads environment variables and initializes Supabase + LangChain clients.
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

# Load .env from parent backend directory
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"), override=True)

# ── Environment Variables ────────────────────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
N8N_CLOUD_URL = os.getenv("n8n_cloud_key")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY not set in .env")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL / SUPABASE_KEY not set in .env")

# ── Supabase Client ──────────────────────────────────────────────────────────
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ── LangChain LLM (structured output via with_structured_output) ─────────────
llm = ChatOpenAI(
    model=OPENAI_MODEL,
    temperature=0.2,
    api_key=OPENAI_API_KEY,
    max_tokens=4096,
)

# ── Embeddings for pgvector RAG queries ──────────────────────────────────────
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    api_key=OPENAI_API_KEY,
)
