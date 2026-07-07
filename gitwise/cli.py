"""GitWise CLI entry point.

Usage:
    gitwise index https://github.com/tiangolo/fastapi --repo fastapi
    gitwise query "How does dependency injection work?" --repo fastapi
    gitwise chat --repo fastapi
"""
import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.status import Status

from gitwise.core.cloner import CloneError, clone_repo, repo_name_from_url
from gitwise.core.indexer import build_index, collection_exists, query_index
from gitwise.core.llm import LLMError, answer_question
from gitwise.core.branding import show_intro_animation, print_assistant_label

app = typer.Typer(help="Chat with any GitHub repo in plain English.")
console = Console()


@app.command()
def index(
    url: str = typer.Argument(..., help="GitHub repository URL, e.g. https://github.com/owner/repo"),
    repo: str = typer.Option(None, "--repo", help="Friendly name to refer to this repo later. Defaults to owner__repo."),
    force: bool = typer.Option(False, "--force", help="Re-clone and re-index even if already cached."),
):
    """Clone a GitHub repo and build its searchable index."""
    collection_name = repo or repo_name_from_url(url)

    try:
        with Status(f"[bold cyan]Cloning {url} ...", console=console):
            local_path = clone_repo(url, force=force)
    except CloneError as e:
        console.print(f"[bold red]Clone failed:[/bold red] {e}")
        raise typer.Exit(code=1)

    try:
        with Status("[bold cyan]Chunking files and building vector index ...", console=console):
            chunk_count = build_index(local_path, collection_name)
    except Exception as e:
        console.print(f"[bold red]Indexing failed:[/bold red] {e}")
        raise typer.Exit(code=1)

    if chunk_count == 0:
        console.print(
            Panel(
                "No indexable files were found. Check that the repo has source files "
                "with supported extensions.",
                title="⚠️  Nothing indexed",
                border_style="yellow",
            )
        )
        raise typer.Exit(code=1)

    console.print(
        Panel(
            f"Repo:  [bold]{url}[/bold]\n"
            f"Name:  [bold]{collection_name}[/bold]\n"
            f"Chunks indexed: [bold]{chunk_count}[/bold]\n\n"
            f"Try:  gitwise chat --repo {collection_name}",
            title="✅  Index ready",
            border_style="green",
        )
    )


def _ask_and_print(repo: str, question: str, n_results: int) -> None:
    """Retrieve context, call the LLM, and print a Markdown answer with sources."""
    with Status("[bold cyan]Retrieving relevant code ...", console=console):
        hits = query_index(repo, question, n_results=n_results)

    with Status("[bold cyan]Asking the model ...", console=console):
        answer = answer_question(question, hits)

    print_assistant_label(console)
    console.print(Markdown(answer))

    if hits:
        sources = ", ".join(sorted({h["file_path"] for h in hits}))
        console.print(f"\n[dim]Sources: {sources}[/dim]")


@app.command()
def query(
    question: str = typer.Argument(..., help="Your question about the repo, in plain English."),
    repo: str = typer.Option(..., "--repo", help="Name given to the repo when it was indexed."),
    n_results: int = typer.Option(6, "--n-results", help="How many chunks to retrieve for context."),
):
    """Ask a single question about a previously indexed repo."""
    if not collection_exists(repo):
        console.print(
            f"[bold red]No index found for repo '{repo}'.[/bold red] "
            f"Run [bold]gitwise index <url> --repo {repo}[/bold] first."
        )
        raise typer.Exit(code=1)

    try:
        _ask_and_print(repo, question, n_results)
    except LLMError as e:
        console.print(f"[bold red]{e}[/bold red]")
        raise typer.Exit(code=1)


@app.command()
def chat(
    repo: str = typer.Option(..., "--repo", help="Name given to the repo when it was indexed."),
    n_results: int = typer.Option(6, "--n-results", help="How many chunks to retrieve for context."),
):
    """Have an ongoing conversation about a previously indexed repo.

    Type your questions one after another. Type 'exit' or 'quit' to leave.
    """
    if not collection_exists(repo):
        console.print(
            f"[bold red]No index found for repo '{repo}'.[/bold red] "
            f"Run [bold]gitwise index <url> --repo {repo}[/bold] first."
        )
        raise typer.Exit(code=1)

    show_intro_animation(console)

    console.print(
        Panel(
            f"Chatting about [bold]{repo}[/bold]. Type your question and press Enter.\n"
            f"Type [bold]exit[/bold] or [bold]quit[/bold] to leave.",
            title="💬  GitWise Chat",
            border_style="cyan",
        )
    )

    while True:
        try:
            question = console.input("\n[bold green]You:[/bold green] ")
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Goodbye.[/dim]")
            break

        if question.strip().lower() in {"exit", "quit"}:
            console.print("[dim]Goodbye.[/dim]")
            break

        if not question.strip():
            continue

        try:
            _ask_and_print(repo, question, n_results)
        except LLMError as e:
            console.print(f"[bold red]{e}[/bold red]")
            # Don't exit the loop for one bad answer - let them fix the key and keep chatting
            continue


if __name__ == "__main__":
    app()
