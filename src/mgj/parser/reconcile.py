"""
mgj.parser.reconcile
--------------------
Reconciliation of new parser output against an existing instance graph.

Today's invariant: parser-output entities for an *unaffirmed* question
are dropped before re-extraction. Affirmed questions are protected by
the affirmation guard in ``extract.run_extraction`` (the call is
refused unless force=True), so reconciliation never touches affirmed
entities.

Drop semantics — for question Qi, remove every entity whose:
- rdf:type matches the question's primary class, AND
- carries a ``mgj:extractedBy`` link (i.e. was parser-emitted, not
  hand-added via the CLI).

The Submission's link triple to the entity is also removed.
"""

from __future__ import annotations

from rdflib import Graph, URIRef
from rdflib.namespace import RDF

from mgj.namespaces import MGJ

# Per-question owners: (entity OWL class, link predicate from Submission).
QUESTION_OWNERS: dict[int, list[tuple[str, str]]] = {
    2: [("Stakeholder", "hasStakeholder")],
    3: [("EnvironmentalFactor", "hasEnvironmentalFactor")],
    4: [("ConstitutionalElement", "hasConstitutionalElement")],
    5: [("FieldSite", "hasFieldSite")],
    6: [],  # Q6 sets singleton properties on the Submission, not n-ary entities.
    7: [("OriginEvent", "hasOriginEvent")],
    8: [("EvolutionMechanism", "hasEvolutionMechanism")],
    9: [("Reference", "hasReference")],
}


def drop_parser_output_for_question(g: Graph, sub: URIRef, question: int) -> None:
    """Remove parser-output entities for ``question`` from ``g``.

    "Parser-output" means the entity carries an ``mgj:extractedBy``
    triple. Hand-added entities (which lack that triple) are preserved.
    """
    owners = QUESTION_OWNERS.get(question, [])

    # Find every parser-emitted entity once, then dispatch by class.
    parser_entities = list(g.subjects(predicate=MGJ.extractedBy))

    # Remove primary entities of the owned classes for this question.
    owned_classes = {MGJ[cls] for cls, _ in owners}
    link_preds_by_class = {MGJ[cls]: MGJ[link] for cls, link in owners}

    for entity in parser_entities:
        types = set(g.objects(entity, RDF.type))
        matched_class = next(iter(types & owned_classes), None)
        if matched_class is None:
            continue
        # Drop the Submission's link to this entity, then all triples about it.
        g.remove((sub, link_preds_by_class[matched_class], entity))
        for p, o in list(g.predicate_objects(entity)):
            g.remove((entity, p, o))

    # Drop any orphaned UnresolvedAgent that was a parser output for this Qi
    # and is no longer referenced by anything.
    if question in QUESTION_OWNERS:
        _drop_orphan_unresolved_agents(g)


def _drop_orphan_unresolved_agents(g: Graph) -> None:
    """An UnresolvedAgent referenced by no Stakeholder, OriginEvent, or
    other entity is orphaned — drop it. Only parser-output (mgj:extractedBy)
    UAs are eligible for dropping."""
    for ua in list(g.subjects(RDF.type, MGJ.UnresolvedAgent)):
        if (ua, MGJ.extractedBy, None) not in g:
            continue
        referenced = (
            any(g.subjects(MGJ.stakeholderAgent, ua))
            or any(g.subjects(MGJ.originParticipant, ua))
            or any(g.subjects(MGJ.authoredBy, ua))
        )
        if referenced:
            continue
        for p, o in list(g.predicate_objects(ua)):
            g.remove((ua, p, o))


__all__ = ["drop_parser_output_for_question", "QUESTION_OWNERS"]
