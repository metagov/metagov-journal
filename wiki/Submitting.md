# Submitting a Specification

Submissions are GitHub pull requests. Authors fork the repository, build their submission with the `mgj` CLI, and open a PR; reviewers comment, the author iterates, editors merge.

## Workflow

1. **Fork** [metagov/metagov-journal](https://github.com/metagov/metagov-journal) and clone your fork.
2. **Read** the [catechism](https://github.com/metagov/metagov-journal/blob/main/catechism.md) and the [evaluation criteria](https://github.com/metagov/metagov-journal/blob/main/criteria.md).
3. **Branch**: `git checkout -b submit/{your-institution-slug}`.
4. **Install the CLI**: `pip install -e .` from the repo root. This makes `mgj` available.
5. **Scaffold**: `mgj init {your-slug} --name "Your Institution"`. This creates `submissions/{your-slug}/` with an `input.md` template.
6. **Author** your `input.md` against the catechism — 75–110 words per question, concrete examples, references where possible.
7. **Build the structured graph**:
    - With LLM extraction: `mgj extract {your-slug}` parses your prose into typed RDF.
    - Or hand-build via CLI commands (`mgj stakeholder add`, `mgj factor add`, etc.) — see `mgj --help` and the [build script](https://github.com/metagov/metagov-journal/blob/main/scripts/build_self_submission.py) as a worked example.
8. **Validate**: `mgj validate {your-slug}` — must pass before review.
9. **Compile**: `mgj compile {your-slug}` writes `compiled.md`. Read it; if it doesn't read naturally, return to step 6 or 7.
10. **Open a PR** against `main`. The `validate.yml` workflow re-runs all checks. Reviewers comment in the PR thread.

## What the editors look for

The [evaluation criteria](https://github.com/metagov/metagov-journal/blob/main/criteria.md) are the formal standard. Briefly: completeness across all nine catechism answers, clarity, evidence (references resolve), demonstrated "living" status, and contribution to the broader catalog.
