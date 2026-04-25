"""
mgj.commands.extract
--------------------
``mgj extract <slug> [-q N] [--force]``

Runs the LLM-driven extractor over the submission's input.md, emitting
typed RDF triples into instance.ttl. The default backend is
``ClaudeBackend``; tests inject ``MockLLMBackend`` via the
``mgj.commands.extract.backend_factory`` hook.
"""

from __future__ import annotations

from typing import Callable

import typer

from mgj.commands._common import console, err_console
from mgj.parser.backends import ClaudeBackend, LLMBackend
from mgj.parser.extract import run_extraction
from mgj.parser.schemas import QUESTIONS_WITH_ENTITIES

app = typer.Typer(no_args_is_help=True, help="LLM-driven extraction.")


def _default_backend_factory() -> LLMBackend:
    """Default to Claude. Override via monkeypatching for tests."""
    return ClaudeBackend()


backend_factory: Callable[[], LLMBackend] = _default_backend_factory
"""Module-level hook tests reassign to inject a mock backend."""


@app.command()
def extract(
    slug: str = typer.Argument(..., help="Submission slug"),
    question: int = typer.Option(
        None, "--question", "-q", help="Extract a specific question (default: all)"
    ),
    force: bool = typer.Option(
        False, "--force", help="Re-extract even for already-affirmed questions"
    ),
) -> None:
    if question is not None and question not in QUESTIONS_WITH_ENTITIES:
        raise typer.BadParameter(
            f"--question must be one of {QUESTIONS_WITH_ENTITIES}"
        )

    backend = backend_factory()
    try:
        result = run_extraction(
            slug,
            backend=backend,
            questions=[question] if question is not None else None,
            force=force,
        )
    except FileNotFoundError as e:
        err_console.print(f"[red]{e}[/red]")
        raise typer.Exit(code=1)

    if result.extracted_questions:
        qs = ", ".join(f"Q{q}" for q in result.extracted_questions)
        console.print(f"[green]✓ extracted[/green] {qs}")
    if result.cache_hits:
        qs = ", ".join(f"Q{q}" for q in result.cache_hits)
        console.print(f"[dim]cache hit:[/dim] {qs}")
    if result.skipped_affirmed:
        qs = ", ".join(f"Q{q}" for q in result.skipped_affirmed)
        console.print(
            f"[yellow]skipped affirmed:[/yellow] {qs} "
            "(use --force or `mgj unaffirm -q N` first)"
        )
