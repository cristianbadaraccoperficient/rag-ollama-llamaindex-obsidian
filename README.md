# RAG Obsidian — Ollama + LlamaIndex + ChromaDB

Sistema RAG completamente local que usa tu vault de Obsidian como fuente de conocimiento. Sin API keys, sin datos en la nube.

## Stack

| Rol | Tecnología |
|---|---|
| LLM (generación) | [Ollama](https://ollama.com) — `llama3.2:1b` |
| Embeddings | Ollama — `nomic-embed-text` |
| Framework RAG | [LlamaIndex](https://www.llamaindex.ai) |
| Vector store | [ChromaDB](https://www.trychroma.com) (local) |
| Fuente de datos | Vault de Obsidian (archivos `.md`) |

## Requisitos

- Python 3.11+
- [Ollama](https://ollama.com/download) instalado y corriendo

## Instalación

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Bajar los modelos
ollama pull llama3.2:1b
ollama pull nomic-embed-text

# 3. Configurar
cp .env.example .env
```

Editá `.env` y poné la ruta de tu vault:

```ini
OBSIDIAN_VAULT_PATH=C:\Users\tu-usuario\Documents\mi-vault
```

Para encontrar la ruta en Obsidian: **Settings → About → Vault path**.

## Uso

```bash
# Indexar el vault (primera vez o después de cambiar notas)
python ingest.py

# Consultar
python query.py "¿Qué notas tengo sobre machine learning?"
```

La primera indexación puede tardar varios minutos según el tamaño del vault. Las siguientes son incrementales: solo se re-indexan notas nuevas o modificadas.

## Cómo funciona

**Ingesta (`ingest.py`)**

1. Lee todos los `.md` del vault recursivamente
2. Limpia el texto: extrae frontmatter YAML como metadata, convierte `[[wikilinks]]` a texto plano, normaliza `#tags`
3. Divide cada nota en chunks con `MarkdownNodeParser` (por headings) + `SentenceSplitter` (512 tokens, overlap 64)
4. Genera embeddings con `nomic-embed-text` vía Ollama
5. Persiste en ChromaDB con soporte incremental: archivos sin cambios se saltean, archivos borrados se eliminan del índice

**Consulta (`query.py`)**

1. Convierte la pregunta en un embedding y busca los chunks más similares en ChromaDB
2. Sintetiza una respuesta con `llama3.2` usando los chunks como contexto
3. Muestra la respuesta y una tabla con las notas fuente, su score de similitud y tags

## Configuración

Todas las opciones se configuran en `.env`:

| Variable | Default | Descripción |
|---|---|---|
| `OBSIDIAN_VAULT_PATH` | — | Ruta al vault (requerida) |
| `OLLAMA_LLM_MODEL` | `llama3.2:1b` | Modelo de generación |
| `OLLAMA_EMBED_MODEL` | `nomic-embed-text` | Modelo de embeddings |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | URL de Ollama |
| `CHUNK_SIZE` | `512` | Tamaño de chunks en tokens |
| `CHUNK_OVERLAP` | `64` | Overlap entre chunks |
| `TOP_K` | `5` | Notas fuente a recuperar por consulta |

## Re-indexar desde cero

```bash
rm -rf storage/
python ingest.py
```
