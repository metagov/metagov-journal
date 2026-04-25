"""M2: Pydantic Submission → rdflib Graph serialization."""

from __future__ import annotations

from datetime import date

from rdflib import Literal, URIRef
from rdflib.namespace import FOAF, RDF

from mgj.models import (
    EnvironmentalFactor,
    Institution,
    LegalContext,
    Organization,
    Person,
    Stakeholder,
    Submission,
)
from mgj.namespaces import MGJ
from mgj.serialize import (
    add_institution,
    add_organization,
    add_person,
    submission_to_graph,
)
from tests.test_models import _build_complete_submission


def test_serialize_minimum_submission_round_trips_via_sparql() -> None:
    s = _build_complete_submission()
    g = submission_to_graph(s)

    # Submission node has correct rdf:type
    sub = URIRef(s.iri)
    assert (sub, RDF.type, MGJ.Submission) in g

    # Per-question narratives present
    assert (sub, MGJ.q1Narrative, Literal("Purpose narrative.")) in g
    assert (sub, MGJ.q9Narrative, Literal("References narrative.")) in g

    # Stakeholder edge present
    sh = URIRef(s.stakeholders[0].iri)
    assert (sub, MGJ.hasStakeholder, sh) in g
    assert (sh, RDF.type, MGJ.Stakeholder) in g

    # EnvironmentalFactor typed by Lessig modality
    ef = URIRef(s.environmental_factors[0].iri)
    assert (ef, MGJ.lessigModality, MGJ.Law) in g


def test_serialize_includes_optional_legal_context() -> None:
    s = _build_complete_submission()
    s = s.model_copy(
        update={
            "legal_context": LegalContext(
                iri="https://journal.metagov.org/submissions/test/v1.0.0/legal/1",
                host_organization_iri="https://journal.metagov.org/orgs/metagov",
                legal_relationship="FiscalSponsor",
                description="Fiscal sponsorship under Metagov.",
                funding_reference="GRANT-2024-1",
            )
        }
    )
    g = submission_to_graph(s)
    sub = URIRef(s.iri)
    lc = URIRef(s.legal_context.iri)
    assert (sub, MGJ.operatesUnder, lc) in g
    assert (lc, MGJ.legalRelationship, MGJ.FiscalSponsor) in g
    assert (lc, MGJ.fundingReference, Literal("GRANT-2024-1")) in g


def test_add_person_and_organization_emit_foaf_types() -> None:
    from rdflib import Graph

    g = Graph()
    p = Person(iri="https://journal.metagov.org/people/alice", name="Alice Example")
    o = Organization(iri="https://journal.metagov.org/orgs/metagov", name="Metagov")
    add_person(g, p)
    add_organization(g, o)
    assert (URIRef(p.iri), RDF.type, FOAF.Person) in g
    assert (URIRef(o.iri), RDF.type, FOAF.Organization) in g
    assert (URIRef(p.iri), FOAF.name, Literal("Alice Example")) in g


def test_add_institution() -> None:
    from rdflib import Graph

    g = Graph()
    i = Institution(
        iri="https://journal.metagov.org/institutions/test",
        name="Test Institution",
        description="A test.",
    )
    add_institution(g, i)
    assert (URIRef(i.iri), RDF.type, MGJ.Institution) in g
    assert (URIRef(i.iri), MGJ.institutionName, Literal("Test Institution")) in g
