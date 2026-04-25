"""
mgj.parser.schemas
------------------
Per-question Pydantic schemas for parser output.

These are *parser-output* models — what the LLM is asked to produce — not
the canonical ``mgj.models``. The orchestration layer maps each parser
output to canonical RDF triples in ``extract.py``. Keeping the two sets
of models distinct lets us evolve the parser interface independently of
the wire format.

Each schema mirrors a single catechism question. The JSON-schema view
(via ``model_json_schema()``) is what we hand to the backend's
structured-output / tool-use API.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field

NonEmptyStr = Annotated[str, Field(min_length=1)]


# ---------------------------------------------------------------------------
# Q2 — stakeholders
# ---------------------------------------------------------------------------


class ExtractedStakeholder(BaseModel):
    role_label: NonEmptyStr = Field(
        description="The stakeholder's role within the institution, e.g. 'Editor', 'Reviewer'."
    )
    agent_label: NonEmptyStr = Field(
        description=(
            "The literal phrase identifying the actor (e.g. 'Alice Chen', "
            "'Metagov community'). The author will resolve this to a specific "
            "Person or Organization later."
        )
    )
    responsibilities: str | None = Field(
        default=None,
        description="Description of what this stakeholder is responsible for. Optional.",
    )


class Q2Extraction(BaseModel):
    stakeholders: list[ExtractedStakeholder] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Q3 — environmental factors (Lessig-typed)
# ---------------------------------------------------------------------------


class ExtractedFactor(BaseModel):
    modality: Literal["Law", "Norms", "Markets", "Architecture"] = Field(
        description="Which Lessig modality this factor falls under."
    )
    description: NonEmptyStr = Field(
        description="Description of the environmental force and how it shapes the institution."
    )


class Q3Extraction(BaseModel):
    factors: list[ExtractedFactor] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Q4 — constitutional elements
# ---------------------------------------------------------------------------


class ExtractedConstitutionalElement(BaseModel):
    label: NonEmptyStr = Field(
        description="Short name for the rule, norm, or procedure."
    )
    description: NonEmptyStr
    element_type: Literal[
        "Bylaw",
        "Norm",
        "DecisionProcedure",
        "DisputeResolution",
        "AmendmentProcess",
    ] = Field(description="Category of constitutional element.")
    source_url: str | None = Field(
        default=None,
        description="Optional canonical URL for this element (charter doc, repo file).",
    )


class Q4Extraction(BaseModel):
    elements: list[ExtractedConstitutionalElement] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Q5 — field sites
# ---------------------------------------------------------------------------


class ExtractedFieldSite(BaseModel):
    label: NonEmptyStr
    url: str | None = None
    description: str | None = None


class Q5Extraction(BaseModel):
    field_sites: list[ExtractedFieldSite] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Q6 — author disclosure (singleton)
# ---------------------------------------------------------------------------


class Q6Extraction(BaseModel):
    author_label: NonEmptyStr | None = Field(
        default=None,
        description="The author's name as it appears in the prose. Author resolves to a Person.",
    )
    author_role: str | None = None
    disclosure: str | None = Field(
        default=None,
        description="Disclosure of biases, blind spots, or motivations.",
    )


# ---------------------------------------------------------------------------
# Q7 — origin events
# ---------------------------------------------------------------------------


class ExtractedOriginEvent(BaseModel):
    label: NonEmptyStr
    description: NonEmptyStr
    date: str | None = Field(
        default=None,
        description="ISO 8601 date if specifiable (YYYY or YYYY-MM-DD); otherwise null.",
    )
    participant_labels: list[str] = Field(
        default_factory=list,
        description="Names of participants. Author resolves these to People/Orgs later.",
    )


class Q7Extraction(BaseModel):
    events: list[ExtractedOriginEvent] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Q8 — evolution mechanisms
# ---------------------------------------------------------------------------


class ExtractedEvolutionMechanism(BaseModel):
    label: NonEmptyStr
    description: NonEmptyStr


class Q8Extraction(BaseModel):
    mechanisms: list[ExtractedEvolutionMechanism] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Q9 — references
# ---------------------------------------------------------------------------


class ExtractedReference(BaseModel):
    title: NonEmptyStr
    identifier: NonEmptyStr = Field(description="DOI or canonical URL.")
    creators: list[str] = Field(default_factory=list)
    date: str | None = None


class Q9Extraction(BaseModel):
    references: list[ExtractedReference] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Mapping: question number → schema
# ---------------------------------------------------------------------------

EXTRACTION_SCHEMAS: dict[int, type[BaseModel]] = {
    2: Q2Extraction,
    3: Q3Extraction,
    4: Q4Extraction,
    5: Q5Extraction,
    6: Q6Extraction,
    7: Q7Extraction,
    8: Q8Extraction,
    9: Q9Extraction,
}
"""Q1 has no typed entities (narrative-only). All other questions have a schema."""

QUESTIONS_WITH_ENTITIES = sorted(EXTRACTION_SCHEMAS.keys())


__all__ = [
    "ExtractedStakeholder",
    "Q2Extraction",
    "ExtractedFactor",
    "Q3Extraction",
    "ExtractedConstitutionalElement",
    "Q4Extraction",
    "ExtractedFieldSite",
    "Q5Extraction",
    "Q6Extraction",
    "ExtractedOriginEvent",
    "Q7Extraction",
    "ExtractedEvolutionMechanism",
    "Q8Extraction",
    "ExtractedReference",
    "Q9Extraction",
    "EXTRACTION_SCHEMAS",
    "QUESTIONS_WITH_ENTITIES",
]
