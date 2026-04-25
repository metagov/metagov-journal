"""
mgj.graph
---------
RDFLib graph loading helpers.

Responsibilities:
- Resolve repo-relative paths to ontology, shapes, and shared registries.
- Load instance Turtle files, optionally merging shared registries and the
  ontology.
- Provide a SPARQL convenience wrapper with standard prefixes.

Path resolution is rooted at the repository, not the current working
directory: helpers walk up from this file's location to find the project
root.
"""

from __future__ import annotations

from pathlib import Path

from rdflib import Graph
from rdflib.plugins.sparql.processor import SPARQLResult

from mgj.namespaces import SPARQL_PREFIXES

_HERE = Path(__file__).parent.resolve()
_PROJECT_ROOT = _HERE.parent.parent  # src/mgj -> src -> repo root

ONTOLOGY_PATH = _PROJECT_ROOT / "ontology" / "mgj.ttl"
SHAPES_DIR = _PROJECT_ROOT / "ontology" / "shapes"
SYSTEM_SHAPES_PATH = SHAPES_DIR / "system.ttl"
PER_QUESTION_SHAPES_DIR = SHAPES_DIR / "per-question"
SHARED_DIR = _PROJECT_ROOT / "shared"
SUBMISSIONS_DIR = _PROJECT_ROOT / "submissions"


def project_root() -> Path:
    return _PROJECT_ROOT


def submission_dir(slug: str) -> Path:
    return SUBMISSIONS_DIR / slug


def submission_instance_path(slug: str) -> Path:
    return submission_dir(slug) / "instance.ttl"


def per_question_shapes_path(question: int) -> Path:
    """Return the path to a per-question shapes file (q1..q9)."""
    if not 1 <= question <= 9:
        raise ValueError(f"question must be in 1..9, got {question}")
    matches = sorted(PER_QUESTION_SHAPES_DIR.glob(f"q{question}-*.ttl"))
    if not matches:
        raise FileNotFoundError(
            f"no shapes file found for question {question} in {PER_QUESTION_SHAPES_DIR}"
        )
    if len(matches) > 1:
        raise RuntimeError(
            f"multiple shapes files match q{question}-*.ttl: {matches}"
        )
    return matches[0]


def load_ontology() -> Graph:
    g = Graph()
    g.parse(str(ONTOLOGY_PATH), format="turtle")
    return g


def load_system_shapes() -> Graph:
    g = Graph()
    g.parse(str(SYSTEM_SHAPES_PATH), format="turtle")
    return g


def load_per_question_shapes(question: int) -> Graph:
    g = Graph()
    g.parse(str(per_question_shapes_path(question)), format="turtle")
    return g


def load_shared() -> Graph:
    """Load every .ttl file under shared/ into one graph."""
    g = Graph()
    if SHARED_DIR.is_dir():
        for ttl in sorted(SHARED_DIR.glob("*.ttl")):
            g.parse(str(ttl), format="turtle")
    return g


def load_instance(path: str | Path, *, with_shared: bool = True) -> Graph:
    """Load a submission instance.ttl, optionally merged with shared registries."""
    g = Graph()
    if with_shared:
        for ttl in sorted(SHARED_DIR.glob("*.ttl")) if SHARED_DIR.is_dir() else []:
            g.parse(str(ttl), format="turtle")
    g.parse(str(path), format="turtle")
    return g


def sparql_select(graph: Graph, query: str) -> list[dict[str, str]]:
    """Run a SPARQL SELECT, returning rows as dicts of variable→string."""
    result: SPARQLResult = graph.query(SPARQL_PREFIXES + query)
    rows: list[dict[str, str]] = []
    for row in result:
        rows.append(
            {
                str(var): (str(row[var]) if row[var] is not None else "")
                for var in result.vars
            }
        )
    return rows
