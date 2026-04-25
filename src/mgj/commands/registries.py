"""
mgj.commands.registries
-----------------------
CLI commands for the shared people and organizations registries.

Both registries support add / set / list. Removal is intentionally not
supported — references from active submissions could break, and stale
entries do no harm. To retire a person, leave their record in place.
"""

from __future__ import annotations

import typer
from rdflib import Graph, Literal, URIRef
from rdflib.namespace import FOAF, RDF, XSD
from rich.table import Table

from mgj.commands._common import (
    console,
    err_console,
    load_shared_registry,
    save_shared_registry,
)
from mgj.namespaces import organization_iri, person_iri

people_app = typer.Typer(no_args_is_help=True, help="Shared people registry.")
orgs_app = typer.Typer(no_args_is_help=True, help="Shared organizations registry.")


# ---------------------------------------------------------------------------
# people
# ---------------------------------------------------------------------------


@people_app.command("add")
def people_add(
    slug: str = typer.Argument(..., help="URL-safe slug, e.g. 'michael-zargham'"),
    name: str = typer.Option(..., "--name", "-n", help="Display name"),
    homepage: str = typer.Option(None, "--homepage", help="Homepage URL"),
) -> None:
    """Add a foaf:Person to shared/people.ttl. Errors if the slug exists."""
    g = load_shared_registry("people.ttl")
    iri = URIRef(person_iri(slug))
    if (iri, RDF.type, FOAF.Person) in g:
        err_console.print(f"[red]person '{slug}' already exists; use `set` to update[/red]")
        raise typer.Exit(code=1)
    g.add((iri, RDF.type, FOAF.Person))
    g.add((iri, FOAF.name, Literal(name)))
    if homepage:
        g.add((iri, FOAF.homepage, Literal(homepage, datatype=XSD.anyURI)))
    save_shared_registry(g, "people.ttl")
    console.print(f"[green]✓ added person[/green] {slug} → {iri}")


@people_app.command("set")
def people_set(
    slug: str = typer.Argument(...),
    name: str = typer.Option(None, "--name", "-n"),
    homepage: str = typer.Option(None, "--homepage"),
) -> None:
    """Update an existing person. Pass only the fields you want to change."""
    g = load_shared_registry("people.ttl")
    iri = URIRef(person_iri(slug))
    if (iri, RDF.type, FOAF.Person) not in g:
        err_console.print(f"[red]person '{slug}' not found[/red]")
        raise typer.Exit(code=1)
    if name is not None:
        g.remove((iri, FOAF.name, None))
        g.add((iri, FOAF.name, Literal(name)))
    if homepage is not None:
        g.remove((iri, FOAF.homepage, None))
        g.add((iri, FOAF.homepage, Literal(homepage, datatype=XSD.anyURI)))
    save_shared_registry(g, "people.ttl")
    console.print(f"[green]✓ updated person[/green] {slug}")


@people_app.command("list")
def people_list() -> None:
    """List all people in the shared registry."""
    g = load_shared_registry("people.ttl")
    table = Table("slug", "name", "homepage")
    for s in sorted(g.subjects(RDF.type, FOAF.Person)):
        slug = str(s).rsplit("/", 1)[-1]
        name = next(g.objects(s, FOAF.name), Literal(""))
        homepage = next(g.objects(s, FOAF.homepage), Literal(""))
        table.add_row(slug, str(name), str(homepage))
    console.print(table)


# ---------------------------------------------------------------------------
# orgs
# ---------------------------------------------------------------------------


@orgs_app.command("add")
def orgs_add(
    slug: str = typer.Argument(...),
    name: str = typer.Option(..., "--name", "-n"),
    homepage: str = typer.Option(None, "--homepage"),
) -> None:
    """Add a foaf:Organization to shared/organizations.ttl."""
    g = load_shared_registry("organizations.ttl")
    iri = URIRef(organization_iri(slug))
    if (iri, RDF.type, FOAF.Organization) in g:
        err_console.print(f"[red]org '{slug}' already exists; use `set` to update[/red]")
        raise typer.Exit(code=1)
    g.add((iri, RDF.type, FOAF.Organization))
    g.add((iri, FOAF.name, Literal(name)))
    if homepage:
        g.add((iri, FOAF.homepage, Literal(homepage, datatype=XSD.anyURI)))
    save_shared_registry(g, "organizations.ttl")
    console.print(f"[green]✓ added org[/green] {slug} → {iri}")


@orgs_app.command("set")
def orgs_set(
    slug: str = typer.Argument(...),
    name: str = typer.Option(None, "--name", "-n"),
    homepage: str = typer.Option(None, "--homepage"),
) -> None:
    g = load_shared_registry("organizations.ttl")
    iri = URIRef(organization_iri(slug))
    if (iri, RDF.type, FOAF.Organization) not in g:
        err_console.print(f"[red]org '{slug}' not found[/red]")
        raise typer.Exit(code=1)
    if name is not None:
        g.remove((iri, FOAF.name, None))
        g.add((iri, FOAF.name, Literal(name)))
    if homepage is not None:
        g.remove((iri, FOAF.homepage, None))
        g.add((iri, FOAF.homepage, Literal(homepage, datatype=XSD.anyURI)))
    save_shared_registry(g, "organizations.ttl")
    console.print(f"[green]✓ updated org[/green] {slug}")


@orgs_app.command("list")
def orgs_list() -> None:
    g = load_shared_registry("organizations.ttl")
    table = Table("slug", "name", "homepage")
    for s in sorted(g.subjects(RDF.type, FOAF.Organization)):
        slug = str(s).rsplit("/", 1)[-1]
        name = next(g.objects(s, FOAF.name), Literal(""))
        homepage = next(g.objects(s, FOAF.homepage), Literal(""))
        table.add_row(slug, str(name), str(homepage))
    console.print(table)
