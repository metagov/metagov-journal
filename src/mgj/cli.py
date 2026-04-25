"""
mgj.cli
-------
Top-level Typer entry point.

Wires the lifecycle, registry, entity, and affirmation command modules
into a single ``mgj`` CLI.
"""

from __future__ import annotations

import typer

from mgj.commands.affirm import app as affirm_app
from mgj.commands.compile import compile_app, wiki_app
from mgj.commands.extract import app as extract_app
from mgj.commands.entities import (
    author_app,
    constitution_app,
    evolution_app,
    factor_app,
    fieldsite_app,
    legal_app,
    origin_app,
    reference_app,
    stakeholder_app,
)
from mgj.commands.lifecycle import app as lifecycle_app
from mgj.commands.registries import orgs_app, people_app

app = typer.Typer(
    no_args_is_help=True,
    help="Metagov Journal — RDF-native catechism authoring CLI.",
)

# Lifecycle commands (init, status, validate, canonicalize, narrative)
# are top-level rather than nested under a sub-typer, so users can write
# `mgj init …` instead of `mgj lifecycle init …`. Typer's `add_typer`
# does not flatten cleanly, so we register each as a top-level command.
for command_info in lifecycle_app.registered_commands:
    app.registered_commands.append(command_info)

# Affirmation commands likewise top-level (affirm, unaffirm, review).
for command_info in affirm_app.registered_commands:
    app.registered_commands.append(command_info)

# Entity sub-typers
app.add_typer(stakeholder_app, name="stakeholder")
app.add_typer(factor_app, name="factor")
app.add_typer(constitution_app, name="constitution")
app.add_typer(fieldsite_app, name="fieldsite")
app.add_typer(origin_app, name="origin")
app.add_typer(evolution_app, name="evolution")
app.add_typer(reference_app, name="reference")
app.add_typer(legal_app, name="legal")
app.add_typer(author_app, name="author")

# Compilers + parser — register as top-level commands by lifting their
# Typer.registered_commands onto the main app.
for command_info in compile_app.registered_commands:
    app.registered_commands.append(command_info)
for command_info in wiki_app.registered_commands:
    app.registered_commands.append(command_info)
for command_info in extract_app.registered_commands:
    app.registered_commands.append(command_info)

# Shared registry sub-typers
app.add_typer(people_app, name="people")
app.add_typer(orgs_app, name="orgs")


if __name__ == "__main__":
    app()
