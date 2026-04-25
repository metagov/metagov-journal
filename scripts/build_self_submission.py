#!/usr/bin/env python3
"""
Build the self-referential `metagov-journal` submission via mgj CLI commands.

This is the M7 end-to-end smoke test. It demonstrates the full pipeline
without an LLM call: existing prose in submissions/metagov-journal/specification.md
is preserved as input.md, and the structured RDF is constructed via direct
CLI invocations (the same path the parser would write through after author
confirmation in the inner loop).

Idempotent: every step skips work it has already done. Re-runnable safely.

Usage:
    python scripts/build_self_submission.py
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SLUG = "metagov-journal"


def run(args: list[str], allow_failure: bool = False) -> subprocess.CompletedProcess:
    print(f"  $ mgj {' '.join(args)}")
    result = subprocess.run(["mgj", *args], cwd=REPO, capture_output=True, text=True)
    if result.returncode != 0 and not allow_failure:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        sys.exit(result.returncode)
    return result


def step(name: str) -> None:
    print(f"\n--- {name} ---")


def main() -> None:
    step("seed shared people registry")
    for slug, name in [
        ("michael-zargham", "Michael Zargham"),
        ("joshua-tan", "Joshua Tan"),
        ("seth-frey", "Seth Frey"),
        ("ellie-rennie", "Ellie Rennie"),
    ]:
        run(["people", "add", slug, "--name", name], allow_failure=True)

    step("seed shared organizations registry")
    run(["orgs", "add", "metagov", "--name", "Metagov", "--homepage", "https://metagov.org"], allow_failure=True)

    step("copy specification.md → input.md (preserve original prose)")
    sub_dir = REPO / "submissions" / SLUG
    spec = sub_dir / "specification.md"
    input_md = sub_dir / "input.md"
    if not input_md.exists():
        if spec.exists():
            shutil.copyfile(spec, input_md)
            print(f"  copied {spec} → {input_md}")
        else:
            print(f"  [warn] no specification.md at {spec}; skipping")

    step("init the submission scaffold (idempotent)")
    run(["init", SLUG, "--name", "The Metagov Journal", "--version", "1.0.0", "--date", "2026-04-25"], allow_failure=True)

    step("set narratives (Q1..Q9) — preserved author prose")
    narratives = {
        1: (
            "The Metagov Journal produces and maintains a peer-reviewed commons of "
            "institutional knowledge. Its stable pattern involves practitioners documenting "
            "living institutions through structured catechisms, peers reviewing these "
            "documentations for completeness and clarity, and the community accumulating "
            "reusable organizational patterns. Success manifests as a growing repository of "
            "institutional specifications that practitioners reference when designing new "
            "organizations or evolving existing ones. The institution functions properly "
            "when submissions flow regularly, reviews maintain quality standards, and "
            "documented patterns get reused across contexts."
        ),
        2: (
            "Authors document institutions they understand deeply, answering the catechism "
            "and providing supporting materials. Reviewers evaluate submissions for "
            "completeness, clarity, and contribution to knowledge. Editors (initially Joshua "
            "Tan as lead, with Michael Zargham) coordinate review processes, make publication "
            "decisions, and maintain infrastructure. Readers access documented patterns for "
            "learning and adaptation. Metagov provides organizational home and alignment with "
            "digital self-governance mission, with research directors Seth Frey and Ellie "
            "Rennie providing oversight."
        ),
        3: (
            "The journal operates within overlapping contexts. Technically, it depends on "
            "GitHub for version control and collaboration, technical platforms for archival "
            "storage and DOIs. Academically, it bridges scholarly publishing conventions with "
            "open-source software practices. Legally, it operates under Metagov's nonprofit "
            "structure. Normatively, it inherits from both peer review traditions and GitHub "
            "collaboration patterns. Economically, it functions as a scholarly club good "
            "where contribution enables access to curated knowledge."
        ),
        4: (
            "The foundational rules emerge from three layers. The Catechism (nine questions) "
            "structures all submissions, creating comparable documentation. The Review "
            "Criteria define evaluation standards — completeness, clarity, evidence, "
            "viability, and contribution. The GitHub Flow establishes procedural rules — "
            "fork, submit PR, review, revise, merge."
        ),
        5: (
            "Primary activity occurs at github.com/metagov/journal — submissions, reviews, "
            "and discussions. The Metagov website offers organizational context. Joshua "
            "Tan's introductory blog post articulates the founding vision."
        ),
        6: (
            "As author of this draft, I am a systems engineer and protocol architect with "
            "deep experience in open source communities — my role in Metagov is often to "
            "map systems and provide operational policy recommendations. Joshua Tan, "
            "Metagov co-founder and journal's primary driver, provides vision and "
            "organizational support. We both serve on Metagov's board, creating alignment "
            "but also potential conflicts of interest."
        ),
        7: (
            "The journal emerged from Joshua Tan's observation that governance experiments "
            "in DAOs, cooperatives, and digital communities generate valuable innovations "
            "but lack documentation venues. In late 2024, Tan convened Metagov research "
            "directors to design a solution. The founding team brought complementary "
            "perspectives: Tan (platform governance), Zargham (systems engineering), Frey "
            "(cognitive science), Rennie (digital ethnography)."
        ),
        8: (
            "Evolution operates through multiple mechanisms. Immediate adaptation happens "
            "via GitHub. Periodic review occurs quarterly as editors assess processes and "
            "incorporate lessons. Version control enables framework evolution while "
            "maintaining citation stability through semantic versioning. Community feedback "
            "shapes development through discussions and reviews. Scaling triggers activate "
            "new processes as volume grows."
        ),
        9: (
            "Foundational documents and academic references that ground the journal's "
            "design and motivate its operating model."
        ),
    }
    for q, text in narratives.items():
        run(["narrative", SLUG, "--question", str(q), text])

    step("Q2 — stakeholders")
    for role_label, role_slug, person, resp in [
        ("Editor", "editor", "joshua-tan", "Lead editor; coordinates review and publication."),
        ("Editor", "editor", "michael-zargham", "Co-editor; infrastructure and operations."),
        ("Research Director", "research-director", "seth-frey", "Provides oversight; cognitive-science perspective."),
        ("Research Director", "research-director", "ellie-rennie", "Provides oversight; digital-ethnography perspective."),
    ]:
        run(
            [
                "stakeholder",
                "add",
                SLUG,
                "--role-label",
                role_label,
                "--role-slug",
                role_slug,
                "--person",
                person,
                "--responsibilities",
                resp,
            ]
        )
    # Org-level stakeholder
    run(
        [
            "stakeholder",
            "add",
            SLUG,
            "--role-label",
            "Organizational Home",
            "--role-slug",
            "organizational-home",
            "--org",
            "metagov",
            "--responsibilities",
            "Provides nonprofit infrastructure and mission alignment.",
        ]
    )

    step("Q3 — environmental factors (Lessig modalities)")
    factors = [
        ("Architecture", "GitHub provides version control, peer-review tooling, and collaboration infrastructure."),
        ("Norms", "Inherits scholarly peer-review traditions and open-source GitHub collaboration patterns."),
        ("Markets", "Functions as a scholarly club good: contribution enables access to curated knowledge."),
        ("Law", "Operates under Metagov's nonprofit structure; subject to nonprofit governance regulation."),
    ]
    for modality, desc in factors:
        run(["factor", "add", SLUG, "--modality", modality, "--description", desc])

    step("Q4 — constitutional elements")
    elements = [
        ("Catechism", "Bylaw", "Nine-question framework that structures every submission, creating comparable documentation."),
        ("Review Criteria", "Bylaw", "Evaluation standards — completeness, clarity, evidence, viability, contribution."),
        ("GitHub Flow", "DecisionProcedure", "Procedural rules — fork, submit PR, review, revise, merge."),
        ("Editorial Norms", "Norm", "Constructive feedback tone, reasonable review timelines, transparency in decision-making."),
    ]
    for label, etype, desc in elements:
        run(["constitution", "add", SLUG, "--label", label, "--type", etype, "--description", desc])

    step("Q5 — field sites")
    for label, url, desc in [
        ("GitHub repository", "https://github.com/metagov/metagov-journal", "Primary site for submissions, reviews, and discussion."),
        ("Metagov website", "https://metagov.org", "Organizational home and mission context."),
        ("Founding blog post", "https://journal.metagov.org/2025/08/09/metagov-journal.html", "Joshua Tan's introductory articulation of the journal's vision."),
    ]:
        run(["fieldsite", "add", SLUG, "--label", label, "--url", url, "--description", desc])

    step("Q6 — author disclosure")
    run(
        [
            "author",
            "set",
            SLUG,
            "--person",
            "michael-zargham",
            "--role",
            "co-editor and board member",
            "--disclosure",
            "Author serves on Metagov's board with Joshua Tan; potential conflict of interest. Bootstrap submission receives review from fellow research directors rather than external reviewers. Blind spots likely include overemphasis on technical mechanisms.",
        ]
    )

    step("Q7 — origin event")
    run(
        [
            "origin",
            "add",
            SLUG,
            "--label",
            "Founding convening",
            "--description",
            "In late 2024, Joshua Tan convened Metagov research directors to design a journal for documenting living institutions.",
            "--date",
            "2024-11-01",
            "--persons",
            "joshua-tan,michael-zargham,seth-frey,ellie-rennie",
        ]
    )

    step("Q8 — evolution mechanisms")
    for label, desc in [
        ("PR-driven amendment", "Anyone can propose changes to framework documents through GitHub issues and pull requests."),
        ("Quarterly editorial review", "Editors assess processes and incorporate lessons each quarter."),
        ("Semantic versioning", "Framework evolution preserves citation stability via versioned releases."),
    ]:
        run(["evolution", "add", SLUG, "--label", label, "--description", desc])

    step("Q9 — references")
    # Author bylines are stored as a single dcterms:creator literal so order
    # is preserved (RDF triples are unordered; multi-creator references would
    # otherwise lose authorship sequence). Identifiers are DOI URLs where DOIs
    # exist; bare URLs are kept for refs that don't have one (e.g. blog posts).
    refs = [
        (
            "Introducing the Metagov Journal: Publishing Living Institutions",
            "https://journal.metagov.org/2025/08/09/metagov-journal.html",
            "Tan, J.",
            "2025",
        ),
        (
            "Protocols and Institutions",
            "https://doi.org/10.5281/zenodo.15122312",
            "Zargham, M. & Ben-Meir, I.",
            "2025",
        ),
        (
            "What Constitutes a Constitution?",
            "https://doi.org/10.5281/zenodo.10609125",
            "Zargham, M., Alston, E., Nabben, K., & Ben-Meir, I.",
            "2023",
        ),
        (
            "A Journal is a Club",
            "https://doi.org/10.1080/08109028.2017.1386949",
            "Potts, J., Hartley, J., Montgomery, L., Neylon, C., & Rennie, E.",
            "2017",
        ),
        (
            "Building the Loop: The Role of Ethnography in Artificial Organisational Intelligence",
            "https://doi.org/10.1111/epic.70009",
            "Rennie, E., Nabben, K., Zargham, M., Potts, J., Coco, B.A., Miller, L., & Green, M.",
            "2026",
        ),
    ]
    for title, ident, creators, date in refs:
        run(["reference", "add", SLUG, "--title", title, "--identifier", ident, "--creators", creators, "--date", date])

    step("Legal context")
    run(
        [
            "legal",
            "set",
            SLUG,
            "--host",
            "metagov",
            "--relationship",
            "FiscalSponsor",
            "--description",
            "The journal operates under Metagov's 501(c)(3) nonprofit infrastructure.",
        ]
    )

    step("validate (system SHACL)")
    run(["validate", SLUG])

    step("compile")
    run(["compile", SLUG])

    step("regenerate wiki")
    run(["wiki"])

    print("\n✓ self-submission built end-to-end.")


if __name__ == "__main__":
    main()
