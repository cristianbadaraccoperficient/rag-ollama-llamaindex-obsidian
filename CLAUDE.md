# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # then set OBSIDIAN_VAULT_PATH
```

Ollama must be running with both models pulled:
```bash
ollama pull llama3.2
ollama pull nomic-embed-text
```

## Commands

```bash
# Index the vault (first run or after notes change)
python ingest.py

# Query the index
python query.py "tu pregunta"

# Re-index from scratch (delete state and re-run)
rm -rf storage/
python ingest.py
```

## Architecture

The system has two entry points and three support modules:

**`ingest.py`** — reads the Obsidian vault, applies text transforms, and runs an `IngestionPipeline` that embeds and stores nodes in ChromaDB. Uses `DocstoreStrategy.UPSERTS_AND_DELETE` for incremental indexing: unchanged files are skipped (hash comparison), modified files are re-embedded, deleted files are removed from the vector store. State persists in `storage/docstore.json` and `storage/ingest_cache.json`.

**`query.py`** — reconstructs the index from the existing ChromaDB collection (`VectorStoreIndex.from_vector_store`) without re-reading any files, then runs a query engine with `ResponseMode.COMPACT`. Displays the answer and a source-note table via `rich`.

**`config.py`** — loaded at module level by both entry points. Reads `.env`, validates that the vault path exists and Ollama is reachable, and exposes three factory functions: `get_llm()`, `get_embed_model()`, `get_chroma_vector_store()`. All model/path constants live here.

**`obsidian_parser.py`** — pure Python, no LlamaIndex dependency. Handles three Obsidian-specific transforms applied before indexing:
- YAML frontmatter → extracted into `Document.metadata`, stripped from body
- `[[wikilinks]]` → resolved to plain text
- `#tags` → normalized to plain text

The transforms run post-load because `Document.text` is a read-only Pydantic v2 property — `ingest.py` rebuilds `Document` objects with the cleaned text rather than mutating them.

**Chunking pipeline (two stages):**
1. `MarkdownNodeParser` — splits on headings, preserves header hierarchy in node metadata
2. `SentenceSplitter(chunk_size=512, chunk_overlap=64)` — size-caps large nodes

Both LLM and embed model point to local Ollama. `Settings.llm` / `Settings.embed_model` are set at the top of each entry point — no OpenAI key is used anywhere.

## Storage layout (runtime, gitignored)

```
storage/
├── chroma_db/         # ChromaDB persistence (PersistentClient)
├── docstore.json      # SimpleDocumentStore — tracks doc hashes for incremental indexing
└── ingest_cache.json  # IngestionCache — node-level dedup cache
```

## Key .env variables

| Variable | Default | Notes |
|---|---|---|
| `OBSIDIAN_VAULT_PATH` | — | Required, no default |
| `OLLAMA_LLM_MODEL` | `llama3.2` | Generation model |
| `OLLAMA_EMBED_MODEL` | `nomic-embed-text` | Must be pulled separately |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | `512` / `64` | Affects retrieval precision |
| `TOP_K` | `5` | Number of source nodes returned |
