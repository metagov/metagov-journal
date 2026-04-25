# Contributing to Infrastructure

Infrastructure contributions evolve the journal's machinery itself — the typed schema, the tooling, and the AI facilitation that every author and reviewer depends on. This is a **distinct mode of participation** from authoring submissions, peer-reviewing them, or serving as an editor: infrastructure contributions improve how *every* submission gets processed, not the substance of any single submission.

## What counts as infrastructure

| Surface | What it does |
| --- | --- |
| `ontology/mgj.ttl` | OWL classes defining the catechism schema |
| `ontology/shapes/**` | SHACL shapes gating validation (per-question + system) |
| `src/mgj/models.py`, `serialize.py` | Pydantic ↔ RDF serialization / deserialization |
| `src/mgj/cli.py`, `src/mgj/commands/**` | The `mgj` command-line interface |
| `src/mgj/compilers/**` | Deterministic compilation: `instance.ttl` → `compiled.md` and the wiki |
| `src/mgj/parser/**` | LLM-assisted catechism extraction — the **AI facilitation layer** |
| `src/mgj/parser/prompts.py` | The prompt templates that shape extraction behavior |
| `.github/workflows/**` | CI: validate, compile, publish the wiki |
| `scripts/**` | Operational scripts (e.g. self-submission rebuild) |

## How to contribute

1. **Open an [issue](https://github.com/metagov/metagov-journal/issues)** describing the gap, proposal, or bug. For non-trivial proposals, discuss in the issue before writing code.
2. **Fork the repo and branch** off `main`.
3. **Make your change.** For ontology / SHACL changes, ensure existing submissions still validate. For CLI / parser changes, add or update tests in `tests/`. For workflow changes, describe what triggers and what side effects.
4. **Open a PR.** `validate.yml` runs `pytest`, SHACL system validation on every submission, and a compile-staleness check.
5. **Code owners review** per [`.github/CODEOWNERS`](https://github.com/metagov/metagov-journal/blob/main/.github/CODEOWNERS). Reviewers check correctness, scope, backwards compatibility (does this break existing submissions?), and alignment with the journal's design principles.
6. **Merge.** Once approved and CI is green, merge to `main` triggers `compile.yml`, which recompiles every `compiled.md` and republishes the wiki.

## Framework changes vs. infrastructure changes

A note on scope: changes to [`catechism.md`](https://github.com/metagov/metagov-journal/blob/main/catechism.md), [`criteria.md`](https://github.com/metagov/metagov-journal/blob/main/criteria.md), or [`evaluation.md`](https://github.com/metagov/metagov-journal/blob/main/evaluation.md) are **framework changes**, not infrastructure changes. They alter what every author must answer or how reviewers evaluate; they warrant **editorial group review** beyond code-owner approval. If you're proposing a catechism question change or a new evaluation criterion, expect a longer discussion.

## How this fits with the other modes

| Role | What they do |
| --- | --- |
| **Reader** | Browses the wiki and repo to learn from documented institutions |
| **Author** | Documents an institution they participate in, answering the catechism |
| **Reviewer** | Peer-reviews open submissions on substance |
| **Editor** | Coordinates review, makes publication decisions (appointed) |
| **Infrastructure contributor** | Improves the schema, tooling, and AI facilitation that everyone else depends on (open — anyone can contribute) |

Recurring substantive infrastructure contributors may be invited into the editorial group over time, but contributing infrastructure doesn't require editorial appointment.
