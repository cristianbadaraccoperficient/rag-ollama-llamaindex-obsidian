import sys

from rich.console import Console

import config
from obsidian_parser import clean_obsidian_text, obsidian_file_metadata
from llama_index.core.schema import Document

console = Console()


def main():
    console.print("[bold cyan]RAG Obsidian — Ingest[/bold cyan]")

    try:
        config.validate()
    except (FileNotFoundError, RuntimeError) as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)

    from llama_index.core import Settings, SimpleDirectoryReader
    from llama_index.core.ingestion import IngestionCache, IngestionPipeline
    from llama_index.core.node_parser import MarkdownNodeParser, SentenceSplitter
    from llama_index.core.storage.docstore import SimpleDocumentStore
    from llama_index.core.ingestion import DocstoreStrategy

    Settings.llm = config.get_llm()
    Settings.embed_model = config.get_embed_model()
    Settings.chunk_size = config.CHUNK_SIZE
    Settings.chunk_overlap = config.CHUNK_OVERLAP

    console.print(f"Vault: [green]{config.OBSIDIAN_VAULT_PATH}[/green]")
    console.print(f"LLM model: [yellow]{config.OLLAMA_LLM_MODEL}[/yellow]  |  Embeddings: [yellow]{config.OLLAMA_EMBED_MODEL}[/yellow]")

    # Load docstore (incremental indexing state)
    if config.DOCSTORE_PATH.exists():
        docstore = SimpleDocumentStore.from_persist_path(str(config.DOCSTORE_PATH))
        console.print(f"Docstore loaded: {len(docstore.docs)} previous documents")
    else:
        docstore = SimpleDocumentStore()
        console.print("New docstore")

    # Load ingestion cache
    if config.CACHE_PATH.exists():
        ingest_cache = IngestionCache.from_persist_path(str(config.CACHE_PATH))
        console.print("Ingestion cache loaded")
    else:
        ingest_cache = IngestionCache()

    # Read vault
    console.print("\nReading .md files from vault...")
    reader = SimpleDirectoryReader(
        input_dir=str(config.OBSIDIAN_VAULT_PATH),
        recursive=True,
        required_exts=[".md"],
        filename_as_id=True,
        file_metadata=obsidian_file_metadata,
    )
    documents = reader.load_data(show_progress=True)
    console.print(f"[green]{len(documents)}[/green] notes found")

    # Apply Obsidian text transforms (Document.text is read-only in Pydantic v2)
    documents = [
        Document(
            text=clean_obsidian_text(doc.text)[0],
            metadata=doc.metadata,
            id_=doc.id_,
        )
        for doc in documents
    ]

    vector_store = config.get_chroma_vector_store()

    pipeline = IngestionPipeline(
        transformations=[
            MarkdownNodeParser(),
            SentenceSplitter(chunk_size=config.CHUNK_SIZE, chunk_overlap=config.CHUNK_OVERLAP),
            Settings.embed_model,
        ],
        vector_store=vector_store,
        docstore=docstore,
        cache=ingest_cache,
        docstore_strategy=DocstoreStrategy.UPSERTS_AND_DELETE,
    )

    console.print("\nIndexing... (first run may take several minutes)")
    nodes = pipeline.run(documents=documents, show_progress=True)

    docstore.persist(persist_path=str(config.DOCSTORE_PATH))
    ingest_cache.persist(persist_path=str(config.CACHE_PATH))

    console.print(f"\n[bold green]Done.[/bold green] {len(nodes)} nodes indexed in ChromaDB.")
    console.print(f"Index stored at: [dim]{config.CHROMA_DB_PATH}[/dim]")


if __name__ == "__main__":
    main()
