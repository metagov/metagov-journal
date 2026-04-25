"""
mgj.commands.entities
---------------------
Per-entity CLI command groups for catechism Q2..Q9 and the cross-Q
LegalContext. Every mutation goes through ``with_mutation`` so the
canonicalize+validate+save invariant holds.

One sub-typer per entity type:
    stakeholder  Q2
    factor       Q3 (environmental factor)
    constitution Q4 (constitutional element)
    fieldsite    Q5
    origin       Q7 (origin event)
    evolution    Q8 (evolution mechanism)
    reference    Q9
    legal        cross-Q (legal context)
"""

from __future__ import annotations

from datetime import date as DateT

import typer
from rdflib import Graph, Literal, URIRef
from rdflib.namespace import DCTERMS, FOAF, RDF, SKOS, XSD
from rich.table import Table

from mgj.commands._common import (
    console,
    err_console,
    get_submission_iri,
    get_submission_version,
    load_submission_graph,
    next_local_id,
    with_mutation,
)
from mgj.namespaces import (
    MGJ,
    organization_iri,
    person_iri,
    role_iri,
    submission_entity_iri,
)

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _resolve_agent(g: Graph, person: str | None, org: str | None) -> URIRef:
    if (person is None) == (org is None):
        raise typer.BadParameter("provide exactly one of --person or --org")
    if person:
        iri = URIRef(person_iri(person))
        if (iri, RDF.type, FOAF.Person) not in g:
            raise typer.BadParameter(
                f"person '{person}' not in shared/people.ttl — run `mgj people add` first"
            )
        return iri
    iri = URIRef(organization_iri(org))
    if (iri, RDF.type, FOAF.Organization) not in g:
        raise typer.BadParameter(
            f"org '{org}' not in shared/organizations.ttl — run `mgj orgs add` first"
        )
    return iri


def _ensure_role_concept(g: Graph, role_slug: str, role_label: str) -> URIRef:
    iri = URIRef(role_iri(role_slug))
    if (iri, RDF.type, SKOS.Concept) not in g:
        g.add((iri, RDF.type, SKOS.Concept))
        g.add((iri, SKOS.inScheme, MGJ.RoleType))
        g.add((iri, SKOS.prefLabel, Literal(role_label)))
    return iri


def _entity_iri(slug: str, version: str, kind: str, local_id: str) -> URIRef:
    return URIRef(submission_entity_iri(slug, version, kind, local_id))


def _local_id_from_iri(iri: str) -> str:
    return iri.rstrip("/").rsplit("/", 1)[-1]


def _remove_subject(g: Graph, subj: URIRef) -> None:
    """Remove all triples where ``subj`` is subject. Object-position triples
    are left in place (the link from Submission to subj is removed by the
    caller via the link predicate)."""
    for p, o in list(g.predicate_objects(subj)):
        g.remove((subj, p, o))


# ---------------------------------------------------------------------------
# Q2 — stakeholder
# ---------------------------------------------------------------------------

stakeholder_app = typer.Typer(no_args_is_help=True, help="Q2 — stakeholders.")


@stakeholder_app.command("add")
def stakeholder_add(
    slug: str = typer.Argument(...),
    role_label: str = typer.Option(..., "--role-label", help="e.g. 'Editor', 'Reviewer'"),
    role_slug: str = typer.Option(
        ..., "--role-slug", help="URL-safe role slug, e.g. 'editor'"
    ),
    person: str = typer.Option(None, "--person", help="Slug from shared/people.ttl"),
    org: str = typer.Option(None, "--org", help="Slug from shared/organizations.ttl"),
    responsibilities: str = typer.Option(None, "--responsibilities"),
) -> None:
    with with_mutation(slug, question=2) as g:
        sub = get_submission_iri(g, slug)
        version = get_submission_version(g, slug)
        agent = _resolve_agent(g, person, org)
        role = _ensure_role_concept(g, role_slug, role_label)
        lid = next_local_id(g, slug, version, "stakeholder", "Stakeholder")
        node = _entity_iri(slug, version, "stakeholder", lid)
        g.add((node, RDF.type, MGJ.Stakeholder))
        g.add((node, MGJ.stakeholderAgent, agent))
        g.add((node, MGJ.roleLabel, Literal(role_label)))
        g.add((node, MGJ.hasRole, role))
        if responsibilities:
            g.add((node, MGJ.stakeholderResponsibilities, Literal(responsibilities)))
        g.add((sub, MGJ.hasStakeholder, node))
    console.print(f"[green]✓ added stakeholder {lid}[/green]")


@stakeholder_app.command("list")
def stakeholder_list(slug: str = typer.Argument(...)) -> None:
    g = load_submission_graph(slug)
    table = Table("id", "agent", "role", "responsibilities")
    for s in sorted(g.subjects(RDF.type, MGJ.Stakeholder)):
        agent = next(g.objects(s, MGJ.stakeholderAgent), URIRef(""))
        role = next(g.objects(s, MGJ.roleLabel), Literal(""))
        resp = next(g.objects(s, MGJ.stakeholderResponsibilities), Literal(""))
        table.add_row(_local_id_from_iri(str(s)), str(agent), str(role), str(resp))
    console.print(table)


@stakeholder_app.command("remove")
def stakeholder_remove(
    slug: str = typer.Argument(...),
    local_id: str = typer.Argument(..., help="Numeric id from `stakeholder list`"),
) -> None:
    with with_mutation(slug, question=2) as g:
        version = get_submission_version(g, slug)
        node = _entity_iri(slug, version, "stakeholder", local_id)
        if (node, RDF.type, MGJ.Stakeholder) not in g:
            raise typer.BadParameter(f"stakeholder {local_id} not found")
        sub = get_submission_iri(g, slug)
        g.remove((sub, MGJ.hasStakeholder, node))
        _remove_subject(g, node)
    console.print(f"[yellow]– removed stakeholder {local_id}[/yellow]")


# ---------------------------------------------------------------------------
# Q3 — environmental factor
# ---------------------------------------------------------------------------

factor_app = typer.Typer(no_args_is_help=True, help="Q3 — environmental factors.")


@factor_app.command("add")
def factor_add(
    slug: str = typer.Argument(...),
    modality: str = typer.Option(
        ..., "--modality", help="Law | Norms | Markets | Architecture"
    ),
    description: str = typer.Option(..., "--description", "-d"),
) -> None:
    if modality not in {"Law", "Norms", "Markets", "Architecture"}:
        raise typer.BadParameter(
            "modality must be one of: Law, Norms, Markets, Architecture"
        )
    with with_mutation(slug, question=3) as g:
        sub = get_submission_iri(g, slug)
        version = get_submission_version(g, slug)
        lid = next_local_id(g, slug, version, "factor", "EnvironmentalFactor")
        node = _entity_iri(slug, version, "factor", lid)
        g.add((node, RDF.type, MGJ.EnvironmentalFactor))
        g.add((node, MGJ.lessigModality, MGJ[modality]))
        g.add((node, MGJ.factorDescription, Literal(description)))
        g.add((sub, MGJ.hasEnvironmentalFactor, node))
    console.print(f"[green]✓ added factor {lid}[/green]")


@factor_app.command("list")
def factor_list(slug: str = typer.Argument(...)) -> None:
    g = load_submission_graph(slug)
    table = Table("id", "modality", "description")
    for s in sorted(g.subjects(RDF.type, MGJ.EnvironmentalFactor)):
        mod = next(g.objects(s, MGJ.lessigModality), URIRef(""))
        desc = next(g.objects(s, MGJ.factorDescription), Literal(""))
        table.add_row(
            _local_id_from_iri(str(s)),
            str(mod).rsplit("#", 1)[-1],
            str(desc),
        )
    console.print(table)


@factor_app.command("remove")
def factor_remove(
    slug: str = typer.Argument(...), local_id: str = typer.Argument(...)
) -> None:
    with with_mutation(slug, question=3) as g:
        version = get_submission_version(g, slug)
        node = _entity_iri(slug, version, "factor", local_id)
        if (node, RDF.type, MGJ.EnvironmentalFactor) not in g:
            raise typer.BadParameter(f"factor {local_id} not found")
        g.remove((get_submission_iri(g, slug), MGJ.hasEnvironmentalFactor, node))
        _remove_subject(g, node)
    console.print(f"[yellow]– removed factor {local_id}[/yellow]")


# ---------------------------------------------------------------------------
# Q4 — constitutional element
# ---------------------------------------------------------------------------

constitution_app = typer.Typer(
    no_args_is_help=True, help="Q4 — constitutional elements."
)

_ELEMENT_TYPES = {"Bylaw", "Norm", "DecisionProcedure", "DisputeResolution", "AmendmentProcess"}


@constitution_app.command("add")
def constitution_add(
    slug: str = typer.Argument(...),
    label: str = typer.Option(..., "--label", "-l"),
    description: str = typer.Option(..., "--description", "-d"),
    element_type: str = typer.Option(
        ..., "--type", help="Bylaw | Norm | DecisionProcedure | DisputeResolution | AmendmentProcess"
    ),
    source_url: str = typer.Option(None, "--source-url"),
) -> None:
    if element_type not in _ELEMENT_TYPES:
        raise typer.BadParameter(f"--type must be one of {sorted(_ELEMENT_TYPES)}")
    with with_mutation(slug, question=4) as g:
        sub = get_submission_iri(g, slug)
        version = get_submission_version(g, slug)
        lid = next_local_id(g, slug, version, "constitution", "ConstitutionalElement")
        node = _entity_iri(slug, version, "constitution", lid)
        g.add((node, RDF.type, MGJ.ConstitutionalElement))
        g.add((node, MGJ.elementLabel, Literal(label)))
        g.add((node, MGJ.elementDescription, Literal(description)))
        g.add((node, MGJ.elementType, MGJ[element_type]))
        if source_url:
            g.add((node, MGJ.elementSourceURL, Literal(source_url, datatype=XSD.anyURI)))
        g.add((sub, MGJ.hasConstitutionalElement, node))
    console.print(f"[green]✓ added constitutional element {lid}[/green]")


@constitution_app.command("list")
def constitution_list(slug: str = typer.Argument(...)) -> None:
    g = load_submission_graph(slug)
    table = Table("id", "type", "label", "description")
    for s in sorted(g.subjects(RDF.type, MGJ.ConstitutionalElement)):
        et = next(g.objects(s, MGJ.elementType), URIRef(""))
        lab = next(g.objects(s, MGJ.elementLabel), Literal(""))
        desc = next(g.objects(s, MGJ.elementDescription), Literal(""))
        table.add_row(
            _local_id_from_iri(str(s)),
            str(et).rsplit("#", 1)[-1],
            str(lab),
            str(desc),
        )
    console.print(table)


@constitution_app.command("remove")
def constitution_remove(
    slug: str = typer.Argument(...), local_id: str = typer.Argument(...)
) -> None:
    with with_mutation(slug, question=4) as g:
        version = get_submission_version(g, slug)
        node = _entity_iri(slug, version, "constitution", local_id)
        if (node, RDF.type, MGJ.ConstitutionalElement) not in g:
            raise typer.BadParameter(f"constitution {local_id} not found")
        g.remove((get_submission_iri(g, slug), MGJ.hasConstitutionalElement, node))
        _remove_subject(g, node)
    console.print(f"[yellow]– removed constitution {local_id}[/yellow]")


# ---------------------------------------------------------------------------
# Q5 — field site
# ---------------------------------------------------------------------------

fieldsite_app = typer.Typer(no_args_is_help=True, help="Q5 — field sites.")


@fieldsite_app.command("add")
def fieldsite_add(
    slug: str = typer.Argument(...),
    label: str = typer.Option(..., "--label", "-l"),
    url: str = typer.Option(None, "--url"),
    description: str = typer.Option(None, "--description", "-d"),
) -> None:
    if url is None and not description:
        raise typer.BadParameter("provide at least one of --url or --description")
    with with_mutation(slug, question=5) as g:
        sub = get_submission_iri(g, slug)
        version = get_submission_version(g, slug)
        lid = next_local_id(g, slug, version, "fieldsite", "FieldSite")
        node = _entity_iri(slug, version, "fieldsite", lid)
        g.add((node, RDF.type, MGJ.FieldSite))
        g.add((node, MGJ.fieldSiteLabel, Literal(label)))
        if url:
            g.add((node, MGJ.fieldSiteURL, Literal(url, datatype=XSD.anyURI)))
        if description:
            g.add((node, MGJ.fieldSiteDescription, Literal(description)))
        g.add((sub, MGJ.hasFieldSite, node))
    console.print(f"[green]✓ added field site {lid}[/green]")


@fieldsite_app.command("list")
def fieldsite_list(slug: str = typer.Argument(...)) -> None:
    g = load_submission_graph(slug)
    table = Table("id", "label", "url", "description")
    for s in sorted(g.subjects(RDF.type, MGJ.FieldSite)):
        lab = next(g.objects(s, MGJ.fieldSiteLabel), Literal(""))
        url = next(g.objects(s, MGJ.fieldSiteURL), Literal(""))
        desc = next(g.objects(s, MGJ.fieldSiteDescription), Literal(""))
        table.add_row(_local_id_from_iri(str(s)), str(lab), str(url), str(desc))
    console.print(table)


@fieldsite_app.command("remove")
def fieldsite_remove(
    slug: str = typer.Argument(...), local_id: str = typer.Argument(...)
) -> None:
    with with_mutation(slug, question=5) as g:
        version = get_submission_version(g, slug)
        node = _entity_iri(slug, version, "fieldsite", local_id)
        if (node, RDF.type, MGJ.FieldSite) not in g:
            raise typer.BadParameter(f"fieldsite {local_id} not found")
        g.remove((get_submission_iri(g, slug), MGJ.hasFieldSite, node))
        _remove_subject(g, node)
    console.print(f"[yellow]– removed fieldsite {local_id}[/yellow]")


# ---------------------------------------------------------------------------
# Q7 — origin event
# ---------------------------------------------------------------------------

origin_app = typer.Typer(no_args_is_help=True, help="Q7 — origin events.")


@origin_app.command("add")
def origin_add(
    slug: str = typer.Argument(...),
    label: str = typer.Option(..., "--label", "-l"),
    description: str = typer.Option(..., "--description", "-d"),
    date_: str = typer.Option(None, "--date", help="ISO date"),
    persons: str = typer.Option(
        None, "--persons", help="Comma-separated person slugs"
    ),
    orgs: str = typer.Option(
        None, "--orgs", help="Comma-separated organization slugs"
    ),
) -> None:
    person_iris: list[URIRef] = []
    org_iris: list[URIRef] = []
    if persons:
        person_iris = [URIRef(person_iri(s.strip())) for s in persons.split(",") if s.strip()]
    if orgs:
        org_iris = [URIRef(organization_iri(s.strip())) for s in orgs.split(",") if s.strip()]
    if not person_iris and not org_iris:
        raise typer.BadParameter("provide at least one of --persons or --orgs")

    with with_mutation(slug, question=7) as g:
        # Validate references resolve in shared/
        for p in person_iris:
            if (p, RDF.type, FOAF.Person) not in g:
                raise typer.BadParameter(f"person not in shared/people.ttl: {p}")
        for o in org_iris:
            if (o, RDF.type, FOAF.Organization) not in g:
                raise typer.BadParameter(f"org not in shared/organizations.ttl: {o}")
        sub = get_submission_iri(g, slug)
        version = get_submission_version(g, slug)
        lid = next_local_id(g, slug, version, "origin", "OriginEvent")
        node = _entity_iri(slug, version, "origin", lid)
        g.add((node, RDF.type, MGJ.OriginEvent))
        g.add((node, MGJ.originLabel, Literal(label)))
        g.add((node, MGJ.originDescription, Literal(description)))
        if date_:
            DateT.fromisoformat(date_)  # validate
            g.add((node, MGJ.originDate, Literal(date_, datatype=XSD.date)))
        for p in person_iris:
            g.add((node, MGJ.originParticipant, p))
        for o in org_iris:
            g.add((node, MGJ.originParticipant, o))
        g.add((sub, MGJ.hasOriginEvent, node))
    console.print(f"[green]✓ added origin event {lid}[/green]")


@origin_app.command("list")
def origin_list(slug: str = typer.Argument(...)) -> None:
    g = load_submission_graph(slug)
    table = Table("id", "label", "date", "participants")
    for s in sorted(g.subjects(RDF.type, MGJ.OriginEvent)):
        lab = next(g.objects(s, MGJ.originLabel), Literal(""))
        d = next(g.objects(s, MGJ.originDate), Literal(""))
        parts = ", ".join(
            str(p).rsplit("/", 1)[-1] for p in g.objects(s, MGJ.originParticipant)
        )
        table.add_row(_local_id_from_iri(str(s)), str(lab), str(d), parts)
    console.print(table)


@origin_app.command("remove")
def origin_remove(
    slug: str = typer.Argument(...), local_id: str = typer.Argument(...)
) -> None:
    with with_mutation(slug, question=7) as g:
        version = get_submission_version(g, slug)
        node = _entity_iri(slug, version, "origin", local_id)
        if (node, RDF.type, MGJ.OriginEvent) not in g:
            raise typer.BadParameter(f"origin {local_id} not found")
        g.remove((get_submission_iri(g, slug), MGJ.hasOriginEvent, node))
        _remove_subject(g, node)
    console.print(f"[yellow]– removed origin {local_id}[/yellow]")


# ---------------------------------------------------------------------------
# Q8 — evolution mechanism
# ---------------------------------------------------------------------------

evolution_app = typer.Typer(no_args_is_help=True, help="Q8 — evolution mechanisms.")


@evolution_app.command("add")
def evolution_add(
    slug: str = typer.Argument(...),
    label: str = typer.Option(..., "--label", "-l"),
    description: str = typer.Option(..., "--description", "-d"),
) -> None:
    with with_mutation(slug, question=8) as g:
        sub = get_submission_iri(g, slug)
        version = get_submission_version(g, slug)
        lid = next_local_id(g, slug, version, "evolution", "EvolutionMechanism")
        node = _entity_iri(slug, version, "evolution", lid)
        g.add((node, RDF.type, MGJ.EvolutionMechanism))
        g.add((node, MGJ.mechanismLabel, Literal(label)))
        g.add((node, MGJ.mechanismDescription, Literal(description)))
        g.add((sub, MGJ.hasEvolutionMechanism, node))
    console.print(f"[green]✓ added evolution mechanism {lid}[/green]")


@evolution_app.command("list")
def evolution_list(slug: str = typer.Argument(...)) -> None:
    g = load_submission_graph(slug)
    table = Table("id", "label", "description")
    for s in sorted(g.subjects(RDF.type, MGJ.EvolutionMechanism)):
        lab = next(g.objects(s, MGJ.mechanismLabel), Literal(""))
        desc = next(g.objects(s, MGJ.mechanismDescription), Literal(""))
        table.add_row(_local_id_from_iri(str(s)), str(lab), str(desc))
    console.print(table)


@evolution_app.command("remove")
def evolution_remove(
    slug: str = typer.Argument(...), local_id: str = typer.Argument(...)
) -> None:
    with with_mutation(slug, question=8) as g:
        version = get_submission_version(g, slug)
        node = _entity_iri(slug, version, "evolution", local_id)
        if (node, RDF.type, MGJ.EvolutionMechanism) not in g:
            raise typer.BadParameter(f"evolution {local_id} not found")
        g.remove((get_submission_iri(g, slug), MGJ.hasEvolutionMechanism, node))
        _remove_subject(g, node)
    console.print(f"[yellow]– removed evolution {local_id}[/yellow]")


# ---------------------------------------------------------------------------
# Q9 — reference
# ---------------------------------------------------------------------------

reference_app = typer.Typer(no_args_is_help=True, help="Q9 — references.")


@reference_app.command("add")
def reference_add(
    slug: str = typer.Argument(...),
    title: str = typer.Option(..., "--title", "-t"),
    identifier: str = typer.Option(
        ..., "--identifier", "-i", help="DOI or canonical URL"
    ),
    creators: str = typer.Option(
        None, "--creators", help="Comma-separated author names"
    ),
    date_: str = typer.Option(None, "--date"),
) -> None:
    with with_mutation(slug, question=9) as g:
        sub = get_submission_iri(g, slug)
        version = get_submission_version(g, slug)
        lid = next_local_id(g, slug, version, "reference", "Reference")
        node = _entity_iri(slug, version, "reference", lid)
        g.add((node, RDF.type, MGJ.Reference))
        g.add((node, DCTERMS.title, Literal(title)))
        g.add((node, DCTERMS.identifier, Literal(identifier)))
        if creators:
            for c in [c.strip() for c in creators.split(",") if c.strip()]:
                g.add((node, DCTERMS.creator, Literal(c)))
        if date_:
            g.add((node, DCTERMS.date, Literal(date_)))
        g.add((sub, MGJ.hasReference, node))
    console.print(f"[green]✓ added reference {lid}[/green]")


@reference_app.command("list")
def reference_list(slug: str = typer.Argument(...)) -> None:
    g = load_submission_graph(slug)
    table = Table("id", "title", "identifier", "date", "creators")
    for s in sorted(g.subjects(RDF.type, MGJ.Reference)):
        t = next(g.objects(s, DCTERMS.title), Literal(""))
        i = next(g.objects(s, DCTERMS.identifier), Literal(""))
        d = next(g.objects(s, DCTERMS.date), Literal(""))
        cs = ", ".join(str(c) for c in g.objects(s, DCTERMS.creator))
        table.add_row(_local_id_from_iri(str(s)), str(t), str(i), str(d), cs)
    console.print(table)


@reference_app.command("remove")
def reference_remove(
    slug: str = typer.Argument(...), local_id: str = typer.Argument(...)
) -> None:
    with with_mutation(slug, question=9) as g:
        version = get_submission_version(g, slug)
        node = _entity_iri(slug, version, "reference", local_id)
        if (node, RDF.type, MGJ.Reference) not in g:
            raise typer.BadParameter(f"reference {local_id} not found")
        g.remove((get_submission_iri(g, slug), MGJ.hasReference, node))
        _remove_subject(g, node)
    console.print(f"[yellow]– removed reference {local_id}[/yellow]")


# ---------------------------------------------------------------------------
# LegalContext (cross-Q) — singleton per submission
# ---------------------------------------------------------------------------

legal_app = typer.Typer(no_args_is_help=True, help="Legal context (cross-Q).")

_LEGAL_RELATIONSHIPS = {
    "FiscalSponsor",
    "LegalIncorporation",
    "ParentOrganization",
    "Incubator",
    "Network",
}


@legal_app.command("set")
def legal_set(
    slug: str = typer.Argument(...),
    host: str = typer.Option(..., "--host", help="Org slug from shared/organizations.ttl"),
    relationship: str = typer.Option(
        ..., "--relationship", help=" | ".join(sorted(_LEGAL_RELATIONSHIPS))
    ),
    description: str = typer.Option(..., "--description", "-d"),
    funding_reference: str = typer.Option(None, "--funding-ref"),
) -> None:
    """Set or replace the LegalContext. Singleton per submission."""
    if relationship not in _LEGAL_RELATIONSHIPS:
        raise typer.BadParameter(
            f"--relationship must be one of {sorted(_LEGAL_RELATIONSHIPS)}"
        )
    # Skip per-question validation (LegalContext spans Q3/Q4/Q7);
    # system validation will run later.
    with with_mutation(slug, question=None) as g:
        sub = get_submission_iri(g, slug)
        version = get_submission_version(g, slug)
        host_iri = URIRef(organization_iri(host))
        if (host_iri, RDF.type, FOAF.Organization) not in g:
            raise typer.BadParameter(
                f"org '{host}' not in shared/organizations.ttl"
            )

        # Remove any existing LegalContext for this submission.
        for old in list(g.objects(sub, MGJ.operatesUnder)):
            g.remove((sub, MGJ.operatesUnder, old))
            _remove_subject(g, old)

        node = _entity_iri(slug, version, "legal", "1")
        g.add((node, RDF.type, MGJ.LegalContext))
        g.add((node, MGJ.hostOrganization, host_iri))
        g.add((node, MGJ.legalRelationship, MGJ[relationship]))
        g.add((node, MGJ.legalContextDescription, Literal(description)))
        if funding_reference:
            g.add((node, MGJ.fundingReference, Literal(funding_reference)))
        g.add((sub, MGJ.operatesUnder, node))
    console.print("[green]✓ legal context set[/green]")


@legal_app.command("show")
def legal_show(slug: str = typer.Argument(...)) -> None:
    g = load_submission_graph(slug)
    sub = get_submission_iri(g, slug)
    lc = next(g.objects(sub, MGJ.operatesUnder), None)
    if lc is None:
        console.print("[dim]no legal context set[/dim]")
        return
    host = next(g.objects(lc, MGJ.hostOrganization), URIRef(""))
    rel = next(g.objects(lc, MGJ.legalRelationship), URIRef(""))
    desc = next(g.objects(lc, MGJ.legalContextDescription), Literal(""))
    funding = next(g.objects(lc, MGJ.fundingReference), Literal(""))
    table = Table("field", "value")
    table.add_row("host", str(host).rsplit("/", 1)[-1])
    table.add_row("relationship", str(rel).rsplit("#", 1)[-1])
    table.add_row("description", str(desc))
    if funding:
        table.add_row("funding ref", str(funding))
    console.print(table)


@legal_app.command("clear")
def legal_clear(slug: str = typer.Argument(...)) -> None:
    with with_mutation(slug, question=None) as g:
        sub = get_submission_iri(g, slug)
        for old in list(g.objects(sub, MGJ.operatesUnder)):
            g.remove((sub, MGJ.operatesUnder, old))
            _remove_subject(g, old)
    console.print("[yellow]– legal context cleared[/yellow]")


# ---------------------------------------------------------------------------
# Q6 — author disclosure (singleton, lives on Submission)
# ---------------------------------------------------------------------------

author_app = typer.Typer(no_args_is_help=True, help="Q6 — author disclosure.")


@author_app.command("set")
def author_set(
    slug: str = typer.Argument(...),
    person: str = typer.Option(..., "--person", help="Slug from shared/people.ttl"),
    role: str = typer.Option(None, "--role", help="Author's role within the institution"),
    disclosure: str = typer.Option(None, "--disclosure", help="Disclosure narrative"),
) -> None:
    with with_mutation(slug, question=6) as g:
        sub = get_submission_iri(g, slug)
        person_uri = URIRef(person_iri(person))
        if (person_uri, RDF.type, FOAF.Person) not in g:
            raise typer.BadParameter(
                f"person '{person}' not in shared/people.ttl"
            )
        g.remove((sub, MGJ.authoredBy, None))
        g.add((sub, MGJ.authoredBy, person_uri))
        if role is not None:
            g.remove((sub, MGJ.authorRole, None))
            g.add((sub, MGJ.authorRole, Literal(role)))
        if disclosure is not None:
            g.remove((sub, MGJ.authorDisclosure, None))
            g.add((sub, MGJ.authorDisclosure, Literal(disclosure)))
    console.print("[green]✓ author disclosure set[/green]")
