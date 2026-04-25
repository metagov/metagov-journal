"""M2: SHACL validation runs in per-question and system modes and returns
structured violations."""

from __future__ import annotations

from datetime import date

from rdflib import Graph, Literal, URIRef
from rdflib.namespace import RDF, SKOS

from mgj.models import (
    Institution,
    Organization,
    Person,
    Stakeholder,
    Submission,
)
from mgj.namespaces import MGJ, role_iri
from mgj.serialize import (
    add_institution,
    add_organization,
    add_person,
    submission_to_graph,
)
from mgj.validate import validate
from tests.test_models import _build_complete_submission


def _seed_shared(g: Graph) -> None:
    """Add the shared agents and role concept that the test submission references."""
    add_person(
        g,
        Person(iri="https://journal.metagov.org/people/alice", name="Alice Example"),
    )
    # Mint a role concept in mgj:RoleType
    role = URIRef(role_iri("founder"))
    g.add((role, RDF.type, SKOS.Concept))
    g.add((role, SKOS.inScheme, MGJ.RoleType))
    g.add((role, SKOS.prefLabel, Literal("Founder")))


def test_complete_submission_passes_system_shapes() -> None:
    s = _build_complete_submission()
    institution = Institution(iri=s.institution_iri, name="Test Institution")
    g = submission_to_graph(s, institution=institution)
    _seed_shared(g)
    report = validate(g, mode="system")
    assert report.conforms, str(report)


def test_missing_q5_fieldsite_fails_system_shapes() -> None:
    s = _build_complete_submission()
    s = s.model_copy(update={"field_sites": []})
    institution = Institution(iri=s.institution_iri, name="Test Institution")
    g = submission_to_graph(s, institution=institution)
    _seed_shared(g)
    report = validate(g, mode="system")
    assert not report.conforms
    msgs = " | ".join(v.message for v in report.violations)
    assert "FieldSite" in msgs


def test_missing_q3_factor_fails_system_shapes() -> None:
    s = _build_complete_submission()
    s = s.model_copy(update={"environmental_factors": []})
    institution = Institution(iri=s.institution_iri, name="Test Institution")
    g = submission_to_graph(s, institution=institution)
    _seed_shared(g)
    report = validate(g, mode="system")
    assert not report.conforms
    msgs = " | ".join(v.message for v in report.violations)
    assert "EnvironmentalFactor" in msgs


def test_unresolved_agent_fails_system_shapes() -> None:
    """A stakeholder pointing at an UnresolvedAgent must fail system validation."""
    s = _build_complete_submission()
    # Replace the stakeholder's agent with an UnresolvedAgent
    from mgj.models import UnresolvedAgent

    ua = UnresolvedAgent(
        iri="https://journal.metagov.org/submissions/test/v1.0.0/unresolved/1",
        label="the community",
    )
    new_stakeholder = s.stakeholders[0].model_copy(update={"agent_iri": ua.iri})
    s = s.model_copy(
        update={
            "stakeholders": [new_stakeholder],
            "unresolved_agents": [ua],
        }
    )
    institution = Institution(iri=s.institution_iri, name="Test Institution")
    g = submission_to_graph(s, institution=institution)
    _seed_shared(g)
    report = validate(g, mode="system")
    assert not report.conforms
    msgs = " | ".join(v.message for v in report.violations)
    assert "UnresolvedAgent" in msgs or "resolved" in msgs


def test_per_question_q3_well_formedness_passes() -> None:
    """An EnvironmentalFactor with a valid modality passes the Q3 inner-loop shape."""
    s = _build_complete_submission()
    institution = Institution(iri=s.institution_iri, name="Test Institution")
    g = submission_to_graph(s, institution=institution)
    _seed_shared(g)
    report = validate(g, mode="per_question", question=3)
    assert report.conforms, str(report)


def test_per_question_q3_rejects_factor_without_modality() -> None:
    """An EnvironmentalFactor with no Lessig modality fails Q3 inner-loop validation."""
    s = _build_complete_submission()
    institution = Institution(iri=s.institution_iri, name="Test Institution")
    g = submission_to_graph(s, institution=institution)
    _seed_shared(g)
    # Drop the lessigModality triple from the (one) EnvironmentalFactor
    factor_iri = URIRef(s.environmental_factors[0].iri)
    g.remove((factor_iri, MGJ.lessigModality, None))
    report = validate(g, mode="per_question", question=3)
    assert not report.conforms
    msgs = " | ".join(v.message for v in report.violations)
    assert "Lessig" in msgs or "lessigModality" in msgs.lower() or "modality" in msgs
