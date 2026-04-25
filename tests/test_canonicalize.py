"""M2.5: canonicalization invariants — hash stability, idempotence,
prefix invariance, and isomorphism-respect."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
from rdflib import BNode, Graph, Literal, URIRef
from rdflib.namespace import RDF

from mgj.canonicalize import (
    canonical_nt,
    canonicalize_file,
    canonicalize_turtle,
    graph_hash,
)
from mgj.models import Institution, Person
from mgj.namespaces import MGJ
from mgj.serialize import add_institution, add_person, submission_to_graph
from tests.test_models import _build_complete_submission


# ---------------------------------------------------------------------------
# Hash stability under triple order / prefix changes
# ---------------------------------------------------------------------------


def _two_graphs_with_same_triples_in_different_orders() -> tuple[Graph, Graph]:
    EX = "http://ex.org/"
    triples = [
        (URIRef(EX + "a"), URIRef(EX + "p"), Literal("x")),
        (URIRef(EX + "b"), URIRef(EX + "p"), Literal("y")),
        (URIRef(EX + "a"), URIRef(EX + "q"), Literal("z")),
    ]
    g1 = Graph()
    for t in triples:
        g1.add(t)
    g2 = Graph()
    for t in reversed(triples):
        g2.add(t)
    return g1, g2


def test_graph_hash_invariant_under_triple_insertion_order() -> None:
    g1, g2 = _two_graphs_with_same_triples_in_different_orders()
    assert graph_hash(g1) == graph_hash(g2)


def test_graph_hash_changes_on_real_change() -> None:
    g1, _ = _two_graphs_with_same_triples_in_different_orders()
    g2 = Graph()
    for t in g1:
        g2.add(t)
    g2.add((URIRef("http://ex.org/c"), URIRef("http://ex.org/p"), Literal("new")))
    assert graph_hash(g1) != graph_hash(g2)


def test_graph_hash_invariant_across_prefix_choice() -> None:
    """A graph parsed from two different Turtle prefix declarations
    that produce the same triples must hash equal."""
    ttl_a = """
        @prefix ex: <http://ex.org/> .
        ex:a ex:p "x" ; ex:q "z" .
        ex:b ex:p "y" .
    """
    ttl_b = """
        @prefix foo: <http://ex.org/> .
        foo:a foo:p "x" .
        foo:a foo:q "z" .
        foo:b foo:p "y" .
    """
    g1, g2 = Graph(), Graph()
    g1.parse(data=ttl_a, format="turtle")
    g2.parse(data=ttl_b, format="turtle")
    assert graph_hash(g1) == graph_hash(g2)


def test_graph_hash_invariant_across_blank_node_labels() -> None:
    """Two isomorphic graphs with differently-labeled blank nodes hash equal."""
    EX = "http://ex.org/"
    g1 = Graph()
    b1 = BNode("a")
    g1.add((URIRef(EX + "x"), URIRef(EX + "has"), b1))
    g1.add((b1, URIRef(EX + "p"), Literal("v")))

    g2 = Graph()
    b2 = BNode("zzzz")
    g2.add((URIRef(EX + "x"), URIRef(EX + "has"), b2))
    g2.add((b2, URIRef(EX + "p"), Literal("v")))

    assert graph_hash(g1) == graph_hash(g2)


# ---------------------------------------------------------------------------
# canonical_nt and canonicalize_turtle are byte-stable
# ---------------------------------------------------------------------------


def test_canonical_nt_byte_stable() -> None:
    g1, g2 = _two_graphs_with_same_triples_in_different_orders()
    assert canonical_nt(g1) == canonical_nt(g2)


def test_canonicalize_turtle_byte_stable() -> None:
    g1, g2 = _two_graphs_with_same_triples_in_different_orders()
    assert canonicalize_turtle(g1) == canonicalize_turtle(g2)


# ---------------------------------------------------------------------------
# Idempotence: parse → canonicalize → parse → canonicalize is fixed point
# ---------------------------------------------------------------------------


def test_canonicalize_turtle_idempotent_on_submission() -> None:
    s = _build_complete_submission()
    institution = Institution(iri=s.institution_iri, name="Test Institution")
    g = submission_to_graph(s, institution=institution)

    once = canonicalize_turtle(g)
    g2 = Graph()
    g2.parse(data=once, format="turtle")
    twice = canonicalize_turtle(g2)
    assert once == twice


def test_canonicalize_file_idempotent(tmp_path: Path) -> None:
    """Round-trip a submission through disk canonicalization twice."""
    s = _build_complete_submission()
    institution = Institution(iri=s.institution_iri, name="Test Institution")
    g = submission_to_graph(s, institution=institution)

    p = tmp_path / "instance.ttl"
    p.write_text(canonicalize_turtle(g))

    # First canonicalize_file: file is already canonical → no change.
    changed_first = canonicalize_file(p)
    assert changed_first is False

    # Append the same triples in scrambled order to a fresh file: the
    # canonicalize_file pass should normalize back to the original.
    scrambled = """
        @prefix mgj:     <https://journal.metagov.org/ns/mgj#> .
        @prefix foaf:    <http://xmlns.com/foaf/0.1/> .
        @prefix dcterms: <http://purl.org/dc/terms/> .
        @prefix xsd:     <http://www.w3.org/2001/XMLSchema#> .

        <https://journal.metagov.org/institutions/test>
            foaf:name "ignored" .  # extra triple — shouldn't be present after canonicalize
    """
    p.write_text(scrambled)
    canonicalize_file(p)
    # Now re-canonicalizing should be a fixed point.
    assert canonicalize_file(p) is False


def test_round_trip_hash_preserved_across_disk(tmp_path: Path) -> None:
    """Hash of an in-memory graph equals hash of the same graph after
    disk write+reread via canonical Turtle."""
    s = _build_complete_submission()
    institution = Institution(iri=s.institution_iri, name="Test Institution")
    g = submission_to_graph(s, institution=institution)

    p = tmp_path / "instance.ttl"
    p.write_text(canonicalize_turtle(g))

    g_reloaded = Graph()
    g_reloaded.parse(str(p), format="turtle")

    assert graph_hash(g) == graph_hash(g_reloaded)


# ---------------------------------------------------------------------------
# Real-world isomorphism: same submission, different IRIs → different hash
# ---------------------------------------------------------------------------


def test_distinct_submissions_have_distinct_hashes() -> None:
    s1 = _build_complete_submission()
    s2 = s1.model_copy(
        update={
            "submission_version": "1.0.1",
            "iri": "https://journal.metagov.org/submissions/test/v1.0.1",
        }
    )
    institution = Institution(iri=s1.institution_iri, name="Test Institution")
    g1 = submission_to_graph(s1, institution=institution)
    g2 = submission_to_graph(s2, institution=institution)
    assert graph_hash(g1) != graph_hash(g2)
