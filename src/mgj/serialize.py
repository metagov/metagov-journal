"""
mgj.serialize
-------------
Pydantic Submission → rdflib Graph.

One-direction serialization. The graph is the source of truth at rest;
Pydantic models are the typed authoring/parser interface that the CLI
and parser layers use to construct content. The CLI's read paths use
SPARQL against the loaded graph rather than re-deserializing the whole
submission into a model.

Output is deterministic for a given input model: triples are added in a
fixed order, and rdflib's Turtle serializer normalizes prefix ordering
in the final output. This is a prerequisite for the compilation
determinism invariant.
"""

from __future__ import annotations

from rdflib import Graph, Literal, URIRef
from rdflib.namespace import DCTERMS, FOAF, RDF, RDFS, SKOS, XSD

from mgj.models import (
    ConstitutionalElement,
    EnvironmentalFactor,
    EvolutionMechanism,
    FieldSite,
    Institution,
    LegalContext,
    OriginEvent,
    Organization,
    Person,
    Reference,
    Stakeholder,
    Submission,
    UnresolvedAgent,
)
from mgj.namespaces import MGJ


def _u(iri: str) -> URIRef:
    return URIRef(iri)


def _mgj(local: str) -> URIRef:
    return MGJ[local]


# ---------------------------------------------------------------------------
# Shared agents
# ---------------------------------------------------------------------------


def add_person(g: Graph, p: Person) -> None:
    node = _u(p.iri)
    g.add((node, RDF.type, FOAF.Person))
    g.add((node, FOAF.name, Literal(p.name)))
    if p.homepage is not None:
        g.add((node, FOAF.homepage, Literal(str(p.homepage), datatype=XSD.anyURI)))


def add_organization(g: Graph, o: Organization) -> None:
    node = _u(o.iri)
    g.add((node, RDF.type, FOAF.Organization))
    g.add((node, FOAF.name, Literal(o.name)))
    if o.homepage is not None:
        g.add((node, FOAF.homepage, Literal(str(o.homepage), datatype=XSD.anyURI)))


def add_unresolved_agent(g: Graph, u: UnresolvedAgent) -> None:
    node = _u(u.iri)
    g.add((node, RDF.type, _mgj("UnresolvedAgent")))
    g.add((node, _mgj("unresolvedLabel"), Literal(u.label)))


# ---------------------------------------------------------------------------
# Institution
# ---------------------------------------------------------------------------


def add_institution(g: Graph, i: Institution) -> None:
    node = _u(i.iri)
    g.add((node, RDF.type, _mgj("Institution")))
    g.add((node, _mgj("institutionName"), Literal(i.name)))
    if i.description is not None:
        g.add((node, _mgj("institutionDescription"), Literal(i.description)))


# ---------------------------------------------------------------------------
# Per-question entities
# ---------------------------------------------------------------------------


def add_stakeholder(g: Graph, s: Stakeholder) -> None:
    node = _u(s.iri)
    g.add((node, RDF.type, _mgj("Stakeholder")))
    g.add((node, _mgj("stakeholderAgent"), _u(s.agent_iri)))
    g.add((node, _mgj("roleLabel"), Literal(s.role_label)))
    if s.role_iri is not None:
        g.add((node, _mgj("hasRole"), _u(s.role_iri)))
    if s.responsibilities is not None:
        g.add((node, _mgj("stakeholderResponsibilities"), Literal(s.responsibilities)))


def add_field_site(g: Graph, f: FieldSite) -> None:
    node = _u(f.iri)
    g.add((node, RDF.type, _mgj("FieldSite")))
    g.add((node, _mgj("fieldSiteLabel"), Literal(f.label)))
    if f.url is not None:
        g.add((node, _mgj("fieldSiteURL"), Literal(str(f.url), datatype=XSD.anyURI)))
    if f.description is not None:
        g.add((node, _mgj("fieldSiteDescription"), Literal(f.description)))


def add_environmental_factor(g: Graph, e: EnvironmentalFactor) -> None:
    node = _u(e.iri)
    g.add((node, RDF.type, _mgj("EnvironmentalFactor")))
    g.add((node, _mgj("lessigModality"), _mgj(e.modality)))
    g.add((node, _mgj("factorDescription"), Literal(e.description)))


def add_constitutional_element(g: Graph, c: ConstitutionalElement) -> None:
    node = _u(c.iri)
    g.add((node, RDF.type, _mgj("ConstitutionalElement")))
    g.add((node, _mgj("elementLabel"), Literal(c.label)))
    g.add((node, _mgj("elementDescription"), Literal(c.description)))
    g.add((node, _mgj("elementType"), _mgj(c.element_type)))
    if c.source_url is not None:
        g.add(
            (node, _mgj("elementSourceURL"), Literal(str(c.source_url), datatype=XSD.anyURI))
        )


def add_origin_event(g: Graph, o: OriginEvent) -> None:
    node = _u(o.iri)
    g.add((node, RDF.type, _mgj("OriginEvent")))
    g.add((node, _mgj("originLabel"), Literal(o.label)))
    g.add((node, _mgj("originDescription"), Literal(o.description)))
    if o.date is not None:
        g.add((node, _mgj("originDate"), Literal(o.date.isoformat(), datatype=XSD.date)))
    for p_iri in o.participant_iris:
        g.add((node, _mgj("originParticipant"), _u(p_iri)))


def add_evolution_mechanism(g: Graph, m: EvolutionMechanism) -> None:
    node = _u(m.iri)
    g.add((node, RDF.type, _mgj("EvolutionMechanism")))
    g.add((node, _mgj("mechanismLabel"), Literal(m.label)))
    g.add((node, _mgj("mechanismDescription"), Literal(m.description)))


def add_reference(g: Graph, r: Reference) -> None:
    node = _u(r.iri)
    g.add((node, RDF.type, _mgj("Reference")))
    g.add((node, DCTERMS.title, Literal(r.title)))
    g.add((node, DCTERMS.identifier, Literal(r.identifier)))
    if r.date is not None:
        g.add((node, DCTERMS.date, Literal(r.date)))
    for c in r.creators:
        g.add((node, DCTERMS.creator, Literal(c)))


def add_legal_context(g: Graph, l: LegalContext) -> None:
    node = _u(l.iri)
    g.add((node, RDF.type, _mgj("LegalContext")))
    g.add((node, _mgj("hostOrganization"), _u(l.host_organization_iri)))
    g.add((node, _mgj("legalRelationship"), _mgj(l.legal_relationship)))
    g.add((node, _mgj("legalContextDescription"), Literal(l.description)))
    if l.funding_reference is not None:
        g.add((node, _mgj("fundingReference"), Literal(l.funding_reference)))


# ---------------------------------------------------------------------------
# Submission
# ---------------------------------------------------------------------------


def add_submission(g: Graph, s: Submission) -> None:
    node = _u(s.iri)
    g.add((node, RDF.type, _mgj("Submission")))
    g.add((node, _mgj("documents"), _u(s.institution_iri)))
    g.add(
        (node, _mgj("submissionDate"), Literal(s.submission_date.isoformat(), datatype=XSD.date))
    )
    g.add((node, _mgj("submissionVersion"), Literal(s.submission_version)))

    # Q6 author disclosure
    if s.author_iri is not None:
        g.add((node, _mgj("authoredBy"), _u(s.author_iri)))
    if s.author_role is not None:
        g.add((node, _mgj("authorRole"), Literal(s.author_role)))
    if s.author_disclosure is not None:
        g.add((node, _mgj("authorDisclosure"), Literal(s.author_disclosure)))

    # Per-question narratives
    narratives = [
        (s.q1_narrative, "q1Narrative"),
        (s.q2_narrative, "q2Narrative"),
        (s.q3_narrative, "q3Narrative"),
        (s.q4_narrative, "q4Narrative"),
        (s.q5_narrative, "q5Narrative"),
        (s.q6_narrative, "q6Narrative"),
        (s.q7_narrative, "q7Narrative"),
        (s.q8_narrative, "q8Narrative"),
        (s.q9_narrative, "q9Narrative"),
    ]
    for value, prop in narratives:
        if value is not None:
            g.add((node, _mgj(prop), Literal(value)))

    # Per-question entity links
    for st in s.stakeholders:
        add_stakeholder(g, st)
        g.add((node, _mgj("hasStakeholder"), _u(st.iri)))
    for ef in s.environmental_factors:
        add_environmental_factor(g, ef)
        g.add((node, _mgj("hasEnvironmentalFactor"), _u(ef.iri)))
    for ce in s.constitutional_elements:
        add_constitutional_element(g, ce)
        g.add((node, _mgj("hasConstitutionalElement"), _u(ce.iri)))
    for fs in s.field_sites:
        add_field_site(g, fs)
        g.add((node, _mgj("hasFieldSite"), _u(fs.iri)))
    for oe in s.origin_events:
        add_origin_event(g, oe)
        g.add((node, _mgj("hasOriginEvent"), _u(oe.iri)))
    for em in s.evolution_mechanisms:
        add_evolution_mechanism(g, em)
        g.add((node, _mgj("hasEvolutionMechanism"), _u(em.iri)))
    for ref in s.references:
        add_reference(g, ref)
        g.add((node, _mgj("hasReference"), _u(ref.iri)))

    if s.legal_context is not None:
        add_legal_context(g, s.legal_context)
        g.add((node, _mgj("operatesUnder"), _u(s.legal_context.iri)))

    for ua in s.unresolved_agents:
        add_unresolved_agent(g, ua)


def submission_to_graph(s: Submission, institution: Institution | None = None) -> Graph:
    """Serialize a Submission to a fresh, namespace-bound Graph.

    If ``institution`` is provided, the institution's triples are added
    (useful for tests / first-time scaffolding). In normal flows the
    institution lives in shared/ and is loaded from there.
    """
    g = Graph()
    g.bind("mgj", MGJ)
    g.bind("foaf", FOAF)
    g.bind("dcterms", DCTERMS)
    g.bind("skos", SKOS)
    g.bind("rdfs", RDFS)
    if institution is not None:
        add_institution(g, institution)
    add_submission(g, s)
    return g
