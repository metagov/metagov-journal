"""M2: Pydantic model construction and required-field enforcement."""

from __future__ import annotations

from datetime import date

import pytest
from pydantic import ValidationError

from mgj.models import (
    ConstitutionalElement,
    EnvironmentalFactor,
    EvolutionMechanism,
    FieldSite,
    Institution,
    LegalContext,
    OriginEvent,
    Person,
    Reference,
    Stakeholder,
    Submission,
)


def test_person_minimal() -> None:
    p = Person(iri="https://journal.metagov.org/people/alice", name="Alice")
    assert p.name == "Alice"


def test_person_rejects_empty_name() -> None:
    with pytest.raises(ValidationError):
        Person(iri="https://journal.metagov.org/people/x", name="")


def test_environmental_factor_modality_literal() -> None:
    ef = EnvironmentalFactor(
        iri="https://journal.metagov.org/submissions/x/v1/factor/1",
        modality="Law",
        description="Operates under Metagov's 501(c)(3) status.",
    )
    assert ef.modality == "Law"


def test_environmental_factor_rejects_unknown_modality() -> None:
    with pytest.raises(ValidationError):
        EnvironmentalFactor(
            iri="https://journal.metagov.org/submissions/x/v1/factor/1",
            modality="Bureaucracy",  # not a Lessig modality
            description="Some force",
        )


def test_constitutional_element_rejects_unknown_type() -> None:
    with pytest.raises(ValidationError):
        ConstitutionalElement(
            iri="https://journal.metagov.org/submissions/x/v1/constitution/1",
            label="Charter",
            description="Founding charter",
            element_type="Constitution",  # not in our closed scheme
        )


def test_legal_context_rejects_unknown_relationship() -> None:
    with pytest.raises(ValidationError):
        LegalContext(
            iri="https://journal.metagov.org/submissions/x/v1/legal/1",
            host_organization_iri="https://journal.metagov.org/orgs/metagov",
            legal_relationship="Affiliate",  # not in closed scheme
            description="Operates under Metagov.",
        )


def _build_complete_submission() -> Submission:
    """A minimum-passing submission used by serialize+validate tests."""
    return Submission(
        iri="https://journal.metagov.org/submissions/test/v1.0.0",
        institution_iri="https://journal.metagov.org/institutions/test",
        submission_date=date(2026, 4, 25),
        submission_version="1.0.0",
        author_iri="https://journal.metagov.org/people/alice",
        author_role="founder",
        author_disclosure="Author is a founder; potential bias toward favorable framing.",
        q1_narrative="Purpose narrative.",
        q2_narrative="Stakeholder narrative.",
        q3_narrative="Environment narrative.",
        q4_narrative="Constitution narrative.",
        q5_narrative="Field site narrative.",
        q6_narrative="Author relationship narrative.",
        q7_narrative="Origins narrative.",
        q8_narrative="Evolution narrative.",
        q9_narrative="References narrative.",
        stakeholders=[
            Stakeholder(
                iri="https://journal.metagov.org/submissions/test/v1.0.0/stakeholder/1",
                agent_iri="https://journal.metagov.org/people/alice",
                role_label="Founder",
                role_iri="https://journal.metagov.org/roles/founder",
            )
        ],
        environmental_factors=[
            EnvironmentalFactor(
                iri="https://journal.metagov.org/submissions/test/v1.0.0/factor/1",
                modality="Law",
                description="Subject to nonprofit regulation.",
            )
        ],
        constitutional_elements=[
            ConstitutionalElement(
                iri="https://journal.metagov.org/submissions/test/v1.0.0/constitution/1",
                label="Charter",
                description="Founding charter document.",
                element_type="Bylaw",
            )
        ],
        field_sites=[
            FieldSite(
                iri="https://journal.metagov.org/submissions/test/v1.0.0/fieldsite/1",
                label="GitHub repo",
                url="https://github.com/example/repo",
            )
        ],
        origin_events=[
            OriginEvent(
                iri="https://journal.metagov.org/submissions/test/v1.0.0/origin/1",
                label="Founding meeting",
                description="Founders convened.",
                date=date(2024, 1, 1),
                participant_iris=["https://journal.metagov.org/people/alice"],
            )
        ],
        evolution_mechanisms=[
            EvolutionMechanism(
                iri="https://journal.metagov.org/submissions/test/v1.0.0/evolution/1",
                label="PR-driven amendment",
                description="Changes via GitHub PR.",
            )
        ],
        references=[
            Reference(
                iri="https://journal.metagov.org/submissions/test/v1.0.0/reference/1",
                title="Founding paper",
                identifier="https://example.org/founding",
                creators=["Alice"],
                date="2024",
            )
        ],
    )


def test_complete_submission_constructs() -> None:
    s = _build_complete_submission()
    assert len(s.stakeholders) == 1
    assert s.legal_context is None
    assert len(s.unresolved_agents) == 0
