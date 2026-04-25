# Implementation: Operational Processes

This document details the concrete processes for operating the Metagov Journal, from submission through publication. Processes are designed to evolve based on experience.

## Technical Infrastructure

### Repository structure

```text
/
├── readme.md                 # entry point
├── background.md             # intellectual foundations
├── catechism.md              # the 9-question framework
├── criteria.md               # evaluation principles
├── evaluation.md             # reviewer framework
├── contributing.md           # author/reviewer/contributor guide
├── implementation.md         # operational processes (this file)
├── ontology/
│   ├── mgj.ttl                          # OWL classes for the catechism
│   └── shapes/
│       ├── per-question/q{1..9}-*.ttl   # inner-loop SHACL
│       └── system.ttl                   # outer-loop SHACL
├── shared/
│   ├── people.ttl              # canonical foaf:Person registry
│   ├── organizations.ttl       # canonical foaf:Organization registry
│   └── vocabularies.ttl        # SKOS schemes (open: RoleType)
├── submissions/
│   └── [institution-slug]/
│       ├── input.md            # author's prose answering the catechism
│       ├── instance.ttl        # canonical RDF (CLI-managed; never hand-edited)
│       ├── compiled.md         # generated published article
│       └── extraction-trace.json   # parser provenance + per-Q affirmation log
├── wiki/                     # auto-generated cross-linked wiki; published to GitHub Wiki
├── src/mgj/                  # mgj CLI tool implementation
├── scripts/                  # operational scripts
└── .github/
    ├── CODEOWNERS
    └── workflows/{validate,compile}.yml
```

### Pipeline overview

The journal uses an **RDF-native** pipeline. The technical pattern is described academically in Rennie et al. (2026), "Building the Loop," which articulates Knowledge Organisation Infrastructure (KOI) — the protocol this journal applies to peer-reviewed institutional documentation.

1. **Author writes prose** in `input.md` — the canonical text source.
2. **Parser extracts typed RDF** (LLM-assisted via Anthropic Claude or hand-built via the `mgj` CLI) into `instance.ttl`.
3. **SHACL validates** the structured graph (per-question shapes during authoring; system shape before merge).
4. **Compiler generates** `compiled.md` (the published article) and the wiki cross-links from `instance.ttl`.
5. **CI republishes** derived artifacts on every merge to `main`.

Authors **never edit `instance.ttl` directly** — every mutation flows through the `mgj` CLI, which canonicalizes the on-disk Turtle (URDNA2015 + sorted serialization) and runs SHACL validation atomically.

### Version management

**Living layer**: continuous evolution through Git commits and pull requests.

**Archival layer**: numbered releases (`v1.0.0`, `v1.1.0`) create stable citation points. Major versions indicate structural changes; minor versions indicate content updates; patches indicate errors. Each release is uploaded to Zenodo for DOI assignment (planned; operational details TBD).

**Determinism invariant**: for fixed `(instance.ttl, compiler_version)`, `compiled.md` and the wiki are byte-stable across runs. The `validate.yml` staleness check enforces this.

## Submission Process

### 1. Preparation

Authors prepare their institutional documentation by:

- Reading the [Catechism](./catechism.md) thoroughly
- Studying the [example submission](./submissions/metagov-journal/compiled.md)
- Drafting answers to all nine catechism questions

### 2. Submission

1. Fork the repository, clone, and `pip install -e .` to install `mgj`
2. Branch: `git checkout -b submit/[institution-slug]`
3. Scaffold: `mgj init [institution-slug] --name "Institution Name"`
4. Author `input.md` answering Q1–Q9
5. Build the structured graph: `mgj extract [slug]` (LLM-assisted) or hand-build via `mgj stakeholder add`, `mgj factor add`, etc.
6. Validate: `mgj validate [slug]` (must pass)
7. Compile: `mgj compile [slug]` writes `compiled.md`
8. Submit pull request titled `Submission: [Institution Name]`

The PR triggers `validate.yml`: pytest, SHACL system validation per submission, and a compile-staleness check.

### 3. Review assignment

Editors identify 2–3 appropriate reviewers based on familiarity with similar institutions, complementary expertise, and availability.

## Review Process

### Review framework

Reviewers evaluate submissions using criteria from [Evaluation](./evaluation.md):

1. **Completeness** — are all questions answered?
2. **Clarity** — are answers comprehensible?
3. **Evidence** — are claims supported by references?
4. **Viability** — does the institution appear living?
5. **Contribution** — does this advance institutional knowledge?

### Review submission

Reviewers provide feedback through GitHub's PR review tools:

1. **Read `compiled.md` first** — the article view
2. **Cross-check `input.md`** — the prose source
3. **Spot-check `instance.ttl`** — verify structured entities match prose claims
4. **Use inline PR comments + a "Review changes" summary** in GitHub's PR review UI

### Editorial decision

Editors synthesize reviews and decide based on reviewer recommendations, alignment with the journal's mission, documentation quality, and community value. Decisions are documented in the PR thread.

## Publication Process

### Acceptance

Upon acceptance:

1. Merge PR to `main`
2. `compile.yml` automatically regenerates `compiled.md` and republishes the wiki
3. Create release tag (e.g., `submissions/[slug]/v1.0.0`)
4. Upload to Zenodo for DOI (planned)
5. Announce via Metagov channels

### Post-publication updates

Living institutions evolve, so documentation should too:

1. Authors submit update PRs (using `mgj` CLI to mutate `instance.ttl`)
2. Minor updates merged by editors
3. Major updates may require re-review
4. New version tags create new DOI references while preserving history

## Roles and Engagement Modes

The journal recognizes **five distinct modes of engagement**:

| Role | Open or appointed | Primary surface |
| --- | --- | --- |
| **Reader** | Open | Wiki + repo |
| **Author** | Open | `submissions/[slug]/` PRs |
| **Reviewer** | Open | PR review tools |
| **Editor** | Appointed | Editorial decisions, board membership |
| **Infrastructure Contributor** | Open | `src/mgj/`, `ontology/`, `.github/`, `scripts/` PRs |

Authors, reviewers, and infrastructure contributors are **open** roles — anyone can participate. Editors are **appointed**. The full editorial structure for the journal is canonical in [`submissions/metagov-journal/instance.ttl`](./submissions/metagov-journal/instance.ttl).

### GitHub permissions

- **Editors**: write access to `main`; admin role on the repo with bypass on the branch-protection ruleset
- **Reviewers**: comment access on PRs (default for any GitHub user on a public repo)
- **Authors / Infrastructure Contributors**: fork-and-PR (default)
- **Public**: read access (the repo is public)

The [`.github/CODEOWNERS`](./.github/CODEOWNERS) file routes review requests for every PR to the lead editor by default; as the editorial group expands, patterns can be refined to route specific subtrees (e.g., `submissions/` to specific submission authors, `ontology/` to framework maintainers).

## Bootstrap Process

The journal's first submission (this documentation, in `submissions/metagov-journal/`) requires special handling. The bootstrap is reflexive: the journal's own machinery is documented as the inaugural submission and demonstrates viability through self-application.

### Self-review mechanism

1. Initial draft by Michael Zargham (lead editor)
2. Review by Joshua Tan and other founding editors
3. Public comment period via GitHub issues
4. Revisions via PR
5. Editorial-group approval
6. Tag as `v1.0.0`; upload to Zenodo (planned)

### Transition to standard process

After bootstrap:

1. Open for external submissions
2. Expand editorial board
3. Develop reviewer network
4. All subsequent submissions follow the standard process described above

## Evolution Mechanisms

### Process improvements

- Quarterly editorial review of processes
- Community feedback via issues and PR threads
- Process changes via PRs to framework documents (this file, `catechism.md`, `criteria.md`, `evaluation.md`)
- Major changes trigger a new framework version

### Scaling considerations

As submissions increase:

- Develop reviewer network
- Refine `CODEOWNERS` patterns to route specific subtrees
- Establish editorial rotation
- Consider section editors for specialized domains

### Quality assurance

- Regular review of published institutions
- Update notifications for major changes
- Community flagging of issues
- Periodic reassessment of "living" status

## Tools and Platforms

### Current

- **GitHub**: primary infrastructure (repo, Wiki, Issues, Actions)
- **Zenodo** (planned): DOI and archival
- **Markdown**: prose format (`input.md`, `compiled.md`, framework docs)
- **RDF / Turtle**: canonical structured format (`instance.ttl`, shared registries)
- **OWL + SHACL**: schema and validation
- **Anthropic Claude**: AI-assisted catechism extraction (provider-agnostic; backend abstraction lives in `src/mgj/parser/backends.py` so other LLM providers can be plugged in)

### Future considerations

- Citation tracking
- Impact metrics
- Section-specialized SHACL profiles
- Extended ontology coverage for specific institution types

This implementation will evolve based on experience. The first year focuses on establishing basic processes, building community, and learning what works. Subsequent iterations will formalize successful practices and address discovered needs.
