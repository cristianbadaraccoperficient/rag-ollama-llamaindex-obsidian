# RAG Obsidian — Ollama + LlamaIndex + ChromaDB

A fully local RAG system that uses your Obsidian vault as a knowledge source. No API keys, no data in the cloud.

## Stack

| Role | Technology |
|---|---|
| LLM (generation) | [Ollama](https://ollama.com) — `llama3.2:1b` |
| Embeddings | Ollama — `nomic-embed-text` |
| RAG framework | [LlamaIndex](https://www.llamaindex.ai) |
| Vector store | [ChromaDB](https://www.trychroma.com) (local) |
| Data source | Obsidian vault (`.md` files) |

## Requirements

- Python 3.11+
- [Ollama](https://ollama.com/download) installed and running

## Installation

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Pull the models
ollama pull llama3.2:1b
ollama pull nomic-embed-text

# 3. Configure
cp .env.example .env
```

Edit `.env` and set your vault path:

```ini
OBSIDIAN_VAULT_PATH=C:\Users\your-user\Documents\my-vault
```

To find the path in Obsidian: **Settings → About → Vault path**.

## Usage

```bash
# Index the vault (first time or after changing notes)
python ingest.py

# Query
python query.py "What notes do I have about machine learning?"
```

The first indexing run may take several minutes depending on vault size. Subsequent runs are incremental: only new or modified notes are re-indexed.

## How it works

**Ingest (`ingest.py`)**

1. Reads all `.md` files from the vault recursively
2. Cleans the text: extracts YAML frontmatter as metadata, converts `[[wikilinks]]` to plain text, normalizes `#tags`
3. Splits each note into chunks using `MarkdownNodeParser` (by headings) + `SentenceSplitter` (512 tokens, overlap 64)
4. Generates embeddings with `nomic-embed-text` via Ollama
5. Persists to ChromaDB with incremental support: unchanged files are skipped, deleted files are removed from the index

**Query (`query.py`)**

1. Converts the question into an embedding and retrieves the most similar chunks from ChromaDB
2. Synthesizes an answer with `llama3.2:1b` using the chunks as context
3. Displays the answer and a table of source notes with similarity score and tags

## Configuration

All options are configured in `.env`:

| Variable | Default | Description |
|---|---|---|
| `OBSIDIAN_VAULT_PATH` | — | Path to the vault (required) |
| `OLLAMA_LLM_MODEL` | `llama3.2:1b` | Generation model |
| `OLLAMA_EMBED_MODEL` | `nomic-embed-text` | Embeddings model |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama URL |
| `CHUNK_SIZE` | `512` | Chunk size in tokens |
| `CHUNK_OVERLAP` | `64` | Overlap between chunks |
| `TOP_K` | `5` | Source notes retrieved per query |

## Re-index from scratch

```bash
rm -rf storage/
python ingest.py
```
