"""The versioned, serialisable semantic boundary for Yuho.

The parser and Python AST are intentionally not a backend contract.  This
module lowers AST values into a deterministic, immutable representation that
can be persisted, hashed, inspected, and passed to semantic consumers.

The initial schema has typed statute/provision/element nodes because those are
the executable criminal-law fragment.  ``snapshot`` retains the full module
shape for AST constructs that have not migrated yet.  Consumers must declare
an AST-adapter or unsupported capability for those constructs; they may not
silently treat parser acceptance as semantic support.
"""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from hashlib import sha256
import json
from typing import Any, Iterable, Mapping, Optional, Union

from yuho.ast import nodes

CANONICAL_IR_SCHEMA = "yuho.canonical-ir"
CANONICAL_IR_VERSION = "1.0"

JSONScalar = Union[str, int, float, bool, None]
CanonicalValue = Union[JSONScalar, "CanonicalNode", tuple["CanonicalValue", ...]]


@dataclass(frozen=True)
class CanonicalNode:
    """A deterministic snapshot of an AST node that has no dedicated IR type."""

    kind: str
    fields: tuple[tuple[str, CanonicalValue], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "fields": {name: _value_to_data(value) for name, value in self.fields},
        }


@dataclass(frozen=True)
class CanonicalElement:
    """A statutory element with its source-path-local identity."""

    name: str
    element_type: str
    description: CanonicalValue
    burden: Optional[str]
    burden_standard: Optional[str]
    citation_path: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "element_type": self.element_type,
            "description": _value_to_data(self.description),
            "burden": self.burden,
            "burden_standard": self.burden_standard,
            "citation_path": list(self.citation_path),
        }


@dataclass(frozen=True)
class CanonicalElementGroup:
    """An ``all_of`` or ``any_of`` requirement tree."""

    combinator: str
    members: tuple["CanonicalRequirement", ...]
    citation_path: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "combinator": self.combinator,
            "members": [member.to_dict() for member in self.members],
            "citation_path": list(self.citation_path),
        }


CanonicalRequirement = Union[CanonicalElement, CanonicalElementGroup, CanonicalNode]


@dataclass(frozen=True)
class CanonicalProvision:
    """One scoped provision.  A child inherits its ancestor requirement path."""

    citation_path: tuple[str, ...]
    definitions: tuple[CanonicalNode, ...]
    elements: tuple[CanonicalRequirement, ...]
    penalties: tuple[CanonicalNode, ...]
    exceptions: tuple[CanonicalNode, ...]
    children: tuple["CanonicalProvision", ...]
    metadata: tuple[tuple[str, CanonicalValue], ...] = ()

    @property
    def citation(self) -> str:
        section, *subsections = self.citation_path
        return f"s{section}{''.join(subsections)}"

    @property
    def has_executable_elements(self) -> bool:
        return bool(self.elements)

    def to_dict(self) -> dict[str, Any]:
        return {
            "citation_path": list(self.citation_path),
            "definitions": [definition.to_dict() for definition in self.definitions],
            "elements": [element.to_dict() for element in self.elements],
            "penalties": [penalty.to_dict() for penalty in self.penalties],
            "exceptions": [exception.to_dict() for exception in self.exceptions],
            "children": [child.to_dict() for child in self.children],
            "metadata": {name: _value_to_data(value) for name, value in self.metadata},
        }


@dataclass(frozen=True)
class CanonicalStatute:
    """A statute and the scoped provisions that make up its rule graph."""

    section_number: str
    title: Optional[str]
    jurisdiction: Optional[str]
    effective_dates: tuple[str, ...]
    root: CanonicalProvision
    metadata: tuple[tuple[str, CanonicalValue], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "section_number": self.section_number,
            "title": self.title,
            "jurisdiction": self.jurisdiction,
            "effective_dates": list(self.effective_dates),
            "root": self.root.to_dict(),
            "metadata": {name: _value_to_data(value) for name, value in self.metadata},
        }


@dataclass(frozen=True)
class CanonicalModule:
    """Canonical semantic data for the module's currently covered fragment."""

    statutes: tuple[CanonicalStatute, ...]
    snapshot: CanonicalNode

    def to_dict(self) -> dict[str, Any]:
        return {
            "statutes": [statute.to_dict() for statute in self.statutes],
            "snapshot": self.snapshot.to_dict(),
        }


@dataclass(frozen=True)
class CanonicalIR:
    """A versioned IR artifact with deterministic serialisation and digest."""

    schema: str
    version: str
    module: CanonicalModule
    source_hash: Optional[str] = None

    def to_dict(self, *, include_source_hash: bool = True) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "schema": self.schema,
            "version": self.version,
            "module": self.module.to_dict(),
        }
        if include_source_hash and self.source_hash is not None:
            payload["source_hash"] = self.source_hash
        return payload

    def serialize(self) -> bytes:
        """Return the canonical UTF-8 JSON byte sequence for this artifact."""
        return json.dumps(
            self.to_dict(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")

    @property
    def digest(self) -> str:
        """Return the semantic digest, intentionally independent of source bytes."""
        semantic_bytes = json.dumps(
            self.to_dict(include_source_hash=False),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
        return sha256(semantic_bytes).hexdigest()

    @property
    def artifact_digest(self) -> str:
        """Return the digest of the IR plus optional normalized source-text provenance."""
        return sha256(self.serialize()).hexdigest()


class CapabilityStatus(str, Enum):
    """The semantic relation a consumer has to an IR feature."""

    MODELED = "modeled"
    AST_ADAPTER = "ast_adapter"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True)
class CapabilityDiagnostic:
    """An explicit unsupported consumer/feature combination."""

    consumer: str
    feature: str
    status: CapabilityStatus
    message: str
    citation_path: tuple[str, ...] = ()

    @property
    def code(self) -> str:
        return f"YIR{self.consumer.upper()}001"

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "consumer": self.consumer,
            "feature": self.feature,
            "status": self.status.value,
            "message": self.message,
            "citation_path": list(self.citation_path),
        }


_CAPABILITY_MATRIX: Mapping[str, Mapping[str, CapabilityStatus]] = {
    # Runtime element evaluation moves through the typed statute IR.  Legacy
    # expressions and exceptions retain a named AST adapter until their own IR
    # evaluator lands; this is not the same as silently claiming support.
    "semantic": {
        "statute": CapabilityStatus.MODELED,
        "subsection": CapabilityStatus.MODELED,
        "expression": CapabilityStatus.AST_ADAPTER,
        "exception": CapabilityStatus.AST_ADAPTER,
        "penalty": CapabilityStatus.AST_ADAPTER,
        "civil_primitive": CapabilityStatus.AST_ADAPTER,
    },
    "runtime": {
        "statute": CapabilityStatus.MODELED,
        "subsection": CapabilityStatus.UNSUPPORTED,
        "expression": CapabilityStatus.AST_ADAPTER,
        "exception": CapabilityStatus.AST_ADAPTER,
        "penalty": CapabilityStatus.UNSUPPORTED,
        "civil_primitive": CapabilityStatus.UNSUPPORTED,
    },
    "z3": {
        "statute": CapabilityStatus.AST_ADAPTER,
        "subsection": CapabilityStatus.AST_ADAPTER,
        "expression": CapabilityStatus.AST_ADAPTER,
        "exception": CapabilityStatus.AST_ADAPTER,
        "penalty": CapabilityStatus.AST_ADAPTER,
        "civil_primitive": CapabilityStatus.UNSUPPORTED,
    },
    "alloy": {
        "statute": CapabilityStatus.AST_ADAPTER,
        "subsection": CapabilityStatus.UNSUPPORTED,
        "expression": CapabilityStatus.UNSUPPORTED,
        "exception": CapabilityStatus.UNSUPPORTED,
        "penalty": CapabilityStatus.UNSUPPORTED,
        "civil_primitive": CapabilityStatus.UNSUPPORTED,
    },
    # Lean consumes generated fixture artifacts rather than production IR in
    # v1.  Keep that boundary explicit until #45 proves a bounded refinement.
    "lean": {
        "statute": CapabilityStatus.UNSUPPORTED,
        "subsection": CapabilityStatus.UNSUPPORTED,
        "expression": CapabilityStatus.UNSUPPORTED,
        "exception": CapabilityStatus.UNSUPPORTED,
        "penalty": CapabilityStatus.UNSUPPORTED,
        "civil_primitive": CapabilityStatus.UNSUPPORTED,
    },
    "export": {
        "statute": CapabilityStatus.AST_ADAPTER,
        "subsection": CapabilityStatus.AST_ADAPTER,
        "expression": CapabilityStatus.AST_ADAPTER,
        "exception": CapabilityStatus.AST_ADAPTER,
        "penalty": CapabilityStatus.AST_ADAPTER,
        "civil_primitive": CapabilityStatus.AST_ADAPTER,
    },
}


def lower_module(ast: nodes.ModuleNode, *, source: Optional[str] = None) -> CanonicalIR:
    """Lower an immutable AST module into canonical IR version ``1.0``."""
    source_hash = None
    if source is not None:
        source_hash = sha256(source.encode("utf-8")).hexdigest()
    return CanonicalIR(
        schema=CANONICAL_IR_SCHEMA,
        version=CANONICAL_IR_VERSION,
        module=CanonicalModule(
            statutes=tuple(lower_statute(statute) for statute in ast.statutes),
            snapshot=_lower_node(ast),
        ),
        source_hash=source_hash,
    )


def lower_statute(statute: nodes.StatuteNode) -> CanonicalStatute:
    """Lower a statute into a scoped canonical provision tree."""
    section = statute.section_number
    root = _lower_provision(statute, (section,))
    title = statute.title.value if statute.title is not None else None
    metadata = _metadata(
        statute,
        exclude={
            "section_number",
            "title",
            "jurisdiction",
            "effective_dates",
            "elements",
            "definitions",
            "penalty",
            "additional_penalties",
            "exceptions",
            "subsections",
        },
    )
    return CanonicalStatute(
        section_number=section,
        title=title,
        jurisdiction=statute.jurisdiction,
        effective_dates=tuple(statute.effective_dates),
        root=root,
        metadata=metadata,
    )


def canonical_hash(value: Union[CanonicalIR, CanonicalModule, CanonicalStatute]) -> str:
    """Hash a canonical artifact with the same serialisation rules as ``CanonicalIR``."""
    if isinstance(value, CanonicalIR):
        return value.digest
    payload = {
        "schema": CANONICAL_IR_SCHEMA,
        "version": CANONICAL_IR_VERSION,
        "artifact": value.to_dict(),
    }
    serialized = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return sha256(serialized).hexdigest()


def diagnose_capabilities(
    ir: CanonicalIR,
    consumer: str,
) -> tuple[CapabilityDiagnostic, ...]:
    """Return explicit diagnostics for unsupported IR consumer combinations."""
    capabilities = _CAPABILITY_MATRIX.get(consumer)
    if capabilities is None:
        raise ValueError(f"unknown canonical-IR consumer: {consumer}")

    diagnostics: list[CapabilityDiagnostic] = []
    for statute in ir.module.statutes:
        _diagnose_provision(statute.root, consumer, capabilities, diagnostics)
    return tuple(diagnostics)


def diagnose_statute_capabilities(
    statute: CanonicalStatute,
    consumer: str,
) -> tuple[CapabilityDiagnostic, ...]:
    """Return explicit consumer diagnostics for one canonical statute."""
    capabilities = _CAPABILITY_MATRIX.get(consumer)
    if capabilities is None:
        raise ValueError(f"unknown canonical-IR consumer: {consumer}")
    diagnostics: list[CapabilityDiagnostic] = []
    _diagnose_provision(statute.root, consumer, capabilities, diagnostics)
    return tuple(diagnostics)


def _diagnose_provision(
    provision: CanonicalProvision,
    consumer: str,
    capabilities: Mapping[str, CapabilityStatus],
    diagnostics: list[CapabilityDiagnostic],
) -> None:
    features: list[str] = ["statute"]
    if len(provision.citation_path) > 1:
        features.append("subsection")
    if provision.penalties:
        features.append("penalty")
    if provision.exceptions:
        features.append("exception")
    if any(isinstance(element, CanonicalNode) for element in provision.elements):
        features.append("civil_primitive")
    if _provision_uses_expression(provision):
        features.append("expression")

    for feature in features:
        status = capabilities[feature]
        if status is CapabilityStatus.UNSUPPORTED:
            diagnostics.append(
                CapabilityDiagnostic(
                    consumer=consumer,
                    feature=feature,
                    status=status,
                    message=(
                        f"{consumer} does not support canonical-IR {feature} semantics "
                        f"at {provision.citation}"
                    ),
                    citation_path=provision.citation_path,
                )
            )
    for child in provision.children:
        _diagnose_provision(child, consumer, capabilities, diagnostics)


def _provision_uses_expression(provision: CanonicalProvision) -> bool:
    def requirement_uses_expression(requirement: CanonicalRequirement) -> bool:
        if isinstance(requirement, CanonicalNode):
            return False
        if isinstance(requirement, CanonicalElement):
            return isinstance(
                requirement.description, CanonicalNode
            ) and requirement.description.kind not in {
                "StringLit",
                "BoolLit",
                "IntLit",
                "FloatLit",
                "MoneyNode",
                "PercentNode",
                "DateNode",
                "DurationNode",
            }
        return any(requirement_uses_expression(member) for member in requirement.members)

    return any(requirement_uses_expression(element) for element in provision.elements)


def _lower_provision(
    node: Union[nodes.StatuteNode, nodes.SubsectionNode],
    citation_path: tuple[str, ...],
) -> CanonicalProvision:
    penalties = tuple(_lower_node(penalty) for penalty in _penalties(node))
    definitions = tuple(_lower_node(definition) for definition in node.definitions)
    exceptions = tuple(_lower_node(exception) for exception in node.exceptions)
    children = tuple(
        _lower_provision(subsection, citation_path + (subsection.number,))
        for subsection in node.subsections
    )
    return CanonicalProvision(
        citation_path=citation_path,
        definitions=definitions,
        elements=tuple(_lower_requirement(member, citation_path) for member in node.elements),
        penalties=penalties,
        exceptions=exceptions,
        children=children,
        metadata=_metadata(
            node,
            exclude={
                "definitions",
                "elements",
                "penalty",
                "additional_penalties",
                "exceptions",
                "subsections",
            },
        ),
    )


def _penalties(node: Union[nodes.StatuteNode, nodes.SubsectionNode]) -> Iterable[nodes.PenaltyNode]:
    if node.penalty is not None:
        yield node.penalty
    yield from node.additional_penalties


def _lower_requirement(
    member: Union[nodes.ElementNode, nodes.ElementGroupNode, nodes.CivilPrimitiveNode],
    citation_path: tuple[str, ...],
) -> CanonicalRequirement:
    if isinstance(member, nodes.ElementNode):
        return CanonicalElement(
            name=member.name,
            element_type=member.element_type,
            description=_lower_value(member.description),
            burden=member.burden,
            burden_standard=member.burden_standard,
            citation_path=citation_path,
        )
    if isinstance(member, nodes.ElementGroupNode):
        return CanonicalElementGroup(
            combinator=member.combinator,
            members=tuple(_lower_requirement(child, citation_path) for child in member.members),
            citation_path=citation_path,
        )
    return _lower_node(member)


def _metadata(node: object, *, exclude: set[str]) -> tuple[tuple[str, CanonicalValue], ...]:
    if not is_dataclass(node):
        return ()
    return tuple(
        (field.name, _lower_value(getattr(node, field.name)))
        for field in fields(node)
        if field.name not in exclude and field.name != "source_location"
    )


def _lower_node(node: object) -> CanonicalNode:
    if not is_dataclass(node):
        raise TypeError(f"canonical node requires a dataclass, got {type(node).__name__}")
    return CanonicalNode(
        kind=type(node).__name__,
        fields=tuple(
            (field.name, _lower_value(getattr(node, field.name)))
            for field in fields(node)
            if field.name != "source_location"
        ),
    )


def _lower_value(value: object) -> CanonicalValue:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Enum):
        return _lower_value(value.value)
    if isinstance(value, (date, datetime, Decimal)):
        return str(value)
    if isinstance(value, Mapping):
        return CanonicalNode(
            kind="mapping",
            fields=tuple(
                (str(key), _lower_value(item))
                for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
            ),
        )
    if isinstance(value, (tuple, list)):
        return tuple(_lower_value(item) for item in value)
    if is_dataclass(value):
        return _lower_node(value)
    raise TypeError(f"canonical IR cannot serialise {type(value).__name__}")


def _value_to_data(value: CanonicalValue) -> Any:
    if isinstance(value, CanonicalNode):
        return value.to_dict()
    if isinstance(value, tuple):
        return [_value_to_data(item) for item in value]
    return value
