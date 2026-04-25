"""
mgj.parser.extract
------------------
Orchestration: input.md → typed RDF triples.

Per-question pipeline:
    1. Slice input.md to the Qi section.
    2. Set the q{i}Narrative literal on the Submission (always done).
    3. If Qi has a parser schema, call the LLMBackend for structured output.
    4. Validate the output via Pydantic.
    5. Convert each parsed entity to RDF triples (minted IRIs, provenance
       stamps, links from Submission).
    6. Reconcile against the existing graph (see ``reconcile.py``):
       parser-output entities for unaffirmed Qi are replaced; affirmed
       entities are sticky.
    7. Save the canonicalized graph; record an Extraction provenance
       node with model id, prompt hash, input SHA, timestamp.

Caching: per-question (input_section_sha, prompt_hash, model_id) keyed
file cache under ``submissions/<slug>/.cache/extractions/``. On cache
hit we skip the backend call entirely.

Affirmation guard: if Qi is already affirmed in extraction-trace.json,
``extract`` refuses to re-run for that Qi unless ``force=True``. The
expected workflow is `mgj unaffirm -q N` first.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from rdflib import Graph, Literal, URIRef
from rdflib.namespace import RDF, XSD

from mgj.canonicalize import canonicalize_turtle
from mgj.commands._common import (
    ExtractionTrace,
    load_trace,
    save_trace,
)
from mgj.graph import submission_dir, submission_instance_path
from mgj.namespaces import MGJ, submission_entity_iri
from mgj.parser import cache as cache_mod
from mgj.parser import reconcile as reconcile_mod
from mgj.parser.backends import ExtractionResult, LLMBackend
from mgj.parser.prompts import system_prompt_for_question
from mgj.parser.schemas import EXTRACTION_SCHEMAS, QUESTIONS_WITH_ENTITIES

# ---------------------------------------------------------------------------
# Top-level entry
# ---------------------------------------------------------------------------


@dataclass
class ExtractionRunResult:
    """Summary returned by ``run_extraction``."""

    extracted_questions: list[int]
    skipped_affirmed: list[int]
    cache_hits: list[int]
    cache_misses: list[int]


def run_extraction(
    slug: str,
    *,
    backend: LLMBackend,
    questions: list[int] | None = None,
    force: bool = False,
) -> ExtractionRunResult:
    """Extract typed RDF triples from input.md for the given submission.

    Parameters
    ----------
    slug : str
        Submission slug.
    backend : LLMBackend
        Provider-agnostic structured-output backend.
    questions : list[int] | None
        If given, only these questions are extracted. Default: all
        questions that have entity schemas (Q2..Q9).
    force : bool
        If True, re-extract even for already-affirmed questions.
    """
    sdir = submission_dir(slug)
    input_md = sdir / "input.md"
    if not input_md.exists():
        raise FileNotFoundError(f"no input.md at {input_md}")

    sections = parse_input_sections(input_md.read_text())

    instance_path = submission_instance_path(slug)
    g = Graph()
    g.parse(str(instance_path), format="turtle")

    # Find the (single) Submission IRI; it's the canonical attachment point.
    sub = _single_submission_iri(g)
    version = _scalar(g, sub, MGJ.submissionVersion)

    trace = load_trace(slug)
    qs = questions if questions is not None else QUESTIONS_WITH_ENTITIES

    extracted: list[int] = []
    skipped_affirmed: list[int] = []
    cache_hits: list[int] = []
    cache_misses: list[int] = []

    # Always set narratives for whatever sections appear, regardless of
    # whether we run extraction. Narratives carry the author's prose
    # and should round-trip to the compiled output.
    for q in range(1, 10):
        if q in sections:
            _set_narrative(g, sub, q, sections[q])

    for q in qs:
        if q not in sections:
            continue
        if not force and trace.affirmed_questions.get(q):
            skipped_affirmed.append(q)
            continue

        prose = sections[q]
        schema_cls = EXTRACTION_SCHEMAS[q]
        json_schema = schema_cls.model_json_schema()
        system_prompt = system_prompt_for_question(q)
        user_prompt = prose

        # Cache lookup first: we don't even need to know model_id without a call,
        # so we use a stable convention: store the latest call's model_id under
        # the (prompt_hash, input_hash) bucket. Implementation: try to find any
        # cached entry whose prompt_hash + input_hash match.
        cached = _lookup_cache(
            sdir,
            prompt=system_prompt,
            user=user_prompt,
        )
        if cached is not None:
            cache_hits.append(q)
            result = cached
        else:
            cache_misses.append(q)
            result = backend.extract(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                json_schema=json_schema,
            )
            cache_mod.save_cached(sdir, result)

        parsed = schema_cls.model_validate(result.parsed)

        # Record an mgj:Extraction activity that we'll attach as
        # provenance to every parser-output entity for this question.
        extraction_iri = URIRef(
            submission_entity_iri(slug, version, "extraction", f"q{q}-{result.timestamp.replace(':','').replace('-','')}")
        )
        _record_extraction_activity(g, extraction_iri, q, result)

        # Reconcile: drop unaffirmed parser-output entities for this Qi.
        reconcile_mod.drop_parser_output_for_question(g, sub, q)

        # Convert parsed -> triples + link to Submission.
        _apply_extracted(g, sub, slug, version, q, parsed, extraction_iri)

        extracted.append(q)
        # Record the extraction in the trace's extraction log.
        trace.extractions.append(
            {
                "question": q,
                "model": result.model_id,
                "prompt_hash": result.prompt_hash,
                "input_hash": result.input_hash,
                "extracted_at": result.timestamp,
                "from_cache": cached is not None,
            }
        )

    # Save back: separate shared subjects (the per-submission file
    # shouldn't redeclare them).
    from mgj.commands._common import save_submission_graph_separating_shared

    save_submission_graph_separating_shared(g, slug)
    save_trace(trace)

    return ExtractionRunResult(
        extracted_questions=extracted,
        skipped_affirmed=skipped_affirmed,
        cache_hits=cache_hits,
        cache_misses=cache_misses,
    )


# ---------------------------------------------------------------------------
# Section slicer
# ---------------------------------------------------------------------------

_HEADING_RE = re.compile(r"^##\s+(\d+)\.\s+", re.MULTILINE)


def parse_input_sections(text: str) -> dict[int, str]:
    """Split input.md into a {question_number: section_prose} dict.

    Headings are recognized as ``## N. ...`` per the input.md template.
    The Q1 marker line itself is included in the slice (helpful context
    for the model). Trailing whitespace is stripped.
    """
    matches = list(_HEADING_RE.finditer(text))
    if not matches:
        return {}
    sections: dict[int, str] = {}
    for i, m in enumerate(matches):
        q = int(m.group(1))
        if not 1 <= q <= 9:
            continue
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        sections[q] = text[start:end].strip()
    return sections


# ---------------------------------------------------------------------------
# Cache lookup: any entry with matching prompt+input
# ---------------------------------------------------------------------------


def _lookup_cache(submission_dir: Path, *, prompt: str, user: str) -> ExtractionResult | None:
    """Look for any cached extraction with matching prompt+input hashes,
    regardless of model id. Returns the most recent match or None."""
    from hashlib import sha256

    prompt_hash = sha256(prompt.encode("utf-8")).hexdigest()
    input_hash = sha256(user.encode("utf-8")).hexdigest()

    cdir = cache_mod.cache_dir(submission_dir)
    if not cdir.exists():
        return None
    import json

    candidates: list[ExtractionResult] = []
    for f in sorted(cdir.glob("*.json")):
        try:
            data = json.loads(f.read_text())
        except json.JSONDecodeError:
            continue
        if data.get("prompt_hash") == prompt_hash and data.get("input_hash") == input_hash:
            candidates.append(ExtractionResult(**data))
    if not candidates:
        return None
    # Return the most recent by timestamp.
    return max(candidates, key=lambda r: r.timestamp)


# ---------------------------------------------------------------------------
# Apply parsed extractions → RDF triples
# ---------------------------------------------------------------------------


def _apply_extracted(
    g: Graph,
    sub: URIRef,
    slug: str,
    version: str,
    q: int,
    parsed,
    extraction_iri: URIRef,
) -> None:
    """Dispatch per-question to a specialized triple-emission helper."""
    if q == 2:
        _emit_stakeholders(g, sub, slug, version, parsed, extraction_iri)
    elif q == 3:
        _emit_factors(g, sub, slug, version, parsed, extraction_iri)
    elif q == 4:
        _emit_constitutional(g, sub, slug, version, parsed, extraction_iri)
    elif q == 5:
        _emit_field_sites(g, sub, slug, version, parsed, extraction_iri)
    elif q == 6:
        _emit_q6(g, sub, slug, version, parsed, extraction_iri)
    elif q == 7:
        _emit_origin_events(g, sub, slug, version, parsed, extraction_iri)
    elif q == 8:
        _emit_evolution(g, sub, slug, version, parsed, extraction_iri)
    elif q == 9:
        _emit_references(g, sub, slug, version, parsed, extraction_iri)


def _next_id(g: Graph, slug: str, version: str, kind: str, owl_class: str) -> str:
    """Find next free integer id for kind, accounting for entities currently in graph."""
    base = submission_entity_iri(slug, version, kind, "")
    nums: list[int] = []
    for s in g.subjects(RDF.type, MGJ[owl_class]):
        iri = str(s)
        if iri.startswith(base):
            tail = iri[len(base):]
            if tail.isdigit():
                nums.append(int(tail))
    return str(max(nums, default=0) + 1)


def _emit_stakeholders(g, sub, slug, version, parsed, extraction_iri):
    for s in parsed.stakeholders:
        sid = _next_id(g, slug, version, "stakeholder", "Stakeholder")
        node = URIRef(submission_entity_iri(slug, version, "stakeholder", sid))
        g.add((node, RDF.type, MGJ.Stakeholder))

        # Mint an UnresolvedAgent for the agent_label; author resolves later.
        ua_id = _next_id(g, slug, version, "unresolved", "UnresolvedAgent")
        ua = URIRef(submission_entity_iri(slug, version, "unresolved", ua_id))
        g.add((ua, RDF.type, MGJ.UnresolvedAgent))
        g.add((ua, MGJ.unresolvedLabel, Literal(s.agent_label)))

        g.add((node, MGJ.stakeholderAgent, ua))
        g.add((node, MGJ.roleLabel, Literal(s.role_label)))
        if s.responsibilities:
            g.add((node, MGJ.stakeholderResponsibilities, Literal(s.responsibilities)))
        g.add((node, MGJ.extractedBy, extraction_iri))
        g.add((sub, MGJ.hasStakeholder, node))


def _emit_factors(g, sub, slug, version, parsed, extraction_iri):
    for f in parsed.factors:
        fid = _next_id(g, slug, version, "factor", "EnvironmentalFactor")
        node = URIRef(submission_entity_iri(slug, version, "factor", fid))
        g.add((node, RDF.type, MGJ.EnvironmentalFactor))
        g.add((node, MGJ.lessigModality, MGJ[f.modality]))
        g.add((node, MGJ.factorDescription, Literal(f.description)))
        g.add((node, MGJ.extractedBy, extraction_iri))
        g.add((sub, MGJ.hasEnvironmentalFactor, node))


def _emit_constitutional(g, sub, slug, version, parsed, extraction_iri):
    for c in parsed.elements:
        cid = _next_id(g, slug, version, "constitution", "ConstitutionalElement")
        node = URIRef(submission_entity_iri(slug, version, "constitution", cid))
        g.add((node, RDF.type, MGJ.ConstitutionalElement))
        g.add((node, MGJ.elementLabel, Literal(c.label)))
        g.add((node, MGJ.elementDescription, Literal(c.description)))
        g.add((node, MGJ.elementType, MGJ[c.element_type]))
        if c.source_url:
            g.add((node, MGJ.elementSourceURL, Literal(c.source_url, datatype=XSD.anyURI)))
        g.add((node, MGJ.extractedBy, extraction_iri))
        g.add((sub, MGJ.hasConstitutionalElement, node))


def _emit_field_sites(g, sub, slug, version, parsed, extraction_iri):
    for f in parsed.field_sites:
        fid = _next_id(g, slug, version, "fieldsite", "FieldSite")
        node = URIRef(submission_entity_iri(slug, version, "fieldsite", fid))
        g.add((node, RDF.type, MGJ.FieldSite))
        g.add((node, MGJ.fieldSiteLabel, Literal(f.label)))
        if f.url:
            g.add((node, MGJ.fieldSiteURL, Literal(f.url, datatype=XSD.anyURI)))
        if f.description:
            g.add((node, MGJ.fieldSiteDescription, Literal(f.description)))
        g.add((node, MGJ.extractedBy, extraction_iri))
        g.add((sub, MGJ.hasFieldSite, node))


def _emit_q6(g, sub, slug, version, parsed, extraction_iri):
    """Q6 is a singleton: set authorRole, authorDisclosure on the
    Submission, and create an UnresolvedAgent for the author_label so
    the author can resolve to a Person."""
    if parsed.author_role:
        g.remove((sub, MGJ.authorRole, None))
        g.add((sub, MGJ.authorRole, Literal(parsed.author_role)))
    if parsed.disclosure:
        g.remove((sub, MGJ.authorDisclosure, None))
        g.add((sub, MGJ.authorDisclosure, Literal(parsed.disclosure)))
    if parsed.author_label:
        ua_id = _next_id(g, slug, version, "unresolved", "UnresolvedAgent")
        ua = URIRef(submission_entity_iri(slug, version, "unresolved", ua_id))
        g.add((ua, RDF.type, MGJ.UnresolvedAgent))
        g.add((ua, MGJ.unresolvedLabel, Literal(parsed.author_label)))
        g.add((ua, MGJ.extractedBy, extraction_iri))
        # NOT linked via authoredBy yet — author must resolve and use
        # `mgj author set` to install the foaf:Person.


def _emit_origin_events(g, sub, slug, version, parsed, extraction_iri):
    for ev in parsed.events:
        eid = _next_id(g, slug, version, "origin", "OriginEvent")
        node = URIRef(submission_entity_iri(slug, version, "origin", eid))
        g.add((node, RDF.type, MGJ.OriginEvent))
        g.add((node, MGJ.originLabel, Literal(ev.label)))
        g.add((node, MGJ.originDescription, Literal(ev.description)))
        if ev.date:
            g.add((node, MGJ.originDate, Literal(ev.date, datatype=XSD.date)))
        for label in ev.participant_labels:
            ua_id = _next_id(g, slug, version, "unresolved", "UnresolvedAgent")
            ua = URIRef(submission_entity_iri(slug, version, "unresolved", ua_id))
            g.add((ua, RDF.type, MGJ.UnresolvedAgent))
            g.add((ua, MGJ.unresolvedLabel, Literal(label)))
            g.add((node, MGJ.originParticipant, ua))
        g.add((node, MGJ.extractedBy, extraction_iri))
        g.add((sub, MGJ.hasOriginEvent, node))


def _emit_evolution(g, sub, slug, version, parsed, extraction_iri):
    for m in parsed.mechanisms:
        mid = _next_id(g, slug, version, "evolution", "EvolutionMechanism")
        node = URIRef(submission_entity_iri(slug, version, "evolution", mid))
        g.add((node, RDF.type, MGJ.EvolutionMechanism))
        g.add((node, MGJ.mechanismLabel, Literal(m.label)))
        g.add((node, MGJ.mechanismDescription, Literal(m.description)))
        g.add((node, MGJ.extractedBy, extraction_iri))
        g.add((sub, MGJ.hasEvolutionMechanism, node))


def _emit_references(g, sub, slug, version, parsed, extraction_iri):
    from rdflib.namespace import DCTERMS

    for r in parsed.references:
        rid = _next_id(g, slug, version, "reference", "Reference")
        node = URIRef(submission_entity_iri(slug, version, "reference", rid))
        g.add((node, RDF.type, MGJ.Reference))
        g.add((node, DCTERMS.title, Literal(r.title)))
        g.add((node, DCTERMS.identifier, Literal(r.identifier)))
        if r.date:
            g.add((node, DCTERMS.date, Literal(r.date)))
        for c in r.creators:
            g.add((node, DCTERMS.creator, Literal(c)))
        g.add((node, MGJ.extractedBy, extraction_iri))
        g.add((sub, MGJ.hasReference, node))


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _set_narrative(g: Graph, sub: URIRef, q: int, section: str) -> None:
    """Strip the ``## N. ...`` heading line from the section and store
    the remaining prose as the q{i}Narrative literal."""
    body_lines = [ln for ln in section.splitlines() if not ln.startswith("## ")]
    body = "\n".join(body_lines).strip()
    if not body:
        return
    prop = MGJ[f"q{q}Narrative"]
    g.remove((sub, prop, None))
    g.add((sub, prop, Literal(body)))


def _record_extraction_activity(
    g: Graph, extraction_iri: URIRef, q: int, result: ExtractionResult
) -> None:
    g.add((extraction_iri, RDF.type, MGJ.Extraction))
    g.add((extraction_iri, MGJ.extractionModel, Literal(result.model_id)))
    g.add((extraction_iri, MGJ.promptHash, Literal(result.prompt_hash)))
    g.add((extraction_iri, MGJ.inputHash, Literal(result.input_hash)))
    g.add((extraction_iri, MGJ.extractedAt, Literal(result.timestamp, datatype=XSD.dateTime)))


def _single_submission_iri(g: Graph) -> URIRef:
    subjects = list(g.subjects(RDF.type, MGJ.Submission))
    if len(subjects) != 1:
        raise ValueError(f"expected one mgj:Submission; found {len(subjects)}")
    return subjects[0]


def _scalar(g: Graph, subject: URIRef, prop: URIRef) -> str:
    val = next(iter(g.objects(subject, prop)), None)
    if val is None:
        raise ValueError(f"missing {prop} on {subject}")
    return str(val)


__all__ = [
    "ExtractionRunResult",
    "run_extraction",
    "parse_input_sections",
]
