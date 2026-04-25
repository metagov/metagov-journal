"""
mgj.namespaces
--------------
Namespace bindings and IRI minting helpers for the Metagov Journal ontology.

A single source of truth for the IRI conventions:

    https://journal.metagov.org/ns/mgj#                ontology terms
    https://journal.metagov.org/institutions/{slug}    persistent institution IRIs
    https://journal.metagov.org/submissions/{slug}/    per-submission entity IRIs
    https://journal.metagov.org/people/{slug}          shared people registry
    https://journal.metagov.org/orgs/{slug}            shared organizations registry
    https://journal.metagov.org/roles/{slug}           SKOS role concepts
"""

from __future__ import annotations

from rdflib import Namespace
from rdflib.namespace import DCTERMS, FOAF, OWL, RDF, RDFS, SKOS, XSD

# Core mgj namespace (matches ontology/mgj.ttl).
MGJ = Namespace("https://journal.metagov.org/ns/mgj#")

# PROV-O.
PROV = Namespace("http://www.w3.org/ns/prov#")

# IRI roots for minted instance entities.
INSTITUTIONS_BASE = "https://journal.metagov.org/institutions/"
SUBMISSIONS_BASE = "https://journal.metagov.org/submissions/"
PEOPLE_BASE = "https://journal.metagov.org/people/"
ORGS_BASE = "https://journal.metagov.org/orgs/"
ROLES_BASE = "https://journal.metagov.org/roles/"


def institution_iri(slug: str) -> str:
    return f"{INSTITUTIONS_BASE}{slug}"


def submission_iri(slug: str, version: str) -> str:
    return f"{SUBMISSIONS_BASE}{slug}/v{version}"


def person_iri(slug: str) -> str:
    return f"{PEOPLE_BASE}{slug}"


def organization_iri(slug: str) -> str:
    return f"{ORGS_BASE}{slug}"


def role_iri(slug: str) -> str:
    return f"{ROLES_BASE}{slug}"


def submission_entity_iri(slug: str, version: str, kind: str, local_id: str) -> str:
    """Mint an IRI for a per-submission entity (Stakeholder, FieldSite, etc.).

    Example:
        submission_entity_iri("metagov-journal", "1.0.0", "stakeholder", "1")
        → "https://journal.metagov.org/submissions/metagov-journal/v1.0.0/stakeholder/1"
    """
    return f"{SUBMISSIONS_BASE}{slug}/v{version}/{kind}/{local_id}"


# Standard prefix block for SPARQL queries.
SPARQL_PREFIXES = """
PREFIX mgj:     <https://journal.metagov.org/ns/mgj#>
PREFIX foaf:    <http://xmlns.com/foaf/0.1/>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX skos:    <http://www.w3.org/2004/02/skos/core#>
PREFIX prov:    <http://www.w3.org/ns/prov#>
PREFIX rdfs:    <http://www.w3.org/2000/01/rdf-schema#>
PREFIX rdf:     <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX xsd:     <http://www.w3.org/2001/XMLSchema#>
"""


__all__ = [
    "MGJ",
    "PROV",
    "FOAF",
    "DCTERMS",
    "SKOS",
    "OWL",
    "RDF",
    "RDFS",
    "XSD",
    "INSTITUTIONS_BASE",
    "SUBMISSIONS_BASE",
    "PEOPLE_BASE",
    "ORGS_BASE",
    "ROLES_BASE",
    "institution_iri",
    "submission_iri",
    "person_iri",
    "organization_iri",
    "role_iri",
    "submission_entity_iri",
    "SPARQL_PREFIXES",
]
