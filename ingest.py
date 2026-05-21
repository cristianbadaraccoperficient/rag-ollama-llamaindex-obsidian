import sys

from rich.console import Console

import config
from obsidian_parser import clean_obsidian_text, obsidian_file_metadata
from llama_index.core.schema import Document

console = Console()


def main():
    console.print("[bold cyan]RAG Obsidian — Ingesta[/bold cyan]")

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
    console.print(f"Modelo LLM: [yellow]{config.OLLAMA_LLM_MODEL}[/yellow]  |  Embeddings: [yellow]{config.OLLAMA_EMBED_MODEL}[/yellow]")

    # Load docstore (incremental indexing state)
    if config.DOCSTORE_PATH.exists():
        docstore = SimpleDocumentStore.from_persist_path(str(config.DOCSTORE_PATH))
        console.print(f"Docstore cargado: {len(docstore.docs)} documentos previos")
    else:
        docstore = SimpleDocumentStore()
        console.print("Docstore nuevo")

    # Load ingestion cache
    if config.CACHE_PATH.exists():
        ingest_cache = IngestionCache.from_persist_path(str(config.CACHE_PATH))
        console.print("Cache de ingesta cargado")
    else:
        ingest_cache = IngestionCache()

    # Read vault
    console.print("\nLeyendo archivos .md del vault...")
    reader = SimpleDirectoryReader(
        input_dir=str(config.OBSIDIAN_VAULT_PATH),
        recursive=True,
        required_exts=[".md"],
        filename_as_id=True,
        file_metadata=obsidian_file_metadata,
    )
    documents = reader.load_data(show_progress=True)
    console.print(f"[green]{len(documents)}[/green] notas encontradas")

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

    console.print("\nIndexando... (esto puede tardar varios minutos en la primera ejecución)")
    nodes = pipeline.run(documents=documents, show_progress=True)

    docstore.persist(persist_path=str(config.DOCSTORE_PATH))
    ingest_cache.persist(persist_path=str(config.CACHE_PATH))

    console.print(f"\n[bold green]Listo.[/bold green] {len(nodes)} nodos indexados en ChromaDB.")
    console.print(f"Índice guardado en: [dim]{config.CHROMA_DB_PATH}[/dim]")


if __name__ == "__main__":
    main()
