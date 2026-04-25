"""
mgj.compilers.wiki
------------------
Auto-generate cross-linked wiki pages from the full Metagov Journal graph.

Pages produced (one Markdown file each):
    Home.md                  Index of all institutions and people
    Institution-{slug}.md    Per-institution view (rendered via the catechism compiler)
    Person-{slug}.md         Person dossier with backlinks
    Organization-{slug}.md   Organization dossier with backlinks

Determinism: queries are ORDER BYed and post-sorted; output is byte-stable
for a fixed graph state across runs.
"""

from __future__ import annotations

from pathlib import Path

from rdflib import Graph

from mgj import graph as graph_mod
from mgj.compilers.catechism import compile_submission
from mgj.graph import load_ontology, sparql_select
from mgj.namespaces import MGJ

WIKI_COMPILER_VERSION = "0.1.0"
WIKI_COMPILER_ID = "mgj.compilers.wiki"


# ---------------------------------------------------------------------------
# Graph loading — full repo
# ---------------------------------------------------------------------------


def load_full_graph() -> Graph:
    """Merge ontology + every shared/*.ttl + every submissions/*/instance.ttl.

    Reads ``mgj.graph.SHARED_DIR`` and ``mgj.graph.SUBMISSIONS_DIR`` via
    the module so test monkeypatching of those attributes is observed.
    """
    g = load_ontology()
    if graph_mod.SHARED_DIR.is_dir():
        for ttl in sorted(graph_mod.SHARED_DIR.glob("*.ttl")):
            g.parse(str(ttl), format="turtle")
    if graph_mod.SUBMISSIONS_DIR.is_dir():
        for instance in sorted(graph_mod.SUBMISSIONS_DIR.glob("*/instance.ttl")):
            g.parse(str(instance), format="turtle")
    return g


# ---------------------------------------------------------------------------
# Top-level entry: write all pages into ``output_dir``
# ---------------------------------------------------------------------------


def compile_wiki(output_dir: str | Path) -> list[Path]:
    """Generate the full wiki tree. Returns the list of files written."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    g = load_full_graph()

    written: list[Path] = []

    # Home
    home = out / "Home.md"
    home.write_text(_render_home(g))
    written.append(home)

    # Institution pages
    for inst in _institution_index(g):
        page = out / f"Institution-{_slug_from_iri(inst['inst'])}.md"
        page.write_text(_render_institution_page(g, inst))
        written.append(page)

    # Person pages
    for person in _person_index(g):
        page = out / f"Person-{_slug_from_iri(person['p'])}.md"
        page.write_text(_render_person_page(g, person))
        written.append(page)

    # Organization pages
    for org in _org_index(g):
        page = out / f"Organization-{_slug_from_iri(org['o'])}.md"
        page.write_text(_render_org_page(g, org))
        written.append(page)

    return sorted(written)


# ---------------------------------------------------------------------------
# Indexes
# ---------------------------------------------------------------------------


def _institution_index(g: Graph) -> list[dict[str, str]]:
    return sparql_select(
        g,
        """
        SELECT ?inst ?name WHERE {
            ?inst a mgj:Institution ; mgj:institutionName ?name .
        } ORDER BY ?name
        """,
    )


def _person_index(g: Graph) -> list[dict[str, str]]:
    return sparql_select(
        g,
        """
        SELECT ?p ?name WHERE {
            ?p a foaf:Person ; foaf:name ?name .
        } ORDER BY ?name
        """,
    )


def _org_index(g: Graph) -> list[dict[str, str]]:
    return sparql_select(
        g,
        """
        SELECT ?o ?name WHERE {
            ?o a foaf:Organization ; foaf:name ?name .
        } ORDER BY ?name
        """,
    )


# ---------------------------------------------------------------------------
# Page renderers
# ---------------------------------------------------------------------------


def _render_home(g: Graph) -> str:
    lines = ["# Metagov Journal", ""]
    lines.append(f"<!-- compiler: {WIKI_COMPILER_ID} v{WIKI_COMPILER_VERSION} -->")
    lines.append("")

    # Engagement section — links to the hand-authored pages that describe
    # how readers, authors, reviewers, and contributors participate. Page
    # files (Reading.md, Submitting.md, Reviewing.md, Contributing.md) are
    # checked into wiki/ in the repo and published alongside the auto-
    # generated catalog.
    lines.extend(
        [
            "## How to engage",
            "",
            "- [Reading the journal](Reading) — discover and read institutional specifications",
            "- [Submitting a specification](Submitting) — author and submit a new specification",
            "- [Participating in review](Reviewing) — peer-review open submissions",
            "- [Contributing to infrastructure](Contributing) — improve the schema, CLI, parser, compilers, and CI that everyone depends on",
            "",
        ]
    )

    institutions = _institution_index(g)
    lines.append("## Institutions")
    lines.append("")
    if institutions:
        for inst in institutions:
            slug = _slug_from_iri(inst["inst"])
            lines.append(f"- [{inst['name']}](Institution-{slug})")
    else:
        lines.append("*(none yet)*")
    lines.append("")

    people = _person_index(g)
    lines.append("## People")
    lines.append("")
    if people:
        for p in people:
            slug = _slug_from_iri(p["p"])
            lines.append(f"- [{p['name']}](Person-{slug})")
    else:
        lines.append("*(none yet)*")
    lines.append("")

    orgs = _org_index(g)
    lines.append("## Organizations")
    lines.append("")
    if orgs:
        for o in orgs:
            slug = _slug_from_iri(o["o"])
            lines.append(f"- [{o['name']}](Organization-{slug})")
    else:
        lines.append("*(none yet)*")
    lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _render_institution_page(g: Graph, inst: dict[str, str]) -> str:
    """Render a per-institution page: same content as compiled.md, plus a
    backlinks section listing related people and orgs."""
    submissions = sparql_select(
        g,
        f"""
        SELECT ?s ?version ?date WHERE {{
            ?s a mgj:Submission ;
               mgj:documents <{inst['inst']}> ;
               mgj:submissionVersion ?version ;
               mgj:submissionDate ?date .
        }} ORDER BY DESC(?date) ?s
        """,
    )
    if not submissions:
        return f"# {inst['name']}\n\n*No submissions yet.*\n"

    # Use the latest submission as the canonical view for now.
    latest = submissions[0]["s"]
    sub_graph = _subgraph_for_submission(g, latest)
    body = compile_submission(sub_graph)

    if len(submissions) > 1:
        history = ["", "## Submission history", ""]
        for s in submissions:
            history.append(f"- v{s['version']} — {s['date']}")
        body += "\n".join(history) + "\n"

    return body


def _render_person_page(g: Graph, person: dict[str, str]) -> str:
    p = person["p"]
    lines = [f"# {person['name']}", ""]
    lines.append(f"<!-- compiler: {WIKI_COMPILER_ID} v{WIKI_COMPILER_VERSION} -->")
    lines.append("")
    lines.append(f"`{p}`")
    lines.append("")

    # Authorship
    authored = sparql_select(
        g,
        f"""
        SELECT ?inst ?instName WHERE {{
            ?s a mgj:Submission ; mgj:authoredBy <{p}> ;
               mgj:documents ?inst .
            ?inst mgj:institutionName ?instName .
        }} ORDER BY ?instName
        """,
    )
    if authored:
        lines.append("## Authored submissions")
        lines.append("")
        for r in authored:
            slug = _slug_from_iri(r["inst"])
            lines.append(f"- [{r['instName']}](Institution-{slug})")
        lines.append("")

    # Stakeholdings
    stakeholdings = sparql_select(
        g,
        f"""
        SELECT ?role ?inst ?instName WHERE {{
            ?stakeholder a mgj:Stakeholder ;
                         mgj:stakeholderAgent <{p}> ;
                         mgj:roleLabel ?role .
            ?s a mgj:Submission ; mgj:hasStakeholder ?stakeholder ;
               mgj:documents ?inst .
            ?inst mgj:institutionName ?instName .
        }} ORDER BY ?instName ?role
        """,
    )
    if stakeholdings:
        lines.append("## Stakeholder roles")
        lines.append("")
        for r in stakeholdings:
            slug = _slug_from_iri(r["inst"])
            lines.append(
                f"- **{r['role']}** in [{r['instName']}](Institution-{slug})"
            )
        lines.append("")

    # Origin participation
    origins = sparql_select(
        g,
        f"""
        SELECT ?label ?date ?inst ?instName WHERE {{
            ?ev a mgj:OriginEvent ;
                mgj:originParticipant <{p}> ;
                mgj:originLabel ?label .
            ?s a mgj:Submission ; mgj:hasOriginEvent ?ev ; mgj:documents ?inst .
            ?inst mgj:institutionName ?instName .
            OPTIONAL {{ ?ev mgj:originDate ?date }}
        }} ORDER BY ?date ?instName
        """,
    )
    if origins:
        lines.append("## Origin events")
        lines.append("")
        for r in origins:
            slug = _slug_from_iri(r["inst"])
            d = f" ({r['date']})" if r["date"] else ""
            lines.append(
                f"- **{r['label']}**{d} — [{r['instName']}](Institution-{slug})"
            )
        lines.append("")

    if not (authored or stakeholdings or origins):
        lines.append("*No recorded participation yet.*")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _render_org_page(g: Graph, org: dict[str, str]) -> str:
    o = org["o"]
    lines = [f"# {org['name']}", ""]
    lines.append(f"<!-- compiler: {WIKI_COMPILER_ID} v{WIKI_COMPILER_VERSION} -->")
    lines.append("")
    lines.append(f"`{o}`")
    lines.append("")

    # Hosts (legal context)
    hosts = sparql_select(
        g,
        f"""
        SELECT ?relationship ?inst ?instName WHERE {{
            ?lc a mgj:LegalContext ;
                mgj:hostOrganization <{o}> ;
                mgj:legalRelationship ?relationship .
            ?s a mgj:Submission ; mgj:operatesUnder ?lc ; mgj:documents ?inst .
            ?inst mgj:institutionName ?instName .
        }} ORDER BY ?instName
        """,
    )
    if hosts:
        lines.append("## Hosts")
        lines.append("")
        for r in hosts:
            slug = _slug_from_iri(r["inst"])
            rel = str(r["relationship"]).rsplit("#", 1)[-1]
            lines.append(
                f"- {_pretty_concept(rel)} of [{r['instName']}](Institution-{slug})"
            )
        lines.append("")

    # Stakeholdings
    stakeholdings = sparql_select(
        g,
        f"""
        SELECT ?role ?inst ?instName WHERE {{
            ?stakeholder a mgj:Stakeholder ;
                         mgj:stakeholderAgent <{o}> ;
                         mgj:roleLabel ?role .
            ?s a mgj:Submission ; mgj:hasStakeholder ?stakeholder ;
               mgj:documents ?inst .
            ?inst mgj:institutionName ?instName .
        }} ORDER BY ?instName ?role
        """,
    )
    if stakeholdings:
        lines.append("## Stakeholder roles")
        lines.append("")
        for r in stakeholdings:
            slug = _slug_from_iri(r["inst"])
            lines.append(
                f"- **{r['role']}** in [{r['instName']}](Institution-{slug})"
            )
        lines.append("")

    if not (hosts or stakeholdings):
        lines.append("*No recorded participation yet.*")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _slug_from_iri(iri: str) -> str:
    return str(iri).rstrip("/").rsplit("/", 1)[-1]


def _pretty_concept(name: str) -> str:
    out: list[str] = []
    for i, ch in enumerate(name):
        if i > 0 and ch.isupper() and not name[i - 1].isupper():
            out.append(" ")
        out.append(ch)
    return "".join(out)


def _subgraph_for_submission(g: Graph, sub_iri: str) -> Graph:
    """Build a fresh graph containing only the triples needed for this submission's
    catechism compilation: the submission, its institution, and all entities
    transitively reachable from the submission, plus the foaf agents
    referenced. This keeps the catechism compiler's _single_submission_iri
    invariant (exactly one mgj:Submission in the graph)."""
    from rdflib import URIRef

    sub_uri = URIRef(sub_iri)
    sg = Graph()
    visited: set[str] = set()
    frontier: list[str] = [sub_iri]

    while frontier:
        node = frontier.pop()
        if node in visited:
            continue
        visited.add(node)
        node_uri = URIRef(node)
        for p, o in g.predicate_objects(node_uri):
            sg.add((node_uri, p, o))
            if isinstance(o, URIRef) and str(o) not in visited:
                # Don't traverse into other Submission nodes; we want a
                # single-submission graph for the compiler.
                if (o, MGJ.documents, None) in g:
                    continue
                frontier.append(str(o))

    # Bring in the institution + its name (already covered if reached via documents)
    return sg


__all__ = [
    "WIKI_COMPILER_ID",
    "WIKI_COMPILER_VERSION",
    "load_full_graph",
    "compile_wiki",
]
