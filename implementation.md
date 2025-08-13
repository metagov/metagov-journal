# Implementation: Operational Processes

This document details the concrete processes for operating the Metagov Journal, from submission through publication. These processes are designed to evolve based on experience.

## Technical Infrastructure

### Repository Structure
```
/
├── readme.md
├── background.md
├── catechism.md
├── criteria.md
├── evaluation.md
├── implementation.md
├── CONTRIBUTING.md
├── submissions/
│   └── [institution-name]/
│       ├── manifest.yml
│       ├── specification.md
│       └── supporting/
└── .github/
    └── workflows and templates
```

### Version Management

**Living Documents**: The repository maintains continuous evolution through commits and pull requests.

**Academic References**: Numbered releases (v1.0.0, v1.1.0) create stable citation points. Major versions indicate structural changes; minor versions indicate content updates; patches fix errors.

**Preprint Synchronization**: Each major or minor release triggers upload to Zenodo, obtaining a DOI for academic citation.

## Submission Process

### 1. Preparation
Authors prepare their institutional documentation by:
- Reading the [Catechism](./catechism.md) thoroughly
- Studying the [Specification](./specification.md) example
- Answering all catechism questions
- Gathering supporting materials and references

### 2. Submission
1. Fork the repository
2. Create directory: `submissions/[institution-name]/`
3. Add `specification.md` with catechism answers
4. Create `manifest.yml`:
```yaml
title: "Institution Full Name"
authors:
  - name: "Author Name"
    orcid: "0000-0000-0000-0000"
    affiliation: "Organization"
submitted: "2025-01-15"
status: "under-review"
reviewers: []
decision: "pending"
doi: ""
version: "1.0.0"
```
5. Add supporting materials to `supporting/` directory
6. Submit pull request with description

### 3. Review Assignment
Editors (initially Joshua Tan and Michael Zargham) identify 2-3 appropriate reviewers based on:
- Familiarity with similar institutions
- Complementary expertise
- Availability and willingness

Reviewers are invited via PR comment and manifest update.

## Review Process

### Review Framework
Reviewers evaluate submissions using criteria from [Evaluation](./evaluation.md):
1. Completeness: Are all questions answered?
2. Clarity: Are answers comprehensible?
3. Evidence: Are claims supported by references?
4. Viability: Does the institution appear living?
5. Contribution: Does this advance institutional knowledge?

### Review Submission
Reviewers provide feedback through two channels:
1. **PR Comments**: Specific suggestions and questions
2. **Review Document**: Overall assessment in `reviews/reviewer-name.md`

Review documents should address:
- Strengths of the documentation
- Gaps or unclear elements
- Suggestions for improvement
- Recommendation (accept/revise/reject)

### Editorial Decision
Editors synthesize reviews and make decisions based on:
- Reviewer recommendations
- Alignment with journal mission
- Documentation quality
- Potential for community value

Decisions are documented in the PR and manifest.yml.

## Publication Process

### Acceptance
Upon acceptance:
1. Merge PR to main branch
2. Update manifest with decision and date
3. Create release tag (e.g., `submissions/dao-governance/v1.0.0`)
4. Upload to Zenodo for DOI assignment
5. Update manifest with DOI
6. Announce via Metagov channels

### Post-Publication Updates
Living institutions evolve, so documentation should too:
1. Authors submit update PRs
2. Minor updates merged by editors
3. Major updates may require re-review
4. Version numbers increment accordingly
5. New releases create new DOIs while maintaining history

## Bootstrap Process

The journal's first submission (this documentation) requires special handling:

### Self-Review Mechanism
1. Initial draft by Michael Zargham
2. Review by Joshua Tan and other Metagov research directors
3. Public comment period via GitHub issues
4. Revisions based on feedback
5. Board approval as organizational commitment
6. Merge and tag as v1.0.0

### Transition to Standard Process
After bootstrap:
1. Open for external submissions
2. Expand editorial board
3. Develop reviewer network
4. All subsequent submissions follow standard process

## Evolution Mechanisms

### Process Improvements
- Quarterly editorial review of processes
- Community feedback via issues and discussions
- Process changes via PRs to implementation documents
- Major changes trigger new repository version

### Scaling Considerations
As submissions increase:
- Develop reviewer database
- Create automated checks
- Establish editorial rotation
- Consider section editors for specialized domains

### Quality Assurance
- Regular review of published institutions
- Update notifications for major changes
- Community flagging of issues
- Periodic reassessment of living status

## Roles and Permissions

### GitHub Permissions
- **Editors**: Write access to main branch
- **Reviewers**: Comment access on PRs
- **Authors**: Fork and PR permissions
- **Public**: Read access to all materials

### Editorial Board
Initially:
- Joshua Tan (Lead Editor)
- Michael Zargham (Editor)
- Future: Expand to 5-7 editors

### Review Network
Build through:
- Published authors becoming reviewers
- Invited experts from related fields
- Partner organizations
- Self-nomination with demonstrated expertise

## Tools and Platforms

### Current
- **GitHub**: Primary infrastructure
- **Zenodo**: DOI and archival storage
- **Markdown**: Document format
- **YAML**: Metadata format

### Future Considerations
- Automated validation tools
- Review management system
- Citation tracking
- Impact metrics

This implementation will evolve based on experience. The first year focuses on establishing basic processes, building community, and learning what works. Subsequent iterations will formalize successful practices and address discovered needs.