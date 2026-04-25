"""
mgj.validate
------------
SHACL validation wrapper.

Two modes:

- ``validate(graph, mode="system")`` runs the full system shapes graph,
  enforcing cardinality, integrity, and the no-UnresolvedAgent rule. This
  is the gate the outer loop ("Conform") clears before compilation.

- ``validate(graph, mode="per_question", question=N)`` runs only the
  shapes for that question (q{N}-*.ttl). This is the inner-loop check
  invoked after every CLI mutation.

The data graph passed in must already include shared registries, so
SHACL ``sh:class foaf:Person`` constraints can resolve. The ontology is
loaded as ``ont_graph`` so SHACL can resolve class hierarchies during
validation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from pyshacl import validate as _pyshacl_validate
from rdflib import Graph

from mgj.graph import (
    load_ontology,
    load_per_question_shapes,
    load_system_shapes,
)


Mode = Literal["per_question", "system"]


@dataclass(frozen=True)
class ValidationViolation:
    focus_node: str
    result_path: str
    message: str
    severity: str
    source_shape: str


@dataclass
class ValidationReport:
    conforms: bool
    violations: list[ValidationViolation] = field(default_factory=list)
    raw_report: str = ""

    @property
    def violation_count(self) -> int:
        return len(self.violations)

    def __str__(self) -> str:
        if self.conforms:
            return "OK: graph conforms"
        lines = [f"FAIL: {self.violation_count} violation(s)"]
        for v in self.violations:
            lines.append(f"  [{v.severity.split('#')[-1]}] focus={v.focus_node}")
            if v.result_path:
                lines.append(f"    path: {v.result_path}")
            if v.message:
                lines.append(f"    msg:  {v.message}")
        return "\n".join(lines)


def _parse_report(report_graph: Graph) -> list[ValidationViolation]:
    q = """
    PREFIX sh: <http://www.w3.org/ns/shacl#>
    SELECT ?focusNode ?resultPath ?message ?severity ?sourceShape
    WHERE {
      ?r a sh:ValidationResult ;
         sh:focusNode      ?focusNode ;
         sh:resultSeverity ?severity ;
         sh:sourceShape    ?sourceShape .
      OPTIONAL { ?r sh:resultPath    ?resultPath }
      OPTIONAL { ?r sh:resultMessage ?message }
    }
    """
    violations: list[ValidationViolation] = []
    for row in report_graph.query(q):
        violations.append(
            ValidationViolation(
                focus_node=str(row.focusNode),
                result_path=str(row.resultPath) if row.resultPath else "",
                message=str(row.message) if row.message else "",
                severity=str(row.severity),
                source_shape=str(row.sourceShape),
            )
        )
    return violations


def validate(
    data_graph: Graph,
    *,
    mode: Mode = "system",
    question: int | None = None,
) -> ValidationReport:
    """Validate ``data_graph`` against the appropriate SHACL shapes.

    Parameters
    ----------
    data_graph
        The submission graph. Should already include shared registries
        (people, orgs) so foaf:Person / foaf:Organization references resolve.
    mode
        ``"system"`` runs the full system shapes; ``"per_question"`` runs
        the shapes for the given question only.
    question
        Required when ``mode="per_question"``; ignored otherwise.
    """
    if mode == "per_question":
        if question is None:
            raise ValueError("question is required when mode='per_question'")
        shapes = load_per_question_shapes(question)
    elif mode == "system":
        shapes = load_system_shapes()
    else:
        raise ValueError(f"unknown mode: {mode!r}")

    ontology = load_ontology()

    conforms, report_graph, report_text = _pyshacl_validate(
        data_graph,
        shacl_graph=shapes,
        ont_graph=ontology,
        inference="none",
        abort_on_first=False,
        serialize_report_graph=False,
        advanced=True,
    )

    return ValidationReport(
        conforms=bool(conforms),
        violations=_parse_report(report_graph),
        raw_report=report_text,
    )


def validate_file(
    path: str | Path,
    *,
    mode: Mode = "system",
    question: int | None = None,
    with_shared: bool = True,
) -> ValidationReport:
    """Load ``path`` and validate. ``with_shared`` controls whether shared
    registries are merged before validation."""
    from mgj.graph import load_instance

    data_graph = load_instance(path, with_shared=with_shared)
    return validate(data_graph, mode=mode, question=question)


__all__ = [
    "Mode",
    "ValidationViolation",
    "ValidationReport",
    "validate",
    "validate_file",
]
