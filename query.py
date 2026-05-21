import sys

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

import config

console = Console()


def display_response(response) -> None:
    console.print(Panel(str(response), title="Answer", border_style="green", padding=(1, 2)))

    if not response.source_nodes:
        return

    table = Table(title="Source notes", show_lines=True, header_style="bold magenta")
    table.add_column("Note", style="cyan", no_wrap=True)
    table.add_column("Score", justify="right", style="yellow")
    table.add_column("Tags", style="dim")

    for node in response.source_nodes:
        meta = node.node.metadata
        score = f"{node.score:.3f}" if node.score is not None else "n/a"
        table.add_row(
            meta.get("note_title") or meta.get("file_name", "unknown"),
            score,
            meta.get("tags", ""),
        )

    console.print(table)


def build_query_engine():
    from llama_index.core import Settings, VectorStoreIndex
    from llama_index.core.response_synthesizers import ResponseMode

    Settings.llm = config.get_llm()
    Settings.embed_model = config.get_embed_model()
    vector_store = config.get_chroma_vector_store(readonly=True)
    index = VectorStoreIndex.from_vector_store(vector_store)
    return index.as_query_engine(
        similarity_top_k=config.TOP_K,
        response_mode=ResponseMode.SIMPLE_SUMMARIZE,
    )


def main():
    if len(sys.argv) < 2:
        console.print("[bold red]Usage:[/bold red] python query.py \"your question\"")
        sys.exit(1)

    question = " ".join(sys.argv[1:])

    try:
        config.validate()
    except (FileNotFoundError, RuntimeError) as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)

    if not config.CHROMA_DB_PATH.exists():
        console.print("[bold red]Error:[/bold red] No index found. Run first: python ingest.py")
        sys.exit(1)

    console.print(f"[bold cyan]Question:[/bold cyan] {question}\n")

    with console.status("Querying..."):
        response = build_query_engine().query(question)

    display_response(response)


if __name__ == "__main__":
    main()
