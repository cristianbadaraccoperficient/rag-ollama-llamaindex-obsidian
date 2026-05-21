import os
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv()

OBSIDIAN_VAULT_PATH = Path(os.environ["OBSIDIAN_VAULT_PATH"])
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_LLM_MODEL = os.getenv("OLLAMA_LLM_MODEL", "llama3.2:1b")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "256"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "32"))
TOP_K = int(os.getenv("TOP_K", "3"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "256"))

STORAGE_DIR = Path(os.getenv("STORAGE_DIR", "./storage"))
CHROMA_DB_PATH = STORAGE_DIR / "chroma_db"
DOCSTORE_PATH = STORAGE_DIR / "docstore.json"
CACHE_PATH = STORAGE_DIR / "ingest_cache.json"
CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION", "obsidian_vault")


def validate(create_dirs: bool = True):
    if not OBSIDIAN_VAULT_PATH.exists():
        raise FileNotFoundError(f"Vault not found: {OBSIDIAN_VAULT_PATH}")
    try:
        httpx.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
    except Exception:
        raise RuntimeError(f"Ollama not reachable at {OLLAMA_BASE_URL}. Run: ollama serve")
    if create_dirs:
        STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        CHROMA_DB_PATH.mkdir(parents=True, exist_ok=True)


def get_llm():
    from llama_index.llms.ollama import Ollama
    return Ollama(
        model=OLLAMA_LLM_MODEL,
        base_url=OLLAMA_BASE_URL,
        request_timeout=600.0,
        context_window=8192,
        num_predict=LLM_MAX_TOKENS,
    )


def get_embed_model():
    from llama_index.embeddings.ollama import OllamaEmbedding
    return OllamaEmbedding(
        model_name=OLLAMA_EMBED_MODEL,
        base_url=OLLAMA_BASE_URL,
    )


def get_chroma_vector_store(readonly: bool = False):
    import chromadb
    from llama_index.vector_stores.chroma import ChromaVectorStore
    client = chromadb.PersistentClient(path=str(CHROMA_DB_PATH))
    if readonly:
        collection = client.get_collection(CHROMA_COLLECTION)
    else:
        collection = client.get_or_create_collection(CHROMA_COLLECTION)
    return ChromaVectorStore(chroma_collection=collection)
