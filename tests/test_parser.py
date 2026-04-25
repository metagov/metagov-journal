"""M5: parser orchestration tests using a MockLLMBackend.

We exercise the full pipeline (input.md slicer → backend call →
RDF emission → reconciliation) without making any network calls.
"""

from __future__ import annotations

from datetime import date as DateT
from pathlib import Path

import pytest
from rdflib import Graph
from rdflib.namespace import DCTERMS, RDF
from typer.testing import CliRunner

import mgj.commands._common as _common
import mgj.commands.extract as extract_cmd
import mgj.graph as _graph
from mgj.cli import app
from mgj.namespaces import MGJ
from mgj.parser.backends import MockLLMBackend
from mgj.parser.extract import parse_input_sections, run_extraction

runner = CliRunner()


# ---------------------------------------------------------------------------
# Section slicing
# ---------------------------------------------------------------------------


def test_parse_input_sections_extracts_each_question() -> None:
    text = """\
# Foo

intro

## 1. Purpose

This is Q1 prose.

## 2. Stakeholders

This is Q2 prose.

## 9. References

This is Q9 prose.
"""
    sections = parse_input_sections(text)
    assert set(sections.keys()) == {1, 2, 9}
    assert "This is Q1 prose." in sections[1]
    assert "This is Q2 prose." in sections[2]
    assert "This is Q9 prose." in sections[9]


def test_parse_input_sections_returns_empty_for_no_headings() -> None:
    sections = parse_input_sections("just prose, no headings")
    assert sections == {}


# ---------------------------------------------------------------------------
# Mock backend dispatch helpers
# ---------------------------------------------------------------------------


def _mock_responder_factory():
    """Returns a responder callable that emits canned per-question JSON
    based on which Qi the system_prompt is for."""

    def responder(system_prompt: str, user_prompt: str) -> dict:
        # Each prompt explicitly names its question; key on that.
        if "Question 2:" in system_prompt:
            return {
                "stakeholders": [
                    {
                        "role_label": "Editor",
                        "agent_label": "Alice Chen",
                        "responsibilities": "Coordinates review.",
                    },
                    {
                        "role_label": "Reader",
                        "agent_label": "the community",
                        "responsibilities": None,
                    },
                ]
            }
        if "Question 3:" in system_prompt:
            return {
                "factors": [
                    {"modality": "Law", "description": "Subject to nonprofit law."}
                ]
            }
        if "Question 4:" in system_prompt:
            return {
                "elements": [
                    {
                        "label": "Charter",
                        "description": "Founding document.",
                        "element_type": "Bylaw",
                        "source_url": None,
                    }
                ]
            }
        if "Question 5:" in system_prompt:
            return {
                "field_sites": [
                    {
                        "label": "GitHub repo",
                        "url": "https://github.com/example/repo",
                        "description": None,
                    }
                ]
            }
        if "Question 6:" in system_prompt:
            return {
                "author_label": "Alice Chen",
                "author_role": "founder",
                "disclosure": "Author is a founder; potential bias.",
            }
        if "Question 7:" in system_prompt:
            return {
                "events": [
                    {
                        "label": "Founding meeting",
                        "description": "Founders convened.",
                        "date": "2024-01-01",
                        "participant_labels": ["Alice Chen", "Bob Tan"],
                    }
                ]
            }
        if "Question 8:" in system_prompt:
            return {
                "mechanisms": [
                    {
                        "label": "PR-driven amendment",
                        "description": "Changes via GitHub PR.",
                    }
                ]
            }
        if "Question 9:" in system_prompt:
            return {
                "references": [
                    {
                        "title": "Founding paper",
                        "identifier": "https://example.org/founding",
                        "creators": ["Alice Chen"],
                        "date": "2024",
                    }
                ]
            }
        raise RuntimeError(f"unrecognized prompt: {system_prompt[:80]!r}")

    return responder


# ---------------------------------------------------------------------------
# Fixture: isolated repo seeded with init+input.md
# ---------------------------------------------------------------------------


@pytest.fixture
def isolated_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    submissions = tmp_path / "submissions"
    shared = tmp_path / "shared"
    submissions.mkdir()
    shared.mkdir()
    monkeypatch.setattr(_graph, "SUBMISSIONS_DIR", submissions)
    monkeypatch.setattr(_graph, "SHARED_DIR", shared)
    monkeypatch.setattr(_common, "SUBMISSIONS_DIR", submissions)
    monkeypatch.setattr(_common, "SHARED_DIR", shared)
    return tmp_path


def _seed_with_input(slug: str, repo: Path, prose: str) -> None:
    runner.invoke(app, ["init", slug, "--name", "Test Institution"])
    (repo / "submissions" / slug / "input.md").write_text(prose)


SAMPLE_PROSE = """\
# Test Institution

## 1. Purpose

The institution maintains a peer-reviewed commons.

## 2. Stakeholders and roles

Alice Chen is the editor. The community participates as readers.

## 3. Environmental factors

Operates as a nonprofit.

## 4. Constitution

The Charter is the founding document.

## 5. Field sites

GitHub repo at github.com/example/repo.

## 6. Author relationship

I am Alice Chen, founder.

## 7. Origins

Founders convened in early 2024.

## 8. Evolution

Changes happen via PR.

## 9. References

Founding paper at example.org/founding.
"""


# ---------------------------------------------------------------------------
# Direct API tests (run_extraction)
# ---------------------------------------------------------------------------


def test_run_extraction_emits_typed_entities_via_mock_backend(
    isolated_repo: Path,
) -> None:
    slug = "demo"
    _seed_with_input(slug, isolated_repo, SAMPLE_PROSE)

    backend = MockLLMBackend(_mock_responder_factory())
    result = run_extraction(slug, backend=backend)

    assert result.extracted_questions == [2, 3, 4, 5, 6, 7, 8, 9]
    assert result.cache_misses == [2, 3, 4, 5, 6, 7, 8, 9]
    assert result.cache_hits == []
    assert result.skipped_affirmed == []

    # Load the resulting graph and verify entities exist.
    g = Graph()
    g.parse(
        str(isolated_repo / "submissions" / slug / "instance.ttl"),
        format="turtle",
    )

    # Q2: 2 stakeholders
    assert sum(1 for _ in g.subjects(RDF.type, MGJ.Stakeholder)) == 2
    # Q3: 1 factor, typed Law
    factors = list(g.subjects(RDF.type, MGJ.EnvironmentalFactor))
    assert len(factors) == 1
    assert (factors[0], MGJ.lessigModality, MGJ.Law) in g
    # Q4: 1 constitutional element typed Bylaw
    elements = list(g.subjects(RDF.type, MGJ.ConstitutionalElement))
    assert len(elements) == 1
    assert (elements[0], MGJ.elementType, MGJ.Bylaw) in g
    # Q5: 1 fieldsite
    assert sum(1 for _ in g.subjects(RDF.type, MGJ.FieldSite)) == 1
    # Q7: 1 origin event with 2 unresolved participants
    origins = list(g.subjects(RDF.type, MGJ.OriginEvent))
    assert len(origins) == 1
    parts = list(g.objects(origins[0], MGJ.originParticipant))
    assert len(parts) == 2
    # All participants are UnresolvedAgent (the parser doesn't resolve)
    for p in parts:
        assert (p, RDF.type, MGJ.UnresolvedAgent) in g
    # Q8: 1 evolution mechanism
    assert sum(1 for _ in g.subjects(RDF.type, MGJ.EvolutionMechanism)) == 1
    # Q9: 1 reference, with title set
    refs = list(g.subjects(RDF.type, MGJ.Reference))
    assert len(refs) == 1
    titles = list(g.objects(refs[0], DCTERMS.title))
    assert len(titles) == 1
    assert str(titles[0]) == "Founding paper"


def test_narratives_are_set_for_every_present_section(
    isolated_repo: Path,
) -> None:
    slug = "narratives"
    _seed_with_input(slug, isolated_repo, SAMPLE_PROSE)
    backend = MockLLMBackend(_mock_responder_factory())
    run_extraction(slug, backend=backend)

    g = Graph()
    g.parse(
        str(isolated_repo / "submissions" / slug / "instance.ttl"),
        format="turtle",
    )
    sub = next(g.subjects(RDF.type, MGJ.Submission))
    for q in range(1, 10):
        prop = MGJ[f"q{q}Narrative"]
        vals = list(g.objects(sub, prop))
        assert len(vals) == 1, f"missing narrative for Q{q}"


def test_extraction_cache_hits_skip_backend(isolated_repo: Path) -> None:
    slug = "cache"
    _seed_with_input(slug, isolated_repo, SAMPLE_PROSE)

    backend = MockLLMBackend(_mock_responder_factory())
    run_extraction(slug, backend=backend, questions=[2, 3])
    assert len(backend.calls) == 2

    # Second run with same input should hit cache for both.
    backend2 = MockLLMBackend(_mock_responder_factory())
    result = run_extraction(slug, backend=backend2, questions=[2, 3])
    assert result.cache_hits == [2, 3]
    assert result.cache_misses == []
    assert backend2.calls == []  # no backend calls on cache hit


def test_affirmed_question_is_skipped_unless_force(
    isolated_repo: Path,
) -> None:
    slug = "affirmed"
    _seed_with_input(slug, isolated_repo, SAMPLE_PROSE)

    backend = MockLLMBackend(_mock_responder_factory())
    run_extraction(slug, backend=backend, questions=[2])

    # Affirm Q2 manually via the CLI
    res = runner.invoke(app, ["affirm", slug, "--question", "2"])
    assert res.exit_code == 0, res.output

    # Re-run extract Q2: should skip
    result = run_extraction(slug, backend=backend, questions=[2])
    assert result.skipped_affirmed == [2]
    assert result.extracted_questions == []

    # With force=True, it re-extracts.
    result = run_extraction(slug, backend=backend, questions=[2], force=True)
    assert result.extracted_questions == [2]


def test_reextraction_drops_old_parser_output(isolated_repo: Path) -> None:
    """Re-running unaffirmed extraction replaces the old parser-output
    entities for that question, not appends."""
    slug = "rerun"
    _seed_with_input(slug, isolated_repo, SAMPLE_PROSE)

    backend = MockLLMBackend(_mock_responder_factory())
    run_extraction(slug, backend=backend, questions=[2])

    g = Graph()
    g.parse(str(isolated_repo / "submissions" / slug / "instance.ttl"), format="turtle")
    first_count = sum(1 for _ in g.subjects(RDF.type, MGJ.Stakeholder))
    assert first_count == 2

    # Modify input prose so the cache misses; backend returns the same shape
    # but we should still see the count stay at 2 (replace, not append).
    new_prose = SAMPLE_PROSE.replace(
        "Alice Chen is the editor",
        "Alice Chen is the chief editor",
    )
    (isolated_repo / "submissions" / slug / "input.md").write_text(new_prose)

    run_extraction(slug, backend=backend, questions=[2])
    g = Graph()
    g.parse(str(isolated_repo / "submissions" / slug / "instance.ttl"), format="turtle")
    second_count = sum(1 for _ in g.subjects(RDF.type, MGJ.Stakeholder))
    assert second_count == 2


def test_hand_added_entity_is_preserved_on_re_extract(
    isolated_repo: Path,
) -> None:
    """Entities without mgj:extractedBy (hand-added via CLI) survive re-extraction."""
    slug = "preserve"
    _seed_with_input(slug, isolated_repo, SAMPLE_PROSE)
    runner.invoke(app, ["people", "add", "alice", "--name", "Alice"])

    # Hand-add a stakeholder via CLI
    res = runner.invoke(
        app,
        [
            "stakeholder",
            "add",
            slug,
            "--role-label",
            "Reviewer",
            "--role-slug",
            "reviewer",
            "--person",
            "alice",
        ],
    )
    assert res.exit_code == 0, res.output

    backend = MockLLMBackend(_mock_responder_factory())
    run_extraction(slug, backend=backend, questions=[2])

    g = Graph()
    g.parse(str(isolated_repo / "submissions" / slug / "instance.ttl"), format="turtle")
    # We expect: 1 hand-added (no mgj:extractedBy) + 2 from extraction = 3 total
    total = list(g.subjects(RDF.type, MGJ.Stakeholder))
    assert len(total) == 3
    hand_added = [s for s in total if (s, MGJ.extractedBy, None) not in g]
    assert len(hand_added) == 1


# ---------------------------------------------------------------------------
# CLI command tests
# ---------------------------------------------------------------------------


def test_extract_cli_uses_injected_backend(
    isolated_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    slug = "cli"
    _seed_with_input(slug, isolated_repo, SAMPLE_PROSE)

    monkeypatch.setattr(
        extract_cmd,
        "backend_factory",
        lambda: MockLLMBackend(_mock_responder_factory()),
    )

    res = runner.invoke(app, ["extract", slug, "--question", "2"])
    assert res.exit_code == 0, res.output
    assert "extracted" in res.output.lower()
