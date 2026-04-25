"""M3: CLI integration test — drive a complete submission build via
typer commands and verify it passes system SHACL.

Tests redirect SUBMISSIONS_DIR and SHARED_DIR onto a tmp_path so the
real repo is not touched.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

import mgj.commands._common as _common
import mgj.graph as _graph
from mgj.canonicalize import graph_hash
from mgj.cli import app
from mgj.graph import load_instance
from mgj.validate import validate

runner = CliRunner()


@pytest.fixture
def isolated_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect SUBMISSIONS_DIR and SHARED_DIR onto tmp_path."""
    submissions = tmp_path / "submissions"
    shared = tmp_path / "shared"
    submissions.mkdir()
    shared.mkdir()
    monkeypatch.setattr(_graph, "SUBMISSIONS_DIR", submissions)
    monkeypatch.setattr(_graph, "SHARED_DIR", shared)
    monkeypatch.setattr(_common, "SUBMISSIONS_DIR", submissions)
    monkeypatch.setattr(_common, "SHARED_DIR", shared)
    return tmp_path


def _run(args: list[str], expect_success: bool = True) -> object:
    result = runner.invoke(app, args)
    if expect_success and result.exit_code != 0:
        print("OUTPUT:", result.output)
        print("EXC:", result.exception)
        raise AssertionError(f"command failed: mgj {' '.join(args)}")
    return result


def test_full_submission_round_trip(isolated_repo: Path) -> None:
    slug = "test-inst"

    # 1. Seed shared registries.
    _run(["people", "add", "alice", "--name", "Alice Example"])
    _run(["people", "add", "bob", "--name", "Bob Example"])
    _run(["orgs", "add", "metagov", "--name", "Metagov"])

    # 2. Init the submission.
    _run(["init", slug, "--name", "Test Institution"])

    # 3. Set narratives for each catechism question.
    for q in range(1, 10):
        _run(
            [
                "narrative",
                slug,
                "--question",
                str(q),
                f"Narrative for Q{q}.",
            ]
        )

    # 4. Q2: a stakeholder.
    _run(
        [
            "stakeholder",
            "add",
            slug,
            "--role-label",
            "Editor",
            "--role-slug",
            "editor",
            "--person",
            "alice",
            "--responsibilities",
            "Reviews submissions.",
        ]
    )

    # 5. Q3: an environmental factor.
    _run(
        [
            "factor",
            "add",
            slug,
            "--modality",
            "Law",
            "--description",
            "Subject to nonprofit regulation.",
        ]
    )

    # 6. Q4: a constitutional element.
    _run(
        [
            "constitution",
            "add",
            slug,
            "--label",
            "Charter",
            "--description",
            "Founding charter document.",
            "--type",
            "Bylaw",
        ]
    )

    # 7. Q5: a field site.
    _run(
        [
            "fieldsite",
            "add",
            slug,
            "--label",
            "GitHub repo",
            "--url",
            "https://github.com/example/repo",
        ]
    )

    # 8. Q6: author disclosure.
    _run(
        [
            "author",
            "set",
            slug,
            "--person",
            "alice",
            "--role",
            "founder",
            "--disclosure",
            "Author is a founder; potential bias.",
        ]
    )

    # 9. Q7: an origin event.
    _run(
        [
            "origin",
            "add",
            slug,
            "--label",
            "Founding meeting",
            "--description",
            "Founders convened.",
            "--date",
            "2024-01-01",
            "--persons",
            "alice,bob",
        ]
    )

    # 10. Q8: an evolution mechanism.
    _run(
        [
            "evolution",
            "add",
            slug,
            "--label",
            "PR-driven amendment",
            "--description",
            "Changes via GitHub PR.",
        ]
    )

    # 11. Q9: a reference.
    _run(
        [
            "reference",
            "add",
            slug,
            "--title",
            "Founding paper",
            "--identifier",
            "https://example.org/founding",
            "--creators",
            "Alice,Bob",
            "--date",
            "2024",
        ]
    )

    # 12. Optional: legal context.
    _run(
        [
            "legal",
            "set",
            slug,
            "--host",
            "metagov",
            "--relationship",
            "FiscalSponsor",
            "--description",
            "Fiscal sponsorship under Metagov.",
        ]
    )

    # 13. System validation should now pass.
    result = _run(["validate", slug])
    assert "✓" in result.output, result.output

    # 14. The on-disk instance.ttl loads + passes system SHACL via the
    # validation library directly (independent of the CLI surface).
    instance = isolated_repo / "submissions" / slug / "instance.ttl"
    assert instance.exists()
    g = load_instance(instance)
    report = validate(g, mode="system")
    assert report.conforms, str(report)


def test_init_then_validate_fails_until_complete(isolated_repo: Path) -> None:
    slug = "incomplete"
    _run(["init", slug, "--name", "Incomplete Institution"])
    # Bare-bones instance: no narratives, no entities. System validation
    # should fail.
    result = runner.invoke(app, ["validate", slug])
    assert result.exit_code == 1
    # Run-time assertion that we hit several violations.
    assert "violation" in result.output.lower() or "FAIL" in result.output


def test_canonicalize_idempotent_via_cli(isolated_repo: Path) -> None:
    slug = "canon"
    _run(["people", "add", "alice", "--name", "Alice"])
    _run(["init", slug, "--name", "Canon"])
    _run(["narrative", slug, "--question", "1", "Purpose."])
    _run(["stakeholder", "add", slug, "--role-label", "Editor", "--role-slug", "editor", "--person", "alice"])

    instance = isolated_repo / "submissions" / slug / "instance.ttl"
    before = instance.read_text()
    _run(["canonicalize", slug])
    after = instance.read_text()
    assert before == after  # already canonical because every CLI write canonicalizes


def test_stakeholder_add_rejects_unknown_person(isolated_repo: Path) -> None:
    slug = "rejects"
    _run(["init", slug, "--name", "Test"])
    result = runner.invoke(
        app,
        [
            "stakeholder",
            "add",
            slug,
            "--role-label",
            "Editor",
            "--role-slug",
            "editor",
            "--person",
            "nonexistent",
        ],
    )
    assert result.exit_code != 0


def test_per_question_validation_runs_on_mutation(isolated_repo: Path) -> None:
    """Adding a malformed entity should be rejected by per-Q SHACL.

    We sneak in a malformed factor by deleting its modality after adding,
    then running affirm — affirm runs per-Q SHACL and must reject.
    """
    slug = "perq"
    _run(["people", "add", "alice", "--name", "Alice"])
    _run(["init", slug, "--name", "Test"])
    _run(["factor", "add", slug, "--modality", "Law", "--description", "ok"])
    # Manually break the instance.ttl to drop modality, then attempt affirm.
    from rdflib import Graph

    instance = isolated_repo / "submissions" / slug / "instance.ttl"
    g = Graph()
    g.parse(str(instance), format="turtle")
    from mgj.namespaces import MGJ

    g.remove((None, MGJ.lessigModality, None))
    instance.write_text(g.serialize(format="turtle"))

    # affirm Q3 should fail per-Q validation.
    result = runner.invoke(app, ["affirm", slug, "--question", "3"])
    assert result.exit_code == 1
