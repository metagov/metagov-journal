# Contributing to the Metagov Journal

Welcome! The Metagov Journal publishes peer-reviewed documentation of living institutions. This guide explains how to participate as an author, reviewer, or editor.

## For Authors

### Before You Submit

1. **Understand the Framework**
   - Read the [Catechism](./catechism.md) carefully
   - Study the [Specification](./specification.md) example
   - Review [Criteria](./criteria.md) for evaluation standards

2. **Prepare Your Documentation**
   - Answer all catechism questions thoroughly
   - Gather supporting references and materials
   - Ensure your institution is "living" (active and evolving)

### Submission Process

1. **Fork this repository** to your GitHub account

2. **Create your submission directory**:
   ```
   submissions/your-institution-name/
   ├── manifest.yml
   ├── specification.md
   └── supporting/
       └── (additional materials)
   ```

3. **Write your specification.md**:
   - Answer each catechism question by number
   - Provide concrete examples and references
   - Aim for 700-1000 words

4. **Create manifest.yml**:
   ```yaml
   title: "Your Institution Name"
   authors:
     - name: "Your Name"
       orcid: "0000-0000-0000-0000"  # Optional
       affiliation: "Your Organization"
   submitted: "2025-MM-DD"
   status: "under-review"
   reviewers: []  # Editors will assign
   decision: "pending"
   doi: ""  # Added after publication
   version: "1.0.0"
   ```

5. **Submit a Pull Request**:
   - Title: `Submission: [Institution Name]`
   - Description: Brief summary and any special considerations
   - Tag: `submission`

### After Submission

- Editors will assign reviewers within one week
- Respond to reviewer comments in the PR
- Make revisions as requested
- Typical review cycle: 2-4 weeks

### Updating Published Institutions

Living institutions evolve! Update your documentation:
1. Submit a PR with changes
2. Describe what changed and why
3. Minor updates merged quickly
4. Major changes may require re-review

## For Reviewers

### Becoming a Reviewer

We welcome reviewers with:
- Experience in institutional design or governance
- Familiarity with specific institutional types
- Commitment to constructive feedback

Express interest by:
- Opening an issue titled "Reviewer Interest: [Your Name]"
- Describing your relevant experience
- Listing institutional domains you can review

### Review Process

When assigned a review:

1. **Read the submission** thoroughly

2. **Evaluate against criteria**:
   - Completeness of answers
   - Clarity of documentation
   - Evidence for claims
   - Institutional viability
   - Knowledge contribution

3. **Provide feedback**:
   - **PR Comments**: Specific line-by-line suggestions
   - **Review Document**: Create `reviews/your-name.md`:
     ```markdown
     # Review of [Institution Name]
     
     ## Summary
     [Overall assessment]
     
     ## Strengths
     - [What works well]
     
     ## Areas for Improvement
     - [What needs work]
     
     ## Specific Suggestions
     - [Actionable feedback]
     
     ## Recommendation
     [Accept/Minor Revisions/Major Revisions/Reject]
     ```

4. **Submit review** within two weeks

### Review Ethics

- Disclose any conflicts of interest
- Provide constructive, respectful feedback
- Focus on documentation quality, not institutional judgment
- Maintain confidentiality during review

## For Editors

### Editorial Responsibilities

- Assign appropriate reviewers
- Synthesize review feedback
- Make publication decisions
- Maintain repository infrastructure
- Facilitate community discussions

### Joining the Editorial Board

As the journal grows, we'll expand the editorial board. Candidates should have:
- Published in the journal as authors
- Served as reviewers
- Demonstrated commitment to the mission

## Technical Guidelines

### Markdown Formatting

- Use clear headers (##, ###)
- Number catechism answers
- Include links as `[text](url)`
- Keep lines under 100 characters

### File Naming

- Use lowercase with hyphens: `institution-name`
- No spaces or special characters
- Keep names concise but descriptive

### Git Workflow

1. Always work in a fork
2. Keep commits focused and well-described
3. One submission per PR
4. Rebase on main before submitting

## Community Participation

### Discussions

- Use [GitHub Discussions](https://github.com/metagov/journal/discussions) for:
  - General questions
  - Process improvements
  - Community announcements

### Issues

- Use [GitHub Issues](https://github.com/metagov/journal/issues) for:
  - Bug reports
  - Feature requests
  - Process clarifications

### Code of Conduct

We follow Metagov's code of conduct:
- Be respectful and inclusive
- Provide constructive feedback
- Welcome diverse perspectives
- Focus on advancing collective knowledge

## Getting Help

- **Questions**: Open a discussion
- **Problems**: Open an issue
- **Private concerns**: Email editors@metagov.org

## Recognition

All contributors are recognized:
- Authors receive citation credit
- Reviewers are acknowledged in publications
- Active participants join the editorial board

Thank you for contributing to the commons of institutional knowledge!