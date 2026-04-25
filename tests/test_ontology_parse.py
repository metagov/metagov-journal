"""M1 acceptance: ontology and SHACL shape graphs parse, and validating an
empty instance graph against the system shapes succeeds in returning a
report (the report is expected to flag missing required fields when given
an empty graph; the goal here is to confirm pyshacl can load and run the
shapes against the ontology, not that a degenerate instance passes)."""

from __future__ import annotations

from pathlib import Path

import pyshacl
from rdflib import Graph

REPO = Path(__file__).resolve().parents[1]
ONTOLOGY = REPO / "ontology" / "mgj.ttl"
SHAPES_DIR = REPO / "ontology" / "shapes"
PER_QUESTION_DIR = SHAPES_DIR / "per-question"
SYSTEM_SHAPES = SHAPES_DIR / "system.ttl"


def test_ontology_parses() -> None:
    g = Graph()
    g.parse(ONTOLOGY, format="turtle")
    assert len(g) > 0


def test_system_shapes_parse() -> None:
    g = Graph()
    g.parse(SYSTEM_SHAPES, format="turtle")
    assert len(g) > 0


def test_per_question_shapes_parse() -> None:
    files = sorted(PER_QUESTION_DIR.glob("q*.ttl"))
    assert len(files) == 9, f"expected 9 per-question shape files, found {len(files)}"
    for f in files:
        g = Graph()
        g.parse(f, format="turtle")
        assert len(g) > 0, f"empty graph parsed from {f}"


def test_pyshacl_runs_against_empty_instance() -> None:
    """pyshacl can load shapes + ontology and validate an empty data graph.

    We do not assert validation passes — an empty graph trivially has no
    targets, so pyshacl should report conforms=True. The point is the
    machinery loads.
    """
    shapes = Graph()
    shapes.parse(SYSTEM_SHAPES, format="turtle")
    for f in sorted(PER_QUESTION_DIR.glob("q*.ttl")):
        shapes.parse(f, format="turtle")

    ontology = Graph()
    ontology.parse(ONTOLOGY, format="turtle")

    data = Graph()  # empty

    conforms, _report_graph, report_text = pyshacl.validate(
        data_graph=data,
        shacl_graph=shapes,
        ont_graph=ontology,
        inference="none",
        meta_shacl=False,
        advanced=True,
    )
    assert conforms is True, f"empty graph should trivially conform; got: {report_text}"
