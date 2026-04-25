"""
mgj.canonicalize
----------------
Deterministic RDF canonicalization for content-addressable graphs.

Two outputs:

- ``canonical_nt(g)`` — sorted N-Triples string. Hash-stable: any two
  isomorphic graphs produce byte-identical output. Use for content
  hashing and equality comparisons.

- ``canonicalize_turtle(g)`` — stable Turtle string for human-readable
  storage. Uses rdflib's ``longturtle`` serializer over a URDNA2015-
  canonicalized graph, with mgj's canonical prefixes pre-bound. Within
  a given rdflib version this is byte-stable.

The two outputs serve different purposes: the N-Triples hash is the
authoritative content identity (rdflib-version independent); the Turtle
form is what we store on disk.

Round-trip invariant:
    parse(canonicalize_turtle(g)) hashes to graph_hash(g)

Idempotence invariant:
    canonicalize_turtle(parse(canonicalize_turtle(g))) == canonicalize_turtle(g)

Both are exercised by tests/test_canonicalize.py.
"""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path

from rdflib import Graph
from rdflib.compare import to_canonical_graph
from rdflib.namespace import DCTERMS, FOAF, RDF, RDFS, SKOS, XSD

from mgj.namespaces import MGJ, PROV


def _canonical_graph_with_prefixes(g: Graph) -> Graph:
    """URDNA2015-canonicalize and re-bind the mgj canonical prefixes.

    ``to_canonical_graph`` returns a read-only aggregate, so we copy its
    triples into a fresh, mutable Graph and bind our standard prefixes
    on the copy. This yields readable Turtle that uses our prefixes
    instead of auto-generated ``ns1``/``ns2`` placeholders.
    """
    canonical = to_canonical_graph(g)
    cg = Graph()
    for t in canonical:
        cg.add(t)
    cg.bind("mgj", MGJ, override=True)
    cg.bind("foaf", FOAF, override=True)
    cg.bind("dcterms", DCTERMS, override=True)
    cg.bind("skos", SKOS, override=True)
    cg.bind("prov", PROV, override=True)
    cg.bind("rdfs", RDFS, override=True)
    cg.bind("rdf", RDF, override=True)
    cg.bind("xsd", XSD, override=True)
    return cg


def canonical_nt(g: Graph) -> str:
    """Sorted N-Triples form of ``g``. Byte-stable for isomorphic graphs.

    Used for content hashing. The output is sorted line-by-line on the
    URDNA2015-canonicalized graph, so reordering the source has no effect
    and blank nodes get deterministic labels.
    """
    cg = to_canonical_graph(g)
    raw = cg.serialize(format="nt")
    lines = [line for line in raw.splitlines() if line.strip()]
    return "\n".join(sorted(lines)) + "\n"


def graph_hash(g: Graph, *, algorithm: str = "sha256") -> str:
    """Hex digest of the canonical N-Triples form. Default: SHA-256.

    Two isomorphic graphs produce identical hashes regardless of triple
    insertion order, blank node labeling, or prefix choices in the
    Turtle source.
    """
    if algorithm != "sha256":
        raise ValueError(f"unsupported algorithm: {algorithm!r}")
    return sha256(canonical_nt(g).encode("utf-8")).hexdigest()


def canonicalize_turtle(g: Graph) -> str:
    """Stable Turtle serialization with canonical mgj prefixes.

    Within a given rdflib version, this is byte-stable: the same graph
    always produces the same string. Across rdflib versions we make no
    guarantee — use ``graph_hash`` for cross-version content addressing.
    """
    cg = _canonical_graph_with_prefixes(g)
    return cg.serialize(format="longturtle")


def canonicalize_file(path: str | Path) -> bool:
    """Parse ``path``, canonicalize, write back. Returns True if changed.

    Idempotent: calling twice in succession on the same file produces no
    change on the second call. Use this after every CLI mutation so the
    on-disk Turtle stays in canonical form regardless of how triples
    were added.
    """
    p = Path(path)
    g = Graph()
    g.parse(str(p), format="turtle")
    canonical = canonicalize_turtle(g)
    if not p.exists() or p.read_text() != canonical:
        p.write_text(canonical)
        return True
    return False


def save_instance(g: Graph, path: str | Path) -> None:
    """Write ``g`` to ``path`` in canonical Turtle form.

    Use from CLI command handlers in place of ``g.serialize(...)`` to
    guarantee on-disk canonicality.
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(canonicalize_turtle(g))


__all__ = [
    "canonical_nt",
    "graph_hash",
    "canonicalize_turtle",
    "canonicalize_file",
    "save_instance",
]
