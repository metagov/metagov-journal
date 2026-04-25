"""
mgj.models
----------
Pydantic v2 models mirroring the mgj ontology (ontology/mgj.ttl).

Conventions
-----------
- Each model maps 1-to-1 to an OWL class.
- Required fields map to SHACL minCount >= 1; optional fields default to None
  or empty list.
- Controlled-vocabulary fields use Literal types listing the SKOS concept
  IRIs from the closed schemes. New role concepts (open scheme) are passed
  as plain IRI strings.
- IRIs are plain strings. Models do not depend on rdflib; the conversion to
  graphs lives in mgj.serialize.

Catechism question mapping
--------------------------
Q1  Submission.q1_narrative + Institution.name (link via Submission.documents_iri)
Q2  Submission.q2_narrative + Submission.stakeholders
Q3  Submission.q3_narrative + Submission.environmental_factors
Q4  Submission.q4_narrative + Submission.constitutional_elements
Q5  Submission.q5_narrative + Submission.field_sites
Q6  Submission.q6_narrative + .author_iri / .author_role / .author_disclosure
Q7  Submission.q7_narrative + Submission.origin_events
Q8  Submission.q8_narrative + Submission.evolution_mechanisms
Q9  Submission.q9_narrative + Submission.references
Cross-question structural: Submission.legal_context (operatesUnder)
"""

from __future__ import annotations

from datetime import date as DateT
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

NonEmptyStr = Annotated[str, Field(min_length=1)]
"""Mirrors sh:minLength 1."""

IRI = str
"""An IRI as a plain string. Not validated as a URL — may be any valid IRI."""


# ---------------------------------------------------------------------------
# Controlled-vocabulary Literals (closed SKOS schemes)
# ---------------------------------------------------------------------------

LessigModalityT = Literal["Law", "Norms", "Markets", "Architecture"]

ConstitutionalElementTypeT = Literal[
    "Bylaw",
    "Norm",
    "DecisionProcedure",
    "DisputeResolution",
    "AmendmentProcess",
]

LegalRelationshipT = Literal[
    "FiscalSponsor",
    "LegalIncorporation",
    "ParentOrganization",
    "Incubator",
    "Network",
]


# ---------------------------------------------------------------------------
# Shared agents (live in shared/people.ttl, shared/organizations.ttl)
# ---------------------------------------------------------------------------


class Person(BaseModel):
    model_config = ConfigDict(frozen=True)
    iri: IRI
    name: NonEmptyStr
    homepage: HttpUrl | None = None


class Organization(BaseModel):
    model_config = ConfigDict(frozen=True)
    iri: IRI
    name: NonEmptyStr
    homepage: HttpUrl | None = None


class UnresolvedAgent(BaseModel):
    """Parser placeholder for an agent reference too vague to type. Must be
    resolved (replaced with a Person or Organization) before system validation."""

    model_config = ConfigDict(frozen=True)
    iri: IRI
    label: NonEmptyStr


# ---------------------------------------------------------------------------
# Persistent institution
# ---------------------------------------------------------------------------


class Institution(BaseModel):
    iri: IRI
    name: NonEmptyStr
    description: str | None = None


# ---------------------------------------------------------------------------
# Per-question typed entities
# ---------------------------------------------------------------------------


class Stakeholder(BaseModel):
    """Q2 — n-ary connector between agent, role, and submission."""

    iri: IRI
    agent_iri: IRI
    """foaf:Person, foaf:Organization, or mgj:UnresolvedAgent IRI."""
    role_label: NonEmptyStr
    role_iri: IRI | None = None
    """SKOS concept in mgj:RoleType. Required at system level; optional inner-loop."""
    responsibilities: str | None = None


class FieldSite(BaseModel):
    """Q5."""

    iri: IRI
    label: NonEmptyStr
    url: HttpUrl | None = None
    description: str | None = None


class EnvironmentalFactor(BaseModel):
    """Q3 — Lessig-typed."""

    iri: IRI
    modality: LessigModalityT
    description: NonEmptyStr


class ConstitutionalElement(BaseModel):
    """Q4."""

    iri: IRI
    label: NonEmptyStr
    description: NonEmptyStr
    element_type: ConstitutionalElementTypeT
    source_url: HttpUrl | None = None


class OriginEvent(BaseModel):
    """Q7 — subClassOf prov:Activity."""

    iri: IRI
    label: NonEmptyStr
    description: NonEmptyStr
    date: DateT | None = None
    participant_iris: list[IRI] = Field(default_factory=list)


class EvolutionMechanism(BaseModel):
    """Q8."""

    iri: IRI
    label: NonEmptyStr
    description: NonEmptyStr


class Reference(BaseModel):
    """Q9 — bibliographic entry, dcterms-driven."""

    iri: IRI
    title: NonEmptyStr
    identifier: NonEmptyStr
    """DOI, URL, or other canonical identifier."""
    creators: list[str] = Field(default_factory=list)
    date: str | None = None
    """Free-form date (year, ISO date, or 'forthcoming') — not strictly typed."""


class LegalContext(BaseModel):
    """Cross-question — host org + relationship type."""

    iri: IRI
    host_organization_iri: IRI
    legal_relationship: LegalRelationshipT
    description: NonEmptyStr
    funding_reference: str | None = None


# ---------------------------------------------------------------------------
# Top-level submission
# ---------------------------------------------------------------------------


class Submission(BaseModel):
    iri: IRI
    institution_iri: IRI
    submission_date: DateT
    submission_version: NonEmptyStr

    # Q6 author disclosure
    author_iri: IRI | None = None
    author_role: str | None = None
    author_disclosure: str | None = None

    # Per-question narratives
    q1_narrative: str | None = None
    q2_narrative: str | None = None
    q3_narrative: str | None = None
    q4_narrative: str | None = None
    q5_narrative: str | None = None
    q6_narrative: str | None = None
    q7_narrative: str | None = None
    q8_narrative: str | None = None
    q9_narrative: str | None = None

    # Per-question typed entities
    stakeholders: list[Stakeholder] = Field(default_factory=list)
    environmental_factors: list[EnvironmentalFactor] = Field(default_factory=list)
    constitutional_elements: list[ConstitutionalElement] = Field(default_factory=list)
    field_sites: list[FieldSite] = Field(default_factory=list)
    origin_events: list[OriginEvent] = Field(default_factory=list)
    evolution_mechanisms: list[EvolutionMechanism] = Field(default_factory=list)
    references: list[Reference] = Field(default_factory=list)

    # Cross-question structural
    legal_context: LegalContext | None = None

    # Parser carryover (entities that surfaced but weren't resolved yet)
    unresolved_agents: list[UnresolvedAgent] = Field(default_factory=list)


__all__ = [
    "NonEmptyStr",
    "IRI",
    "LessigModalityT",
    "ConstitutionalElementTypeT",
    "LegalRelationshipT",
    "Person",
    "Organization",
    "UnresolvedAgent",
    "Institution",
    "Stakeholder",
    "FieldSite",
    "EnvironmentalFactor",
    "ConstitutionalElement",
    "OriginEvent",
    "EvolutionMechanism",
    "Reference",
    "LegalContext",
    "Submission",
]
