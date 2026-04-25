"""
mgj.commands.compile
--------------------
``mgj compile <slug>`` and ``mgj wiki [--output DIR]``.

Both are top-level commands implemented in their own minimal Typer apps;
``cli.py`` merges them into the main app via ``registered_commands``.
"""

from __future__ import annotations

from pathlib import Path

import typer

from mgj.commands._common import console, err_console
from mgj.compilers.catechism import compile_submission_file
from mgj.compilers.wiki import compile_wiki
from mgj.graph import project_root, submission_dir, submission_instance_path

compile_app = typer.Typer()
wiki_app = typer.Typer()


@compile_app.command(name="compile")
def compile_cmd(
    slug: str = typer.Argument(..., help="Submission slug to compile"),
) -> None:
    """Render <slug>/instance.ttl into <slug>/compiled.md."""
    instance = submission_instance_path(slug)
    if not instance.exists():
        err_console.print(f"[red]no instance.ttl at {instance}[/red]")
        raise typer.Exit(code=1)
    output = submission_dir(slug) / "compiled.md"
    output.write_text(compile_submission_file(instance))
    console.print(f"[green]✓ compiled[/green] {output}")


@wiki_app.command(name="wiki")
def wiki_cmd(
    output_dir: str = typer.Option(
        None, "--output", "-o", help="Output directory (default: <repo>/wiki)"
    ),
) -> None:
    """Generate the cross-linked wiki under wiki/ (or --output DIR)."""
    out = Path(output_dir) if output_dir else project_root() / "wiki"
    written = compile_wiki(out)
    console.print(f"[green]✓ wrote {len(written)} wiki page(s)[/green] to {out}")
