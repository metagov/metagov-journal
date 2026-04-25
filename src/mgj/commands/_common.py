"""
mgj.commands._common
--------------------
Shared helpers for CLI command modules.

Every CLI mutation flows through ``with_mutation`` so the database
invariant holds:
    1. Load instance.ttl + shared registries into a graph.
    2. Apply mutation in-memory.
    3. Run per-question SHACL on the affected Qi (if any).
    4. If validation fails, abort with a structured error and leave
       the on-disk file unchanged.
    5. Otherwise canonicalize and save.

Affirmation state lives in ``submissions/<slug>/extraction-trace.json``
rather than on RDF triples — see ``load_trace`` / ``save_trace``.
"""

from __future__ import annotations

import json
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterator

import typer
from rdflib import Graph, Literal, URIRef
from rich.console import Console
from rich.table import Table

from mgj.canonicalize import canonicalize_turtle
from mgj.graph import (
    SHARED_DIR,
    SUBMISSIONS_DIR,
    sparql_select,
    submission_dir,
    submission_instance_path,
)
from mgj.namespaces import MGJ, submission_entity_iri, submission_iri
from mgj.validate import ValidationReport, validate

console = Console()
err_console = Console(stderr=True)


# ---------------------------------------------------------------------------
# Affirmation / extraction trace
# ---------------------------------------------------------------------------

TRACE_FILENAME = "extraction-trace.json"


@dataclass
class ExtractionTrace:
    slug: str
    version: str
    affirmed_questions: dict[int, str | None] = field(default_factory=dict)
    """question number -> ISO timestamp of affirmation (or None)."""
    extractions: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "slug": self.slug,
            "version": self.version,
            "affirmed_questions": {str(k): v for k, v in self.affirmed_questions.items()},
            "extractions": self.extractions,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ExtractionTrace":
        return cls(
            slug=data["slug"],
            version=data["version"],
            affirmed_questions={int(k): v for k, v in data.get("affirmed_questions", {}).items()},
            extractions=data.get("extractions", []),
        )


def trace_path(slug: str) -> Path:
    return submission_dir(slug) / TRACE_FILENAME


def load_trace(slug: str) -> ExtractionTrace:
    p = trace_path(slug)
    if not p.exists():
        raise typer.BadParameter(
            f"submission '{slug}' has no extraction-trace.json — run `mgj init {slug}` first"
        )
    return ExtractionTrace.from_dict(json.loads(p.read_text()))


def save_trace(trace: ExtractionTrace) -> None:
    p = trace_path(trace.slug)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(trace.to_dict(), indent=2, sort_keys=True) + "\n")


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# Graph load / save with shared registries
# ---------------------------------------------------------------------------


def _merge_shared(g: Graph) -> None:
    if SHARED_DIR.is_dir():
        for ttl in sorted(SHARED_DIR.glob("*.ttl")):
            g.parse(str(ttl), format="turtle")


def load_submission_graph(slug: str, *, merge_shared: bool = True) -> Graph:
    """Load instance.ttl, optionally merging shared registries.

    The shared registries are merged so SHACL validation sees foaf:Person
    and foaf:Organization triples for resolution checks.
    """
    p = submission_instance_path(slug)
    if not p.exists():
        raise typer.BadParameter(
            f"submission '{slug}' has no instance.ttl at {p} — run `mgj init {slug}` first"
        )
    g = Graph()
    if merge_shared:
        _merge_shared(g)
    g.parse(str(p), format="turtle")
    return g


def save_submission_graph_separating_shared(g: Graph, slug: str) -> None:
    """Write only the per-submission triples to instance.ttl in canonical form.

    Triples whose subjects live in the shared registries (people/orgs) are
    excluded from the per-submission graph so we don't duplicate them on disk.
    """
    submission_only = Graph()
    shared_subjects = _shared_subject_iris()
    for s, p, o in g:
        if str(s) in shared_subjects:
            continue
        submission_only.add((s, p, o))

    out = submission_instance_path(slug)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(canonicalize_turtle(submission_only))


def _shared_subject_iris() -> set[str]:
    """All subject IRIs that live in shared/*.ttl. Used to keep them out of
    instance.ttl when we save."""
    g = Graph()
    _merge_shared(g)
    return {str(s) for s in g.subjects()}


# ---------------------------------------------------------------------------
# Submission identity helpers
# ---------------------------------------------------------------------------


def get_submission_iri(g: Graph, slug: str) -> URIRef:
    """Find the single mgj:Submission IRI in this graph and confirm it
    matches ``slug``. Errors loudly if zero or multiple are found."""
    rows = sparql_select(g, "SELECT ?s WHERE { ?s a mgj:Submission }")
    if not rows:
        raise typer.BadParameter(f"no mgj:Submission found in instance for '{slug}'")
    if len(rows) > 1:
        raise typer.BadParameter(
            f"expected one mgj:Submission per instance.ttl; found {len(rows)} for '{slug}'"
        )
    return URIRef(rows[0]["s"])


def get_submission_version(g: Graph, slug: str) -> str:
    sub = get_submission_iri(g, slug)
    rows = sparql_select(
        g,
        f"SELECT ?v WHERE {{ <{sub}> mgj:submissionVersion ?v }}",
    )
    if not rows:
        raise typer.BadParameter(
            f"submission for '{slug}' has no mgj:submissionVersion triple"
        )
    return rows[0]["v"]


def next_local_id(g: Graph, slug: str, version: str, kind: str, owl_class: str) -> str:
    """Find the next available numeric local id for entities of `kind`.

    ``owl_class`` is the OWL class local name (e.g. 'Stakeholder') used to
    locate existing entities of this kind.
    """
    base = submission_entity_iri(slug, version, kind, "")
    rows = sparql_select(
        g,
        f"SELECT ?s WHERE {{ ?s a mgj:{owl_class} }}",
    )
    nums: list[int] = []
    for row in rows:
        iri = row["s"]
        if iri.startswith(base):
            tail = iri[len(base):]
            if tail.isdigit():
                nums.append(int(tail))
    return str(max(nums, default=0) + 1)


# ---------------------------------------------------------------------------
# Mutation framework
# ---------------------------------------------------------------------------


@contextmanager
def with_mutation(slug: str, *, question: int | None = None) -> Iterator[Graph]:
    """Context manager that loads, yields the graph for in-memory mutation,
    then validates (per-Q if ``question`` is set, otherwise no validation),
    and saves.

    On validation failure, raises ``typer.Exit(1)`` after printing a
    structured violation report. The on-disk file is *not* updated."""
    g = load_submission_graph(slug, merge_shared=True)
    yield g

    if question is not None:
        report = validate(g, mode="per_question", question=question)
        if not report.conforms:
            err_console.print(f"[red]rejected: Q{question} validation failed[/red]")
            for v in report.violations:
                err_console.print(f"  • {v.message}  (focus={v.focus_node})")
            raise typer.Exit(code=1)

    save_submission_graph_separating_shared(g, slug)


def report_validation(report: ValidationReport, *, label: str = "") -> None:
    if report.conforms:
        console.print(f"[green]✓ {label or 'OK'}[/green]")
        return
    console.print(f"[red]✗ {label or 'FAIL'}[/red]: {report.violation_count} violation(s)")
    for v in report.violations:
        console.print(f"  • {v.message}")
        if v.result_path:
            console.print(f"    path: {v.result_path}")
        console.print(f"    focus: {v.focus_node}")


# ---------------------------------------------------------------------------
# Shared registry IO
# ---------------------------------------------------------------------------


def shared_path(filename: str) -> Path:
    return SHARED_DIR / filename


def load_shared_registry(filename: str) -> Graph:
    p = shared_path(filename)
    g = Graph()
    if p.exists():
        g.parse(str(p), format="turtle")
    return g


def save_shared_registry(g: Graph, filename: str) -> None:
    p = shared_path(filename)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(canonicalize_turtle(g))


__all__ = [
    "ExtractionTrace",
    "TRACE_FILENAME",
    "console",
    "err_console",
    "trace_path",
    "load_trace",
    "save_trace",
    "now_iso",
    "load_submission_graph",
    "save_submission_graph_separating_shared",
    "get_submission_iri",
    "get_submission_version",
    "next_local_id",
    "with_mutation",
    "report_validation",
    "shared_path",
    "load_shared_registry",
    "save_shared_registry",
]
