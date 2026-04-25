# Contributing to the Metagov Journal

Welcome. The Metagov Journal publishes peer-reviewed documentation of living institutions. This guide is the canonical reference for how to participate; the [wiki](https://github.com/metagov/metagov-journal/wiki) surfaces shorter entry-point pages for each engagement mode.

## Modes of engagement

The journal recognizes five distinct modes of participation:

| Role | What they do | Open or appointed |
| --- | --- | --- |
| **Reader** | Browses the wiki + repo to learn from documented institutions | Open |
| **Author** | Documents an institution they participate in via the catechism | Open |
| **Reviewer** | Peer-reviews open submissions on substance | Open |
| **Editor** | Coordinates review, makes publication decisions | Appointed |
| **Infrastructure Contributor** | Improves the schema, tooling, and AI facilitation that processes every submission | Open |

## For Authors

### Before you submit

1. **Understand the framework**
   - Read the [Catechism](./catechism.md) carefully — the nine questions every submission answers
   - Study the [example submission](./submissions/metagov-journal/compiled.md) — what a published submission looks like
   - Review the [Criteria](./criteria.md) for evaluation standards

2. **Prepare your prose**
   - Answer all nine catechism questions thoroughly (75–110 words each is the typical depth)
   - Gather supporting references and materials
   - Ensure your institution is "living" (active and evolving)

### Submission process

1. **Fork** this repository to your GitHub account, then clone your fork.

2. **Install the `mgj` CLI** from the repo root:

   ```bash
   pip install -e .
   ```

3. **Branch off `main`**:

   ```bash
   git checkout -b submit/[institution-slug]
   ```

4. **Scaffold your submission**:

   ```bash
   mgj init [institution-slug] --name "Institution Name"
   ```

   This creates `submissions/[institution-slug]/` with an `input.md` template, an empty `instance.ttl`, and `extraction-trace.json`.

5. **Author `input.md`** — write prose under each `## N. ...` heading addressing the catechism question. The text under each heading is the answer to that question; the parser uses the heading layout to slice the file.

6. **Build the structured graph**. Two paths:
   - **LLM extraction** (with an Anthropic API key configured):

     ```bash
     mgj extract [slug]
     ```

     Then walk through each question with `mgj review [slug] --question N` to confirm the parser's extraction. Correct via CLI commands as needed (`mgj stakeholder set ...`, `mgj factor remove ...`, etc.); affirm with `mgj affirm [slug] --question N`.
   - **Hand-build via CLI commands** (no LLM required): use `mgj stakeholder add`, `mgj factor add`, `mgj fieldsite add`, etc. See [`scripts/build_self_submission.py`](./scripts/build_self_submission.py) as a worked example for the inaugural self-submission.

7. **Validate**: `mgj validate [slug]` must pass before review.

8. **Compile**: `mgj compile [slug]` writes `compiled.md`. Read it. If the published view doesn't read naturally, return to step 5 or 6.

9. **Open a Pull Request**:
   - Title: `Submission: [Institution Name]`
   - Description: brief summary, special considerations, and any conflict-of-interest disclosures
   - The `validate.yml` workflow runs SHACL validation, pytest, and a compile-staleness check on every push to the PR.

### After submission

- Editors will assign reviewers
- Respond to reviewer comments in the PR thread
- Make revisions via the same `mgj` CLI commands; recompile; push
- Typical review cycle: 2–4 weeks

### Updating published institutions

Living institutions evolve. To update an existing publication:

1. Submit a PR with changes (using `mgj` CLI to mutate `instance.ttl`)
2. Describe what changed and why
3. Minor updates merged by editors quickly
4. Major changes may require re-review and a version bump

## For Reviewers

### Becoming a reviewer

We welcome reviewers with experience in institutional design or governance, familiarity with specific institutional types, and commitment to constructive feedback. Express interest by opening an issue titled `Reviewer Interest: [Your Name]` with relevant background and the institutional domains you can review.

### Review process

When reviewing an open submission:

1. **Read `compiled.md` first** — it's the article view the journal will publish
2. **Cross-check `input.md`** — the author's source prose, especially Q6 disclosure
3. **Spot-check `instance.ttl`** — the structured RDF; you don't need to grok every line, just confirm entities match the prose claims
4. **Apply the [Evaluation Framework](./evaluation.md)** — completeness, clarity, evidence, viability, contribution
5. **Provide feedback** via inline PR comments and a "Review changes" summary; suggest specific revisions and quote the catechism when relevant
6. **Submit review** within two weeks of assignment

You don't need to run the CLI to review — `validate.yml` already handles SHACL validation and the compile-staleness check. Your job is editorial judgment, not mechanical verification.

### Review ethics

- Disclose any conflicts of interest
- Provide constructive, respectful feedback
- Focus on documentation quality, not institutional judgment
- Maintain confidentiality during review

## For Editors

### Editorial responsibilities

- Assign appropriate reviewers
- Synthesize review feedback
- Make publication decisions
- Coordinate the editorial group
- Steward the framework (catechism, criteria, evaluation) over time

### Joining the editorial board

As the journal grows, the editorial board will expand. Candidates typically have:

- Published in the journal as authors
- Served as reviewers
- Demonstrated commitment to the mission

Editorial appointment is by current editorial-group decision. Recurring substantive infrastructure contributors may also be invited.

## For Infrastructure Contributors

The journal's infrastructure — the schema, the CLI, the parser, the compilers, the AI facilitation layer, and the CI workflows — is open to contribution from anyone, distinct from authoring or reviewing submissions.

### Surfaces

| Surface | What it does |
| --- | --- |
| `ontology/mgj.ttl` | OWL classes defining the catechism schema |
| `ontology/shapes/**` | SHACL shapes (per-question + system) |
| `src/mgj/{models,serialize,graph,validate,canonicalize}.py` | RDF ↔ Pydantic, SHACL runner, canonicalization |
| `src/mgj/cli.py`, `src/mgj/commands/**` | the `mgj` CLI surface |
| `src/mgj/compilers/**` | deterministic compilers (catechism + wiki) |
| `src/mgj/parser/**` | LLM-assisted extraction — the AI facilitation layer |
| `src/mgj/parser/prompts.py` | the prompt templates that shape extraction |
| `.github/workflows/**` | CI: validate, compile, publish wiki |
| `scripts/**` | operational scripts |

### Workflow

1. **Open an [issue](https://github.com/metagov/metagov-journal/issues)** describing the gap, proposal, or bug. For non-trivial proposals, discuss in the issue before writing code.
2. **Fork, branch off `main`, make your change** with tests where applicable.
3. **Open a PR**. `validate.yml` runs `pytest`, SHACL system validation on every submission, and a compile-staleness check.
4. **Code-owner review** per [`.github/CODEOWNERS`](./.github/CODEOWNERS). Reviewers check correctness, scope, backwards compatibility, and alignment with the journal's design principles.
5. **Merge** triggers `compile.yml`, which republishes derived artifacts.

### Framework changes vs. infrastructure changes

Changes to [`catechism.md`](./catechism.md), [`criteria.md`](./criteria.md), or [`evaluation.md`](./evaluation.md) are **framework changes**, not infrastructure changes. They alter what every author must answer or how reviewers evaluate; they warrant **editorial-group review** beyond code-owner approval.

## Technical Guidelines

### File naming

- Use lowercase with hyphens: `institution-slug`
- No spaces or special characters
- Keep names concise but descriptive

### Git workflow

- Always work in a fork (or feature branch with write access)
- Keep commits focused and well-described
- One submission per PR
- Rebase on `main` before submitting if `main` has moved substantially

### Markdown formatting

- Use clear headers (`##`, `###`)
- Link as `[text](url)`
- Keep lines reasonable in width

## Community Participation

### Issues

Use [GitHub Issues](https://github.com/metagov/metagov-journal/issues) for bug reports, framework proposals, process clarifications, and reviewer-interest declarations.

### Code of conduct

We follow Metagov's code of conduct: be respectful and inclusive, provide constructive feedback, welcome diverse perspectives, focus on advancing collective knowledge.

## Getting Help

- **Questions**: Open an issue
- **Private concerns**: <editors@metagov.org>

## Recognition

All contributors are recognized:

- Authors receive citation credit
- Reviewers are acknowledged in publications
- Substantive infrastructure contributors may be invited into the editorial group

Thank you for contributing to the commons of institutional knowledge.
