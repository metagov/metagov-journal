# The Metagov Journal

A peer-reviewed journal for documenting living institutions and their organizational patterns.

## Motivation

Humanity creates institutions—stable patterns of behavior that persist beyond their creators. While traditional scholarship studies institutions from the outside, practitioners need documentation from within: how are these patterns created, maintained, and evolved by specific organizational configurations?

The Metagov Journal addresses this gap by publishing peer-reviewed specifications of living institutions. Each submission answers a structured catechism, documenting not just what an institution does but how its particular arrangement of people, processes, and tools produces stable patterns of collective behavior.

This journal itself is a living institution, evolving through use while maintaining scholarly standards through version control and DOI assignment.

## For Authors

To submit institutional documentation:
1. Review the [Catechism](./catechism.md) - nine questions your documentation must answer
2. Study the [Specification](./specification.md) - example of complete documentation
3. Understand the [Criteria](./criteria.md) - how submissions are evaluated
4. Follow [Contributing](./CONTRIBUTING.md) - technical submission process

## For Reviewers

To participate in peer review:
1. Read the [Evaluation](./evaluation.md) framework
2. Understand the [Criteria](./criteria.md) for assessment
3. See [Contributing](./CONTRIBUTING.md) for reviewer guidelines

## For Readers

To understand the framework:
- [Background](./background.md) - intellectual foundations
- [Catechism](./catechism.md) - core documentation framework
- [Implementation](./implementation.md) - how the journal operates

## Repository Structure

```
/
├── Framework Documents (this level)
├── submissions/
│   └── [institution-name]/
│       ├── manifest.yml
│       ├── specification.md
│       └── supporting/
└── .github/
    └── workflows and templates
```

## Living Documentation

This repository maintains two layers:
1. **Living layer**: Continuous evolution through Git commits and pull requests
2. **Archival layer**: Stable versions released to `<platform>` with DOIs for academic citation
3. **View layer**: Overlay journal model provides space for a metagov-journal specific web-based user experience.

## Governance

The Metagov Journal is a project of [Metagov](https://metagov.org), a nonprofit organization cultivating tools, practices, and communities for digital self-governance.

Initial Editorial Board:
- Joshua Tan (Lead)
- Seth Frey
- Ellie Rennie
- Michael Zargham
- `<tbd>`

## Quick Links

- **Organization**: [Metagov](https://metagov.org)
- **Archive**: [Zenodo Community](https://zenodo.org/communities/metagov)
- **Discussions**: [GitHub Discussions](https://github.com/metagov/metagov-journal/discussions)
- **Issues**: [GitHub Issues](https://github.com/metagov/journal/issues)

## References

### Academic Foundations
- Ostrom, E. (1990). *Governing the Commons: The Evolution of Institutions for Collective Action*. Cambridge University Press.
- Beer, S. (1973). *Designing Freedom*. Anansi Press.
- Lessig, L. (1999). *Code and Other Laws of Cyberspace*. Basic Books.

### Methodological Inspirations
- Heilmeier, G. (1991). The Heilmeier Catechism. DARPA.
- Cordes, R,J., Friedman, D,
& Phelan, S. (2020). ["The Innovator's Catechism: A Tool for Impactful Research."](https://zenodo.org/record/4383230) *Research Practice Methods*.

### Core Framework Papers
- Zargham, M. & Ben-Meir, G. (2024). ["Protocols and Institutions"](https://zenodo.org/records/15122312) appear in *Web3 Blockchain Economic Theory,* edited by Melanie Swan, Soichiro Takagi, and Frank Witte.
-Zargham, M., Alston,E.,Nabben, K, & Ben-Meir, I.(2023) ["What Constitutes a Constitution"](https://zenodo.org/records/10609125) *Metagov Working Papers*.
- Potts, J., Hartley, J., Montgomery, L., Neylon, C., & Rennie, E. (2017). ["A Journal is a Club: A New Economic Model for Scholarly Publishing."](https://www.tandfonline.com/doi/abs/10.1080/08109028.2017.1386949) *Prometheus*, 35(1), 75-92.

### Metagov Context
- Tan, J. (2025). ["Introducing the Metagov Journal: Publishing Living Institutions."](https://journal.metagov.org/2025/08/09/metagov-journal.html)
- [Metagov Website](https://metagov.org): Parent nonprofit advancing digital self-governance
- [GitHub Organization](https://github.com/metagov/): This living document

## License

["Attribution-ShareAlike 4.0 International'](LICENSE)


## Contact

- General inquiries: editors@metagov.org
- Technical issues: Open a GitHub issue
- Submissions: Submit a pull request