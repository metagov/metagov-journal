"""
mgj.commands.lifecycle
----------------------
Lifecycle commands: init, status, validate, canonicalize, narrative.
"""

from __future__ import annotations

from datetime import date as DateT
from pathlib import Path

import typer
from rdflib import Graph, Literal, URIRef
from rdflib.namespace import RDF, XSD
from rich.table import Table

from mgj.canonicalize import canonicalize_file, canonicalize_turtle
from mgj.commands._common import (
    ExtractionTrace,
    console,
    err_console,
    get_submission_iri,
    get_submission_version,
    load_submission_graph,
    load_trace,
    now_iso,
    report_validation,
    save_submission_graph_separating_shared,
    save_trace,
    trace_path,
    with_mutation,
)
from mgj.graph import submission_dir, submission_instance_path
from mgj.namespaces import MGJ, institution_iri, submission_iri
from mgj.validate import validate

app = typer.Typer(no_args_is_help=True, help="Lifecycle commands.")

INPUT_TEMPLATE = """# {name}

*Author's prose answering the institutional catechism. The CLI parser
extracts typed RDF from this file; you confirm the extraction Q-by-Q
before compilation.*

## 1. What is the institution's purpose?

(Write 75–110 words.)

## 2. Who are the stakeholders and what are their roles?

## 3. What environmental factors shape the institution?

## 4. What constitutes the institution's constitution?

## 5. Where are the field sites?

## 6. What is your relationship to the institution?

## 7. How and when did the institution emerge?

## 8. How does the institution evolve?

## 9. What references support this documentation?
"""


@app.command()
def init(
    slug: str = typer.Argument(..., help="URL-safe submission slug, e.g. 'metagov-journal'"),
    name: str = typer.Option(..., "--name", "-n", help="Institution display name"),
    version: str = typer.Option("1.0.0", "--version", "-v", help="Submission version"),
    submission_date: str = typer.Option(
        None, "--date", "-d", help="ISO date (defaults to today)"
    ),
) -> None:
    """Scaffold a new submission directory: input.md, instance.ttl skeleton,
    and extraction-trace.json. Refuses to overwrite an existing submission
    (instance.ttl present); coexists with other files (e.g. manifest.yml,
    legacy specification.md)."""
    target = submission_dir(slug)
    if (target / "instance.ttl").exists():
        err_console.print(
            f"[red]submission '{slug}' already initialized "
            f"(instance.ttl exists at {target})[/red]"
        )
        raise typer.Exit(code=1)
    target.mkdir(parents=True, exist_ok=True)

    # input.md — only write if not already present.
    input_path = target / "input.md"
    if not input_path.exists():
        input_path.write_text(INPUT_TEMPLATE.format(name=name))

    # instance.ttl skeleton: just the Submission and Institution stubs.
    g = Graph()
    inst = URIRef(institution_iri(slug))
    sub = URIRef(submission_iri(slug, version))
    g.add((inst, RDF.type, MGJ.Institution))
    g.add((inst, MGJ.institutionName, Literal(name)))
    g.add((sub, RDF.type, MGJ.Submission))
    g.add((sub, MGJ.documents, inst))
    g.add((sub, MGJ.submissionVersion, Literal(version)))
    today = submission_date or DateT.today().isoformat()
    g.add((sub, MGJ.submissionDate, Literal(today, datatype=XSD.date)))

    save_submission_graph_separating_shared(g, slug)

    # Trace skeleton
    save_trace(
        ExtractionTrace(
            slug=slug,
            version=version,
            affirmed_questions={i: None for i in range(1, 10)},
            extractions=[],
        )
    )

    console.print(f"[green]✓ initialized[/green] submissions/{slug}/")
    console.print(f"  input.md, instance.ttl, extraction-trace.json")


@app.command()
def status(
    slug: str = typer.Argument(..., help="Submission slug"),
) -> None:
    """Report instance state: version, entity counts, per-Q affirmation status."""
    g = load_submission_graph(slug)
    sub = get_submission_iri(g, slug)
    version = get_submission_version(g, slug)
    trace = load_trace(slug)

    console.print(f"[bold]{slug}[/bold] v{version}")
    console.print(f"  IRI: {sub}")

    counts = _entity_counts(g)
    table = Table("question", "entity", "count", "affirmed")
    rows = [
        (1, "(narrative)", _has_narrative(g, sub, "q1Narrative"), trace.affirmed_questions.get(1)),
        (2, "stakeholders", counts["Stakeholder"], trace.affirmed_questions.get(2)),
        (3, "environmental factors", counts["EnvironmentalFactor"], trace.affirmed_questions.get(3)),
        (4, "constitutional elements", counts["ConstitutionalElement"], trace.affirmed_questions.get(4)),
        (5, "field sites", counts["FieldSite"], trace.affirmed_questions.get(5)),
        (6, "(author disclosure)", _has_narrative(g, sub, "q6Narrative"), trace.affirmed_questions.get(6)),
        (7, "origin events", counts["OriginEvent"], trace.affirmed_questions.get(7)),
        (8, "evolution mechanisms", counts["EvolutionMechanism"], trace.affirmed_questions.get(8)),
        (9, "references", counts["Reference"], trace.affirmed_questions.get(9)),
    ]
    for q, label, count, affirmed in rows:
        table.add_row(
            f"Q{q}",
            label,
            str(count),
            affirmed or "[dim]—[/dim]",
        )
    console.print(table)


def _entity_counts(g: Graph) -> dict[str, int]:
    out: dict[str, int] = {}
    for cls in [
        "Stakeholder",
        "EnvironmentalFactor",
        "ConstitutionalElement",
        "FieldSite",
        "OriginEvent",
        "EvolutionMechanism",
        "Reference",
        "LegalContext",
    ]:
        out[cls] = sum(1 for _ in g.subjects(predicate=RDF.type, object=MGJ[cls]))
    return out


def _has_narrative(g: Graph, sub: URIRef, prop: str) -> str:
    """Return 'set' or '—'."""
    return "set" if any(g.objects(subject=sub, predicate=MGJ[prop])) else "—"


@app.command(name="validate")
def validate_cmd(
    slug: str = typer.Argument(..., help="Submission slug"),
    question: int = typer.Option(
        None, "--question", "-q", help="Validate against Qi inner-loop shapes only"
    ),
) -> None:
    """Run SHACL validation. Defaults to system shapes; pass -q N for per-Q."""
    g = load_submission_graph(slug)
    if question is not None:
        report = validate(g, mode="per_question", question=question)
        report_validation(report, label=f"Q{question} per-question")
    else:
        report = validate(g, mode="system")
        report_validation(report, label="system")
    if not report.conforms:
        raise typer.Exit(code=1)


@app.command()
def canonicalize(
    slug: str = typer.Argument(..., help="Submission slug"),
) -> None:
    """Re-normalize instance.ttl into canonical form. Idempotent."""
    p = submission_instance_path(slug)
    if not p.exists():
        err_console.print(f"[red]no instance.ttl at {p}[/red]")
        raise typer.Exit(code=1)
    changed = canonicalize_file(p)
    if changed:
        console.print(f"[yellow]canonicalized[/yellow] {p}")
    else:
        console.print(f"[green]already canonical[/green] {p}")


@app.command()
def narrative(
    slug: str = typer.Argument(..., help="Submission slug"),
    question: int = typer.Option(..., "--question", "-q", help="Question number 1..9"),
    text: str = typer.Argument(..., help="Narrative text"),
) -> None:
    """Set the narrative for a catechism question. Replaces any existing
    narrative for that question."""
    if not 1 <= question <= 9:
        raise typer.BadParameter("question must be 1..9")
    if not text.strip():
        raise typer.BadParameter("narrative must be non-empty")
    with with_mutation(slug, question=question) as g:
        sub = get_submission_iri(g, slug)
        prop = MGJ[f"q{question}Narrative"]
        g.remove((sub, prop, None))
        g.add((sub, prop, Literal(text)))
    console.print(f"[green]✓ Q{question} narrative set[/green]")
