"""M4: catechism + wiki compiler tests.

- compiled.md output is byte-stable across runs (determinism invariant)
- compiled.md includes content from every catechism question
- wiki produces Home + Institution + Person + Organization pages
- wiki cross-links resolve (every link target exists as a file)
- Re-running the wiki compiler is byte-stable
"""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

import mgj.commands._common as _common
import mgj.graph as _graph
from mgj.cli import app

runner = CliRunner()


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


def _run(args: list[str], expect_success: bool = True) -> object:
    result = runner.invoke(app, args)
    if expect_success and result.exit_code != 0:
        raise AssertionError(f"failed: mgj {' '.join(args)}\n{result.output}")
    return result


def _seed_complete_submission(slug: str) -> None:
    """Build a complete submission via CLI commands (matches test_cli's fixture)."""
    _run(["people", "add", "alice", "--name", "Alice Example"])
    _run(["people", "add", "bob", "--name", "Bob Example"])
    _run(["orgs", "add", "metagov", "--name", "Metagov"])
    _run(["init", slug, "--name", "Test Institution", "--date", "2026-04-25"])
    for q in range(1, 10):
        _run(
            ["narrative", slug, "--question", str(q), f"Narrative for Q{q}."]
        )
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
            "Author is a founder; potential bias toward favorable framing.",
        ]
    )
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


def test_compile_produces_full_catechism_markdown(isolated_repo: Path) -> None:
    slug = "demo"
    _seed_complete_submission(slug)

    _run(["compile", slug])
    out = isolated_repo / "submissions" / slug / "compiled.md"
    assert out.exists()
    body = out.read_text()

    # Header
    assert "# Test Institution" in body
    assert "Submission v1.0.0" in body

    # All 9 catechism sections present
    for q in [
        "## 1. Purpose",
        "## 2. Stakeholders",
        "## 3. Environmental factors",
        "## 4. Constitution",
        "## 5. Field sites",
        "## 6. Author relationship",
        "## 7. Origins",
        "## 8. Evolution",
        "## 9. References",
    ]:
        assert q in body, f"missing section: {q}"

    # Legal context section appears (between Q8 and Q9 per the renderer)
    assert "## Legal context" in body
    assert "Metagov" in body

    # Stakeholder line
    assert "**Editor**" in body
    assert "Alice Example" in body

    # Lessig modality grouping for Q3
    assert "### Law" in body

    # Reference rendered with link
    assert "[Founding paper](https://example.org/founding)" in body


def test_compile_is_byte_stable(isolated_repo: Path) -> None:
    """Running the catechism compiler twice over the same instance.ttl
    produces byte-identical output."""
    slug = "stable"
    _seed_complete_submission(slug)
    _run(["compile", slug])
    first = (isolated_repo / "submissions" / slug / "compiled.md").read_text()
    _run(["compile", slug])
    second = (isolated_repo / "submissions" / slug / "compiled.md").read_text()
    assert first == second


def test_wiki_produces_home_and_entity_pages(isolated_repo: Path) -> None:
    slug = "wiki-demo"
    _seed_complete_submission(slug)

    wiki_dir = isolated_repo / "wiki"
    _run(["wiki", "--output", str(wiki_dir)])

    # Home + Institution + Person × 2 + Organization × 1
    assert (wiki_dir / "Home.md").exists()
    assert (wiki_dir / "Institution-test-institution-slug-not-known.md").exists() or any(
        p.name.startswith("Institution-") for p in wiki_dir.iterdir()
    )
    assert (wiki_dir / "Person-alice.md").exists()
    assert (wiki_dir / "Person-bob.md").exists()
    assert (wiki_dir / "Organization-metagov.md").exists()

    # Home indexes all institutions and people
    home = (wiki_dir / "Home.md").read_text()
    assert "Test Institution" in home
    assert "Alice Example" in home
    assert "Metagov" in home

    # Person page has backlinks: alice authored + is a stakeholder + participated in origin
    alice = (wiki_dir / "Person-alice.md").read_text()
    assert "Authored submissions" in alice
    assert "Stakeholder roles" in alice
    assert "Origin events" in alice

    # Org page records the fiscal sponsor relationship
    metagov = (wiki_dir / "Organization-metagov.md").read_text()
    assert "Fiscal Sponsor" in metagov
    assert "Test Institution" in metagov


def test_wiki_is_byte_stable(isolated_repo: Path) -> None:
    """Re-running the wiki compiler over the same graph state yields identical output."""
    slug = "wiki-stable"
    _seed_complete_submission(slug)

    wiki_dir = isolated_repo / "wiki"
    _run(["wiki", "--output", str(wiki_dir)])
    first_pages = {
        p.name: p.read_text() for p in sorted(wiki_dir.iterdir()) if p.suffix == ".md"
    }

    _run(["wiki", "--output", str(wiki_dir)])
    second_pages = {
        p.name: p.read_text() for p in sorted(wiki_dir.iterdir()) if p.suffix == ".md"
    }
    assert first_pages == second_pages


def test_wiki_internal_links_target_existing_files(isolated_repo: Path) -> None:
    """Every wiki Markdown link of the form [...](Name) should resolve to
    a sibling .md file."""
    slug = "links"
    _seed_complete_submission(slug)
    wiki_dir = isolated_repo / "wiki"
    _run(["wiki", "--output", str(wiki_dir)])

    import re

    page_files = {p.stem for p in wiki_dir.iterdir() if p.suffix == ".md"}
    for page in wiki_dir.iterdir():
        if page.suffix != ".md":
            continue
        for match in re.finditer(r"\[[^\]]+\]\((Institution|Person|Organization)-[^)]+\)", page.read_text()):
            link = match.group()
            target = link.split("](", 1)[1].rstrip(")")
            assert target in page_files, f"broken link in {page.name}: {target}"
