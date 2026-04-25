# The Metagov Journal

A peer-reviewed journal for documenting living institutions and their organizational patterns.

## Motivation

Humanity creates institutions—stable patterns of behavior that persist beyond their creators. While traditional scholarship studies institutions from the outside, practitioners need documentation from within: how are these patterns created, maintained, and evolved by specific organizational configurations?

The Metagov Journal addresses this gap by publishing peer-reviewed specifications of living institutions. Each submission answers a structured catechism, documenting not just what an institution does but how its particular arrangement of people, processes, and tools produces stable patterns of collective behavior.

This journal itself is a living institution, evolving through use while maintaining scholarly standards through version control and DOI assignment.

## Attribution and Methodological Lineage

The technical approach used in this repository — schema-driven Git+RDF authoring, deterministic compilation from canonical Turtle to Markdown, SHACL-validated structured documentation, and the inner-loop / outer-loop pattern for author-confirmed extraction — is **derived from prior work carried out by Michael Zargham** in two settings whose contributions we cite explicitly:

- **[OpenMBEE](https://www.openmbee.org/)** (Open Model-Based Engineering Environment) pioneered formal documentation and Model Management Systems built on **Git and RDF**. The Metagov Journal's pattern of treating the typed RDF graph as source-of-truth and compiled Markdown/wiki views as derived artifacts originates in OpenMBEE practice.

- **[Dynamical Systems Group](https://www.dynamicalsystemsgroup.com/)** operationalized that research into specific document classes used in engineering programs — **Technology Readiness Levels (TRLs)**, **Requirements Traceability Matrices (RTMs)**, and **MOSA (Modular Open Systems Approach) Product Management**. The catechism-driven, SHACL-gated authoring loop and the per-question entity-extraction pipeline used here are direct adaptations of Dynamical Systems Group tooling, recast for institutional documentation rather than technology-readiness assessment.

Proper attribution matters to us: the Metagov Journal exists in the form it does — schema-first, deterministic, content-addressable — because of those prior contributions. The catechism-as-schema approach, the determinism invariant for compiled artifacts, and the PROV-O extraction provenance were developed in the engineering-documentation context first and ported here under the same author's continuity.

## For Authors

To submit institutional documentation:
1. Review the [Catechism](./catechism.md) - nine questions your documentation must answer
2. Study the [example submission](./submissions/metagov-journal/compiled.md) - what a complete, published submission looks like
3. Understand the [Criteria](./criteria.md) - how submissions are evaluated
4. Follow [Contributing](./contributing.md) - technical submission process

## For Reviewers

To participate in peer review:
1. Read the [Evaluation](./evaluation.md) framework
2. Understand the [Criteria](./criteria.md) for assessment
3. See [Contributing](./contributing.md) for reviewer guidelines

## For Readers

To understand the framework:

- [Background](./background.md) - intellectual foundations
- [Catechism](./catechism.md) - core documentation framework
- [Implementation](./implementation.md) - how the journal operates

## For Infrastructure Contributors

The schema, tooling, and AI-facilitation layer that processes every submission are themselves open to contribution — distinct from authoring or reviewing. Surfaces include the OWL ontology, SHACL shapes, the `mgj` CLI, the serialization/deserialization layer, the compilers, the parser prompts, and the CI workflows.

To contribute infrastructure:

1. Open an [issue](https://github.com/metagov/metagov-journal/issues) describing the gap, proposal, or bug
2. Fork, branch, make your change with tests where applicable
3. Open a PR — code owners review per [`.github/CODEOWNERS`](./.github/CODEOWNERS)
4. See the wiki's [Contributing](https://github.com/metagov/metagov-journal/wiki/Contributing) page for the full surface inventory and review expectations

Note: changes to the catechism, criteria, or evaluation docs are *framework* changes (different from infrastructure changes) and warrant editorial-group review beyond code-owner approval.

## Repository Structure

```
/
├── readme.md
├── background.md             # intellectual foundations
├── catechism.md              # the 9-question framework
├── criteria.md               # evaluation principles
├── evaluation.md             # reviewer framework
├── contributing.md           # author/reviewer guide
├── implementation.md         # operational processes
├── ontology/                 # OWL schema + SHACL shapes
├── shared/                   # canonical people/orgs/role registries
├── submissions/
│   └── [institution-slug]/
│       ├── input.md          # author's prose answering the catechism
│       ├── instance.ttl      # canonical RDF graph (CLI-managed)
│       ├── compiled.md       # generated published article
│       └── extraction-trace.json
├── wiki/                     # auto-generated; published to GitHub Wiki
├── src/mgj/                  # mgj CLI tool implementation
├── scripts/                  # operational scripts (e.g. self-submission build)
└── .github/                  # CODEOWNERS + validate/compile workflows
```

## Living Documentation

This repository maintains two layers:
1. **Living layer**: Continuous evolution through Git commits and pull requests
2. **Archival layer**: Stable versions released to `<platform>` with DOIs for academic citation
3. **View layer**: Overlay journal model provides space for a metagov-journal specific web-based user experience.

## Governance

The Metagov Journal is a program of [Metagov](https://metagov.org), a nonprofit organization cultivating tools, practices, and communities for digital self-governance. **Liz Barry**, Metagov's Executive Director, is responsible for resource allocation and ongoing supervision of the program — assigning staff time, overseeing operations, and ensuring accountability for outcomes.

**Lead Editor:** Michael Zargham — credit for the design and development of the catechism framework, review processes, and RDF-native infrastructure.

**Founding Editors** — the convening editorial group:

- Joshua Tan — credit for the founding idea
- Seth Frey — cognitive-science perspective
- Ellie Rennie — digital-ethnography perspective

**Founding Contributors** — helped develop the conceptual framework that bridges Tan's brainstorming to Zargham's implementation:

- Ilan Ben-Meir
- Natalia Dashan

The full structured stakeholder graph for the journal is canonical in [`submissions/metagov-journal/instance.ttl`](./submissions/metagov-journal/instance.ttl) and rendered as a navigable view in the [wiki](https://github.com/metagov/metagov-journal/wiki).

## Quick Links

- **Organization**: [Metagov](https://metagov.org)
- **Wiki**: [navigable index of submissions, people, and engagement docs](https://github.com/metagov/metagov-journal/wiki)
- **Archive**: planned via Zenodo for stable DOI citations (operational details TBD)
- **Issues**: [GitHub Issues](https://github.com/metagov/metagov-journal/issues)

## References

### Academic Foundations
- Ostrom, E. (1990). *Governing the Commons: The Evolution of Institutions for Collective Action*. Cambridge University Press.
- Beer, S. (1973). *Designing Freedom*. Anansi Press.
- Lessig, L. (1999). *Code and Other Laws of Cyberspace*. Basic Books.

### Methodological Inspirations
- Heilmeier, G. (1991). The Heilmeier Catechism. DARPA.
- Cordes, R,J., Friedman, D,
& Phelan, S. (2020). ["The Innovator's Catechism: Operations orders for use by early-stage innovation teams"](https://zenodo.org/record/4383230) *Research Practice Methods*.

### Core Framework Papers
- Zargham, M. & Ben-Meir, G. (2024). ["Protocols and Institutions"](https://zenodo.org/records/15122312) appear in *Web3 Blockchain Economic Theory,* edited by Melanie Swan, Soichiro Takagi, and Frank Witte.
- Zargham, M., Alston,E.,Nabben, K, & Ben-Meir, I.(2023) ["What Constitutes a Constitution"](https://zenodo.org/records/10609125) *Metagov Working Papers*.
- Potts, J., Hartley, J., Montgomery, L., Neylon, C., & Rennie, E. (2017). ["A Journal is a Club: A New Economic Model for Scholarly Publishing."](https://www.tandfonline.com/doi/abs/10.1080/08109028.2017.1386949) *Prometheus*, 35(1), 75-92.

### Metagov Context
- Tan, J. (2025). ["Introducing the Metagov Journal: Publishing Living Institutions."](https://journal.metagov.org/2025/08/09/metagov-journal.html)
- [Metagov Website](https://metagov.org): Parent nonprofit advancing digital self-governance
- [GitHub Organization](https://github.com/metagov/): The Github Organization for Metagov where the Metagov Journal is one repository.

## License

["Attribution-ShareAlike 4.0 International"](LICENSE)

All institutions published in the Metagov Journal via this github based framework will inherit CC-BY-SA-4 license designation, and have the Metagov-Journal Institution as a cited reference.

## Contact

- General inquiries: editors@metagov.org
- Technical issues: Open a GitHub issue
- Submissions: Submit a pull request
