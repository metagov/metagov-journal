# Contributing to the Framework

The journal itself is a living institution — its catechism, evaluation criteria, ontology, and tooling all evolve through the same GitHub-native workflow used for submissions.

## Three modes of contribution

- **Open an [issue](https://github.com/metagov/metagov-journal/issues)** for proposals, gaps, bugs, or questions about the framework. Issues are the right home for "the catechism doesn't account for X" or "the SHACL shape is too strict about Y."

- **Open a PR against framework files**:
  - `catechism.md` — the nine questions
  - `criteria.md`, `evaluation.md` — review standards
  - `ontology/mgj.ttl`, `ontology/shapes/**` — the schema
  - `src/mgj/**` — CLI, parser, compilers
  - `scripts/**` — operational scripts

  Framework PRs follow the same review process as submissions: comment, iterate, merge.

- **Discuss** in the PR thread. Substantive framework changes warrant editorial review and may benefit from broader notice; tag editors when relevant.

## What's a "framework" change vs. a "submission" change?

- A *submission* change touches files only in `submissions/{slug}/` and `shared/` (when adding new people/orgs). It documents an institution.
- A *framework* change touches root-level docs, the ontology, the SHACL shapes, the CLI, or the workflows. It changes how all submissions are written, validated, or published.

The same tooling reviews both — the difference is intent and scope.

## Versioning

The framework follows semantic versioning. Backward-incompatible changes to the catechism or ontology (e.g., adding a required entity type) bump the major version. Submissions are pinned to the version of the framework they were written against.
