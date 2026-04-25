"""
mgj.commands.affirm
-------------------
Per-question affirmation tracking and a textual review dump.

Affirmation state lives in ``submissions/<slug>/extraction-trace.json``
rather than on RDF triples. Affirming Qi means: the parser's output for
that question has been reviewed and confirmed by the author. Affirmation
is sticky against re-extraction (M5 enforces this in reconcile.py).
"""

from __future__ import annotations

import typer
from rdflib import URIRef
from rich.panel import Panel

from mgj.commands._common import (
    console,
    err_console,
    get_submission_iri,
    load_submission_graph,
    load_trace,
    now_iso,
    save_trace,
)
from mgj.namespaces import MGJ
from mgj.validate import validate

app = typer.Typer(no_args_is_help=True, help="Per-question affirmation.")


@app.command()
def affirm(
    slug: str = typer.Argument(...),
    question: int = typer.Option(..., "--question", "-q", help="1..9"),
) -> None:
    """Mark Qi as affirmed. Runs per-Q SHACL first; rejects if it fails."""
    if not 1 <= question <= 9:
        raise typer.BadParameter("question must be 1..9")
    g = load_submission_graph(slug)
    report = validate(g, mode="per_question", question=question)
    if not report.conforms:
        err_console.print(
            f"[red]rejected: Q{question} failed per-question validation[/red]"
        )
        for v in report.violations:
            err_console.print(f"  • {v.message}")
        raise typer.Exit(code=1)

    trace = load_trace(slug)
    trace.affirmed_questions[question] = now_iso()
    save_trace(trace)
    console.print(f"[green]✓ Q{question} affirmed[/green]")


@app.command()
def unaffirm(
    slug: str = typer.Argument(...),
    question: int = typer.Option(..., "--question", "-q"),
) -> None:
    """Clear affirmation for Qi. Use before re-extracting."""
    trace = load_trace(slug)
    trace.affirmed_questions[question] = None
    save_trace(trace)
    console.print(f"[yellow]– Q{question} affirmation cleared[/yellow]")


@app.command()
def review(
    slug: str = typer.Argument(...),
    question: int = typer.Option(..., "--question", "-q"),
) -> None:
    """Render the current state of Qi: narrative + typed entities + violations."""
    g = load_submission_graph(slug)
    sub = get_submission_iri(g, slug)
    nar_prop = MGJ[f"q{question}Narrative"]
    nar = next(g.objects(sub, nar_prop), None)

    panel_body = []
    if nar is not None:
        panel_body.append(f"[bold]narrative[/bold]\n{str(nar)}")
    else:
        panel_body.append("[dim]narrative not set[/dim]")

    panel_body.append("")
    panel_body.append("[bold]entities[/bold]")
    panel_body.append(_render_entities(g, question))

    console.print(Panel("\n".join(panel_body), title=f"Q{question} review — {slug}"))

    report = validate(g, mode="per_question", question=question)
    if report.conforms:
        console.print(f"[green]✓ Q{question} per-question SHACL passes[/green]")
    else:
        console.print(
            f"[red]✗ Q{question} per-question SHACL fails: "
            f"{report.violation_count} violation(s)[/red]"
        )
        for v in report.violations:
            console.print(f"  • {v.message}")

    trace = load_trace(slug)
    affirmed = trace.affirmed_questions.get(question)
    console.print(f"affirmed: [bold]{affirmed or '—'}[/bold]")


def _render_entities(g, question: int) -> str:
    """Render the entities for a given question as plain text."""
    from rdflib import RDF, Literal

    rows: list[str] = []
    if question == 2:
        for s in sorted(g.subjects(RDF.type, MGJ.Stakeholder)):
            agent = next(g.objects(s, MGJ.stakeholderAgent), URIRef(""))
            role = next(g.objects(s, MGJ.roleLabel), Literal(""))
            rows.append(
                f"  · stakeholder {_id(s)}: agent={_short(agent)} role={role}"
            )
    elif question == 3:
        for s in sorted(g.subjects(RDF.type, MGJ.EnvironmentalFactor)):
            mod = next(g.objects(s, MGJ.lessigModality), URIRef(""))
            desc = next(g.objects(s, MGJ.factorDescription), Literal(""))
            rows.append(f"  · factor {_id(s)} [{_short(mod)}]: {desc}")
    elif question == 4:
        for s in sorted(g.subjects(RDF.type, MGJ.ConstitutionalElement)):
            label = next(g.objects(s, MGJ.elementLabel), Literal(""))
            etype = next(g.objects(s, MGJ.elementType), URIRef(""))
            rows.append(f"  · constitution {_id(s)} [{_short(etype)}]: {label}")
    elif question == 5:
        for s in sorted(g.subjects(RDF.type, MGJ.FieldSite)):
            label = next(g.objects(s, MGJ.fieldSiteLabel), Literal(""))
            url = next(g.objects(s, MGJ.fieldSiteURL), Literal(""))
            rows.append(f"  · fieldsite {_id(s)}: {label} {url}".rstrip())
    elif question == 7:
        for s in sorted(g.subjects(RDF.type, MGJ.OriginEvent)):
            label = next(g.objects(s, MGJ.originLabel), Literal(""))
            d = next(g.objects(s, MGJ.originDate), Literal(""))
            rows.append(f"  · origin {_id(s)}: {label} ({d})")
    elif question == 8:
        for s in sorted(g.subjects(RDF.type, MGJ.EvolutionMechanism)):
            label = next(g.objects(s, MGJ.mechanismLabel), Literal(""))
            rows.append(f"  · evolution {_id(s)}: {label}")
    elif question == 9:
        from rdflib.namespace import DCTERMS

        for s in sorted(g.subjects(RDF.type, MGJ.Reference)):
            title = next(g.objects(s, DCTERMS.title), Literal(""))
            ident = next(g.objects(s, DCTERMS.identifier), Literal(""))
            rows.append(f"  · reference {_id(s)}: {title} ({ident})")
    return "\n".join(rows) if rows else "  [dim](none)[/dim]"


def _id(s) -> str:
    return str(s).rsplit("/", 1)[-1]


def _short(uri) -> str:
    s = str(uri)
    if "#" in s:
        return s.rsplit("#", 1)[-1]
    return s.rsplit("/", 1)[-1]
