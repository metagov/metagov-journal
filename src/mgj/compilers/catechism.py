"""
mgj.compilers.catechism
-----------------------
Render a single submission graph into a published Markdown article.

Determinism invariant: for a fixed instance.ttl + compiler version, the
output bytes are identical across runs. The wiki compiler exposes the
same property over the full graph.

Strategy: SPARQL-driven extraction with explicit ORDER BY, then Python
post-sort by local-id integer where applicable so e.g. "stakeholder/2"
precedes "stakeholder/10". Markdown rendering is hand-coded rather than
templated to keep the output easy to inspect and diff.
"""

from __future__ import annotations

from pathlib import Path

from rdflib import Graph

from mgj.graph import load_instance, sparql_select
from mgj.namespaces import SPARQL_PREFIXES

COMPILER_VERSION = "0.1.0"
COMPILER_ID = "mgj.compilers.catechism"


# ---------------------------------------------------------------------------
# Top-level entry points
# ---------------------------------------------------------------------------


def compile_submission_file(instance_path: str | Path) -> str:
    """Load ``instance_path`` and return the compiled Markdown string."""
    g = load_instance(instance_path)
    return compile_submission(g)


def compile_submission(g: Graph) -> str:
    """Render the single mgj:Submission in ``g`` into a Markdown article."""
    sub = _single_submission_iri(g)
    inst_iri, inst_name = _institution_for(g, sub)
    version = _scalar(g, sub, "submissionVersion") or ""
    s_date = _scalar(g, sub, "submissionDate") or ""

    lines: list[str] = []
    lines.append(f"# {inst_name}")
    lines.append("")
    lines.append(f"*Submission v{version} — {s_date}*")
    lines.append("")
    lines.append(f"<!-- compiler: {COMPILER_ID} v{COMPILER_VERSION} -->")
    lines.append("")

    lines.extend(_render_q1(g, sub))
    lines.extend(_render_q2(g, sub))
    lines.extend(_render_q3(g, sub))
    lines.extend(_render_q4(g, sub))
    lines.extend(_render_q5(g, sub))
    lines.extend(_render_q6(g, sub))
    lines.extend(_render_q7(g, sub))
    lines.extend(_render_q8(g, sub))
    lines.extend(_render_legal_context(g, sub))
    lines.extend(_render_q9(g, sub))

    return "\n".join(lines).rstrip() + "\n"


# ---------------------------------------------------------------------------
# Question renderers
# ---------------------------------------------------------------------------


def _render_q1(g: Graph, sub: str) -> list[str]:
    out = ["## 1. Purpose", ""]
    nar = _scalar(g, sub, "q1Narrative")
    out.append(nar or "*(narrative not yet provided)*")
    out.append("")
    return out


def _render_q2(g: Graph, sub: str) -> list[str]:
    out = ["## 2. Stakeholders and roles", ""]
    nar = _scalar(g, sub, "q2Narrative")
    out.append(nar or "*(narrative not yet provided)*")
    out.append("")

    rows = _ordered_select(
        g,
        f"""
        SELECT ?s ?roleLabel ?agentName ?responsibilities
        WHERE {{
            <{sub}> mgj:hasStakeholder ?s .
            ?s mgj:roleLabel ?roleLabel .
            OPTIONAL {{ ?s mgj:stakeholderAgent ?agent . ?agent foaf:name ?agentName }}
            OPTIONAL {{ ?s mgj:stakeholderResponsibilities ?responsibilities }}
        }}
        """,
        sort_key=lambda r: _local_id_int(r["s"]),
    )
    if rows:
        out.append("### Stakeholders")
        out.append("")
        for r in rows:
            line = f"- **{r['roleLabel']}**"
            if r["agentName"]:
                line += f": {r['agentName']}"
            if r["responsibilities"]:
                line += f" — {r['responsibilities']}"
            out.append(line)
        out.append("")
    return out


def _render_q3(g: Graph, sub: str) -> list[str]:
    out = ["## 3. Environmental factors", ""]
    nar = _scalar(g, sub, "q3Narrative")
    out.append(nar or "*(narrative not yet provided)*")
    out.append("")

    rows = _ordered_select(
        g,
        f"""
        SELECT ?s ?modality ?description
        WHERE {{
            <{sub}> mgj:hasEnvironmentalFactor ?s .
            ?s mgj:lessigModality ?modality ;
               mgj:factorDescription ?description .
        }}
        """,
        sort_key=lambda r: (_short_concept(r["modality"]), _local_id_int(r["s"])),
    )
    if rows:
        # Group by modality, preserving the canonical Law/Norms/Markets/Architecture order.
        groups: dict[str, list[dict]] = {}
        for r in rows:
            groups.setdefault(_short_concept(r["modality"]), []).append(r)
        for modality in ["Law", "Norms", "Markets", "Architecture"]:
            if modality not in groups:
                continue
            out.append(f"### {modality}")
            out.append("")
            for r in groups[modality]:
                out.append(f"- {r['description']}")
            out.append("")
    return out


def _render_q4(g: Graph, sub: str) -> list[str]:
    out = ["## 4. Constitution", ""]
    nar = _scalar(g, sub, "q4Narrative")
    out.append(nar or "*(narrative not yet provided)*")
    out.append("")

    rows = _ordered_select(
        g,
        f"""
        SELECT ?s ?label ?description ?type ?sourceURL
        WHERE {{
            <{sub}> mgj:hasConstitutionalElement ?s .
            ?s mgj:elementLabel ?label ;
               mgj:elementDescription ?description ;
               mgj:elementType ?type .
            OPTIONAL {{ ?s mgj:elementSourceURL ?sourceURL }}
        }}
        """,
        sort_key=lambda r: (_short_concept(r["type"]), _local_id_int(r["s"])),
    )
    if rows:
        groups: dict[str, list[dict]] = {}
        for r in rows:
            groups.setdefault(_short_concept(r["type"]), []).append(r)
        for kind in [
            "Bylaw",
            "Norm",
            "DecisionProcedure",
            "DisputeResolution",
            "AmendmentProcess",
        ]:
            if kind not in groups:
                continue
            out.append(f"### {_pretty_concept(kind)}")
            out.append("")
            for r in groups[kind]:
                line = f"- **{r['label']}**: {r['description']}"
                if r["sourceURL"]:
                    line += f" *([source]({r['sourceURL']}))*"
                out.append(line)
            out.append("")
    return out


def _render_q5(g: Graph, sub: str) -> list[str]:
    out = ["## 5. Field sites", ""]
    nar = _scalar(g, sub, "q5Narrative")
    out.append(nar or "*(narrative not yet provided)*")
    out.append("")
    rows = _ordered_select(
        g,
        f"""
        SELECT ?s ?label ?url ?description
        WHERE {{
            <{sub}> mgj:hasFieldSite ?s .
            ?s mgj:fieldSiteLabel ?label .
            OPTIONAL {{ ?s mgj:fieldSiteURL ?url }}
            OPTIONAL {{ ?s mgj:fieldSiteDescription ?description }}
        }}
        """,
        sort_key=lambda r: _local_id_int(r["s"]),
    )
    for r in rows:
        title = f"[{r['label']}]({r['url']})" if r["url"] else f"**{r['label']}**"
        line = f"- {title}"
        if r["description"]:
            line += f" — {r['description']}"
        out.append(line)
    out.append("")
    return out


def _render_q6(g: Graph, sub: str) -> list[str]:
    out = ["## 6. Author relationship", ""]
    nar = _scalar(g, sub, "q6Narrative")
    out.append(nar or "*(narrative not yet provided)*")
    out.append("")
    rows = _ordered_select(
        g,
        f"""
        SELECT ?name
        WHERE {{
            <{sub}> mgj:authoredBy ?p . ?p foaf:name ?name .
        }}
        """,
        sort_key=lambda r: r["name"],
    )
    role = _scalar(g, sub, "authorRole")
    disclosure = _scalar(g, sub, "authorDisclosure")
    if rows:
        author_line = f"*Authored by **{rows[0]['name']}**"
        if role:
            author_line += f" — {role}"
        author_line += ".*"
        out.append(author_line)
        out.append("")
    if disclosure:
        out.append(f"*Disclosure:* {disclosure}")
        out.append("")
    return out


def _render_q7(g: Graph, sub: str) -> list[str]:
    out = ["## 7. Origins", ""]
    nar = _scalar(g, sub, "q7Narrative")
    out.append(nar or "*(narrative not yet provided)*")
    out.append("")
    events = _ordered_select(
        g,
        f"""
        SELECT ?s ?label ?description ?date
        WHERE {{
            <{sub}> mgj:hasOriginEvent ?s .
            ?s mgj:originLabel ?label ;
               mgj:originDescription ?description .
            OPTIONAL {{ ?s mgj:originDate ?date }}
        }}
        """,
        sort_key=lambda r: (r["date"] or "", _local_id_int(r["s"])),
    )
    for ev in events:
        # Resolve participants in a deterministic order
        parts = sparql_select(
            g,
            f"""
            SELECT ?name WHERE {{
                <{ev['s']}> mgj:originParticipant ?p . ?p foaf:name ?name .
            }} ORDER BY ?name
            """,
        )
        names = ", ".join(p["name"] for p in parts)
        date = f" ({ev['date']})" if ev["date"] else ""
        line = f"- **{ev['label']}**{date}: {ev['description']}"
        if names:
            line += f" — *participants: {names}*"
        out.append(line)
    out.append("")
    return out


def _render_q8(g: Graph, sub: str) -> list[str]:
    out = ["## 8. Evolution", ""]
    nar = _scalar(g, sub, "q8Narrative")
    out.append(nar or "*(narrative not yet provided)*")
    out.append("")
    rows = _ordered_select(
        g,
        f"""
        SELECT ?s ?label ?description
        WHERE {{
            <{sub}> mgj:hasEvolutionMechanism ?s .
            ?s mgj:mechanismLabel ?label ;
               mgj:mechanismDescription ?description .
        }}
        """,
        sort_key=lambda r: _local_id_int(r["s"]),
    )
    for r in rows:
        out.append(f"- **{r['label']}**: {r['description']}")
    out.append("")
    return out


def _render_q9(g: Graph, sub: str) -> list[str]:
    out = ["## 9. References", ""]
    nar = _scalar(g, sub, "q9Narrative")
    if nar:
        out.append(nar)
        out.append("")
    rows = _ordered_select(
        g,
        f"""
        SELECT ?s ?title ?identifier ?date
        WHERE {{
            <{sub}> mgj:hasReference ?s .
            ?s dcterms:title ?title ;
               dcterms:identifier ?identifier .
            OPTIONAL {{ ?s dcterms:date ?date }}
        }}
        """,
        sort_key=lambda r: _local_id_int(r["s"]),
    )
    for i, r in enumerate(rows, 1):
        creators = sparql_select(
            g,
            f"""
            SELECT ?c WHERE {{ <{r['s']}> dcterms:creator ?c }} ORDER BY ?c
            """,
        )
        names = ", ".join(c["c"] for c in creators)
        date = f" ({r['date']})" if r["date"] else ""
        prefix = f"{names}{date}" if names else (r["date"] or "")
        title_link = f"[{r['title']}]({r['identifier']})"
        if prefix:
            out.append(f"{i}. {prefix}. {title_link}")
        else:
            out.append(f"{i}. {title_link}")
    out.append("")
    return out


def _render_legal_context(g: Graph, sub: str) -> list[str]:
    rows = sparql_select(
        g,
        f"""
        SELECT ?lc ?relationship ?description ?fundingRef ?hostName WHERE {{
            <{sub}> mgj:operatesUnder ?lc .
            ?lc mgj:legalRelationship ?relationship ;
                mgj:legalContextDescription ?description ;
                mgj:hostOrganization ?host .
            ?host foaf:name ?hostName .
            OPTIONAL {{ ?lc mgj:fundingReference ?fundingRef }}
        }}
        """,
    )
    if not rows:
        return []
    r = rows[0]
    out = ["## Legal context", ""]
    relationship = _short_concept(r["relationship"])
    relationship_pretty = _pretty_concept(relationship)
    out.append(
        f"*Operates under **{r['hostName']}** as {relationship_pretty.lower()}.*"
    )
    out.append("")
    out.append(r["description"])
    if r["fundingRef"]:
        out.append("")
        out.append(f"*Funding reference:* `{r['fundingRef']}`")
    out.append("")
    return out


# ---------------------------------------------------------------------------
# SPARQL + sorting helpers
# ---------------------------------------------------------------------------


def _ordered_select(g: Graph, query: str, *, sort_key) -> list[dict[str, str]]:
    rows = sparql_select(g, query)
    return sorted(rows, key=sort_key)


def _scalar(g: Graph, subject: str, prop: str) -> str | None:
    rows = sparql_select(
        g, f"SELECT ?v WHERE {{ <{subject}> mgj:{prop} ?v }} LIMIT 1"
    )
    return rows[0]["v"] if rows else None


def _single_submission_iri(g: Graph) -> str:
    rows = sparql_select(g, "SELECT ?s WHERE { ?s a mgj:Submission } ORDER BY ?s")
    if len(rows) != 1:
        raise ValueError(
            f"expected exactly one mgj:Submission in graph; found {len(rows)}"
        )
    return rows[0]["s"]


def _institution_for(g: Graph, sub: str) -> tuple[str, str]:
    rows = sparql_select(
        g,
        f"""
        SELECT ?inst ?name WHERE {{
            <{sub}> mgj:documents ?inst . ?inst mgj:institutionName ?name .
        }}
        """,
    )
    if not rows:
        raise ValueError(f"submission {sub} has no institution name")
    return rows[0]["inst"], rows[0]["name"]


def _local_id_int(iri: str) -> int:
    """Return the trailing integer of an IRI for stable numeric sort.
    Falls back to a large number to keep non-numeric IDs at the end."""
    tail = iri.rstrip("/").rsplit("/", 1)[-1]
    if tail.isdigit():
        return int(tail)
    return 1_000_000_000


def _short_concept(iri: str) -> str:
    s = str(iri)
    return s.rsplit("#", 1)[-1].rsplit("/", 1)[-1]


def _pretty_concept(name: str) -> str:
    """Insert spaces before internal capitals: 'DecisionProcedure' -> 'Decision Procedure'."""
    out: list[str] = []
    for i, ch in enumerate(name):
        if i > 0 and ch.isupper() and not name[i - 1].isupper():
            out.append(" ")
        out.append(ch)
    return "".join(out)


__all__ = [
    "COMPILER_ID",
    "COMPILER_VERSION",
    "compile_submission",
    "compile_submission_file",
]
