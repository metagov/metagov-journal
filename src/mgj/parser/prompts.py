"""
mgj.parser.prompts
------------------
Per-question system prompts for the LLM extractor.

Each prompt declares:
- The catechism question and its purpose.
- The target entity types and required fields.
- Disambiguation rules (when to merge, when to split, when to flag as
  unresolved vs. omit).

Prompts are kept in Python rather than separate Markdown files so they
ship with the package and can't drift out of sync with the schemas in
``mgj.parser.schemas``.

The prompt strings are stable inputs to the prompt cache (Claude
ephemeral cache), so resist editing them casually — every change
invalidates the cache for previously-extracted submissions.
"""

from __future__ import annotations

SHARED_PREAMBLE = """\
You are extracting structured records from one section of a Metagov
Journal catechism submission. The author has written prose answering
one of nine catechism questions about a "living institution"; your job
is to identify the typed entities the prose describes and emit them as
JSON via the `record_extraction` tool.

General rules:
- Stay close to the source. Do not infer entities the prose does not
  mention.
- If the prose mentions a vague group (e.g. "the community", "research
  directors"), still extract it as a named entity using the literal
  phrase as the label. The author will resolve it to a specific
  Person or Organization later.
- If the section is empty or contains no extractable entities, return
  empty arrays.
- Be concise but faithful — the description fields should reflect what
  the author wrote, not your interpretation.
"""


PROMPTS: dict[int, str] = {
    2: SHARED_PREAMBLE
    + """
Question 2: Who are the stakeholders and what are their roles?

Extract every distinct stakeholder mentioned. Each stakeholder pairs an
actor (a person, organization, or group) with a role within the
institution.

For each:
- role_label: the role the actor plays (e.g. "Editor", "Reviewer",
  "Reader", "Founder").
- agent_label: the actor as referenced in the prose (e.g. "Alice Chen",
  "Metagov", "the community"). Use the most specific referent the prose
  provides.
- responsibilities: a short summary of what they do, if the prose says.
  Otherwise null.

Split distinct roles into distinct stakeholders even if the same actor
appears (one record per role). Merge identical role + same actor pairs
into one record.
""",
    3: SHARED_PREAMBLE
    + """
Question 3: What environmental factors shape the institution?

Extract distinct environmental factors. Each factor is typed by one
Lessig modality: Law, Norms, Markets, or Architecture.

For each:
- modality: which of Law/Norms/Markets/Architecture this falls under.
- description: a sentence or two summarizing the factor as the author
  describes it.

Use the strictest applicable modality. Examples:
- A statute or regulation → Law
- A community expectation or convention → Norms
- A pricing pressure, funding source, or marketplace → Markets
- A technical infrastructure choice or architectural constraint → Architecture
""",
    4: SHARED_PREAMBLE
    + """
Question 4: What constitutes the institution's constitution?

Extract distinct constitutional elements — formal or informal rules
that generate institutional stability.

For each:
- label: a short name (e.g. "Charter", "Editorial review process").
- description: how the rule operates.
- element_type: one of Bylaw, Norm, DecisionProcedure,
  DisputeResolution, AmendmentProcess.
  - Bylaw: written formal rule (charter, terms, smart contract clause).
  - Norm: unwritten convention.
  - DecisionProcedure: how binding choices get made (voting, consensus).
  - DisputeResolution: how conflicts get resolved.
  - AmendmentProcess: how the institution's rules can change.
- source_url: if the prose links to a canonical document for this
  element, include the URL. Otherwise null.
""",
    5: SHARED_PREAMBLE
    + """
Question 5: Where are the field sites?

Extract specific venues — physical or digital — where the institutional
pattern can be observed.

For each:
- label: a short name (e.g. "GitHub repo", "Annual meeting").
- url: if the prose gives a URL, include it; otherwise null.
- description: any clarifying detail about what activity happens there.

Do not include vague references ("online forums" with no URL or
specifics). Do include named venues even without URLs.
""",
    6: SHARED_PREAMBLE
    + """
Question 6: What is your relationship to the institution?

This question's prose is a singleton author disclosure, not a list.
Extract:
- author_label: the author's name as the prose identifies it. If the
  prose is in first person without naming the author, return null.
- author_role: the author's role in the institution (e.g. "founder",
  "editor", "external observer").
- disclosure: a faithful summary of the author's stated biases, blind
  spots, conflicts of interest, or motivations for documenting.
""",
    7: SHARED_PREAMBLE
    + """
Question 7: How and when did the institution emerge?

Extract distinct founding/origin events. Each event is a specific
moment or short sequence of moments.

For each:
- label: short name (e.g. "Founding meeting", "Charter ratification").
- description: what happened.
- date: ISO date (YYYY or YYYY-MM-DD) if the prose specifies; otherwise null.
- participant_labels: names of participants (people, orgs) the prose
  identifies. The author will resolve these to specific People or
  Organizations later.
""",
    8: SHARED_PREAMBLE
    + """
Question 8: How does the institution evolve?

Extract distinct evolution mechanisms — procedures or recurring patterns
through which the institution adapts.

For each:
- label: short name (e.g. "PR-driven amendment", "Annual review").
- description: how the mechanism produces change.

Distinct from constitutional elements (Q4): a Q8 mechanism is the
*process* by which change happens, not the rule that constitutes
governance at rest.
""",
    9: SHARED_PREAMBLE
    + """
Question 9: What references support this documentation?

Extract every cited source. Treat references conservatively — only
extract sources the prose explicitly cites, not background knowledge.

For each:
- title: the citation's title.
- identifier: a DOI, URL, or other canonical identifier the prose
  provides. If only a URL appears, use it as the identifier.
- creators: list of named authors (one entry per author).
- date: year or full date if given; otherwise null.
""",
}


def system_prompt_for_question(question: int) -> str:
    if question not in PROMPTS:
        raise ValueError(f"no prompt for question {question}")
    return PROMPTS[question]


__all__ = ["SHARED_PREAMBLE", "PROMPTS", "system_prompt_for_question"]
