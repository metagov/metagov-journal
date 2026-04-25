# The Metagov Journal

*Submission v1.0.0 — 2026-04-25*

<!-- compiler: mgj.compilers.catechism v0.1.0 -->

## 1. Purpose

The Metagov Journal produces and maintains a peer-reviewed commons of institutional knowledge. Its stable pattern involves practitioners documenting living institutions through structured catechisms, peers reviewing these documentations for completeness and clarity, and the community accumulating reusable organizational patterns. Success manifests as a growing repository of institutional specifications that practitioners reference when designing new organizations or evolving existing ones. The institution functions properly when submissions flow regularly, reviews maintain quality standards, and documented patterns get reused across contexts.

## 2. Stakeholders and roles

The journal recognizes five distinct modes of engagement. Readers access documented patterns for learning and adaptation. Authors document institutions they participate in by answering the catechism. Reviewers peer-review open submissions on substance. Editors coordinate review and make publication decisions. Infrastructure Contributors evolve the schema, tooling, and AI facilitation that processes every submission — an open role flowing through GitHub-native issue and PR workflows under code-owner review. Joshua Tan, Metagov co-founder, is credited with the founding idea — convening the editorial group and articulating the gap a peer-reviewed venue for living-institution documentation could fill. Ilan Ben-Meir and Natalia Dashan, founding contributors, helped develop the conceptual framework — processing Tan's brainstorming into a concrete design Michael Zargham could implement. Zargham serves as lead editor and is credited with the design and development of the catechism framework, review processes, and RDF-native infrastructure. Seth Frey and Ellie Rennie complete the founding editor group with cognitive-science and digital-ethnography perspectives respectively. Liz Barry, Executive Director of Metagov, is responsible for resource allocation and ongoing supervision — assigning staff time, overseeing operations, and ensuring accountability for outcomes. Metagov itself provides the nonprofit home and mission alignment, with three group-level stakeholders within its broader network: Metagov Research Directors form the expertise kernel and are the natural pool from which editors and reviewers are drawn; Metagov Staff provide administrative support, solicit submissions and reviewers, promote publications, secure funding, and document impact; and the Metagov Community — Metagov's broader network of practitioners and researchers engaged with digital self-governance — is the natural source of authors, reviewers, and readers.

### Stakeholders

- **Lead Editor**: Michael Zargham — Lead editor — credit for design and development of the catechism framework, review processes, and RDF-native infrastructure (the mgj toolchain). Coordinates review and publication.
- **Founding Editor**: Joshua Tan — Founding editor — credit for the founding idea; conceived the journal as a venue for documenting living institutions and convened the editorial group. Provides platform-governance perspective.
- **Founding Editor**: Seth Frey — Founding editor; provides cognitive-science perspective.
- **Founding Editor**: Ellie Rennie — Founding editor; provides digital-ethnography perspective.
- **Organizational Sponsor**: Liz Barry — Executive Director of Metagov — credit for resource allocation and ongoing supervision; assigns staff time, oversees operations, and is accountable for program outcomes. The journal program exists as a result of her organizational support.
- **Organizational Home**: Metagov — Provides nonprofit infrastructure and mission alignment.
- **Founding Contributor**: Ilan Ben-Meir — Founding contributor — helped develop the conceptual framework, processing Joshua Tan's brainstorming into a concrete design that Michael Zargham could implement.
- **Founding Contributor**: Natalia Dashan — Founding contributor — helped develop the conceptual framework, processing Joshua Tan's brainstorming into a concrete design that Michael Zargham could implement.
- **Research Directors**: Metagov Research Directors — Expertise kernel of Metagov; the natural pool from which editors and reviewers are drawn.
- **Staff**: Metagov Staff — Provides administrative support: solicits submissions from authors, solicits reviewers, promotes publications to expand readership, secures program funding, and documents impact.
- **Community**: Metagov Community — The natural source of authors, reviewers, and readers — Metagov's broader network of practitioners and researchers engaged with digital self-governance.

## 3. Environmental factors

The journal operates within overlapping contexts. Technically, it depends on GitHub for version control and collaboration, technical platforms for archival storage and DOIs. Academically, it bridges scholarly publishing conventions with open-source software practices. Legally, it operates under Metagov's nonprofit structure. Normatively, it inherits from both peer review traditions and GitHub collaboration patterns. Economically, it functions as a scholarly club good where contribution enables access to curated knowledge.

### Law

- Operates under Metagov's nonprofit structure; subject to nonprofit governance regulation.

### Norms

- Inherits scholarly peer-review traditions and open-source GitHub collaboration patterns.

### Markets

- Functions as a scholarly club good: contribution enables access to curated knowledge.

### Architecture

- GitHub provides version control, peer-review tooling, and collaboration infrastructure.

## 4. Constitution

The foundational rules emerge from three layers. The Catechism (nine questions) structures all submissions, creating comparable documentation. The Review Criteria define evaluation standards — completeness, clarity, evidence, viability, and contribution. The GitHub Flow establishes procedural rules — fork, submit PR, review, revise, merge.

### Bylaw

- **Catechism**: Nine-question framework that structures every submission, creating comparable documentation.
- **Review Criteria**: Evaluation standards — completeness, clarity, evidence, viability, contribution.
- **Engagement Modes**: The journal recognizes five distinct modes of engagement: Reader, Author, Reviewer, Editor, and Infrastructure Contributor. Reader, Author, Reviewer, and Infrastructure Contributor are open roles that anyone can take through the GitHub-native workflow. Editor is an appointed role; recurring substantive infrastructure contributors may be invited into the editorial group over time. The role taxonomy is canonical in the journal's own RDF and surfaced in the wiki engagement docs and contributing.md.

### Norm

- **Editorial Norms**: Constructive feedback tone, reasonable review timelines, transparency in decision-making.

### Decision Procedure

- **GitHub Flow**: Procedural rules — fork, submit PR, review, revise, merge.

## 5. Field sites

The institution operates across connected venues. Primary activity occurs at github.com/metagov/metagov-journal — submissions, reviews, and discussions. The auto-generated wiki is the navigable reader's view, with cross-linked Institution, Person, and Organization pages plus engagement docs. Stable archival citations are planned via Zenodo for DOI assignment. The Metagov website offers organizational context. Joshua Tan's introductory blog post articulates the founding vision.

- [GitHub repository](https://github.com/metagov/metagov-journal) — Primary site for submissions, reviews, and discussion.
- [Metagov website](https://metagov.org) — Organizational home and mission context.
- [Founding blog post](https://journal.metagov.org/2025/08/09/metagov-journal.html) — Joshua Tan's introductory articulation of the journal's vision.

## 6. Author relationship

As author of this draft and current lead editor, I (Michael Zargham) designed and developed the catechism framework, review processes, and RDF-native infrastructure (the mgj toolchain) that this submission demonstrates. Joshua Tan, Metagov co-founder, is credited with the founding idea — he convened the editorial group and articulated the gap this journal addresses. Liz Barry, as Metagov's Executive Director, is responsible for resource allocation and ongoing supervision of the program. Joshua and I both serve on Metagov's board, creating alignment but also potential conflicts of interest. The founding editorial group's review of this self-submission is necessarily reflexive.

*Authored by **Michael Zargham** — lead editor.*

*Disclosure:* Author (Zargham) is the current lead editor and designed/developed the journal's catechism framework, processes, and tooling. Joshua Tan is credited with the founding idea and serves on Metagov's board with the author. Liz Barry, as Executive Director of Metagov, allocates resources and supervises operations. Bootstrap submission receives review from fellow founding editors rather than external reviewers. Blind spots likely include overemphasis on technical mechanisms and the perspective of the tool-builder.

## 7. Origins

The journal emerged from Joshua Tan's observation that governance experiments in DAOs, cooperatives, and digital communities generate valuable innovations but lack documentation venues. In late 2024, Tan convened a founding group to design a solution. The team brought complementary perspectives: Tan (platform governance and the founding idea), Ilan Ben-Meir and Natalia Dashan (conceptual framework development), Zargham (systems engineering and tooling), Frey (cognitive science), Rennie (digital ethnography). The catechism framework emerged through iterative design — processing Tan's framing into a concrete, implementable specification — balancing academic rigor with practitioner accessibility.

- **Founding convening** (2024-11-01): In late 2024, Joshua Tan convened a founding group to design a peer-reviewed venue for documenting living institutions. Ilan Ben-Meir and Natalia Dashan helped develop the conceptual framework; Michael Zargham led the design and implementation; Seth Frey and Ellie Rennie contributed cognitive-science and digital-ethnography perspectives. — *participants: Ellie Rennie, Ilan Ben-Meir, Joshua Tan, Michael Zargham, Natalia Dashan, Seth Frey*

## 8. Evolution

Evolution operates through multiple mechanisms. Immediate adaptation happens via GitHub. Periodic review occurs quarterly as editors assess processes and incorporate lessons. Version control enables framework evolution while maintaining citation stability through semantic versioning. Community feedback shapes development through discussions and reviews. Scaling triggers activate new processes as volume grows.

- **PR-driven amendment**: Anyone can propose changes to framework documents through GitHub issues and pull requests.
- **Quarterly editorial review**: Editors assess processes and incorporate lessons each quarter.
- **Semantic versioning**: Framework evolution preserves citation stability via versioned releases.

## Legal context

*Operates under **Metagov** as fiscal sponsor.*

The journal operates under Metagov's 501(c)(3) nonprofit infrastructure.

## 9. References

Foundational documents and academic references that ground the journal's design and motivate its operating model.

1. Joshua Tan (2025). [Introducing the Metagov Journal](https://journal.metagov.org/2025/08/09/metagov-journal.html)
2. Ilan Ben-Meir, Michael Zargham (2024). [Protocols and Institutions](https://zenodo.org/records/15122312)
3. Michael Zargham (2023). [What Constitutes a Constitution](https://zenodo.org/records/10609125)
4. Jason Potts (2017). [A Journal is a Club](https://www.tandfonline.com/doi/abs/10.1080/08109028.2017.1386949)
5. OpenMBEE Project. [OpenMBEE: Open Model-Based Engineering Environment](https://www.openmbee.org/)
6. Dynamical Systems Group. [Dynamical Systems Group](https://www.dynamicalsystemsgroup.com/)
7. Brooke Ann Coco, Ellie Rennie, Jason Potts, Kelsie Nabben, Luke Miller, Matthew Green, Michael Zargham (2026). [Building the Loop: The Role of Ethnography in Artificial Organisational Intelligence](https://doi.org/10.1111/epic.70009)
