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
CANONICAL_IR_VERSION = "1.2"

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
class CanonicalDependency:
    """A statically resolved cross-section reference from an executable rule.

    The edge records syntax that names a section explicitly.  It does not
    infer a legal relationship from prose or a section number in a string.
    Runtime consumers must still resolve the target in the active statute
    registry and evaluate it against the active fact context.
    """

    citation_path: tuple[str, ...]
    source_kind: str
    declaration_index: int
    reference_kind: str
    target_section: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "citation_path": list(self.citation_path),
            "source_kind": self.source_kind,
            "declaration_index": self.declaration_index,
            "reference_kind": self.reference_kind,
            "target_section": self.target_section,
        }


@dataclass(frozen=True)
class CanonicalOutcomeTransition:
    """A source-local, typed criminal-outcome transition.

    The target is supplied by syntax, never inferred from an exception's
    prose effect. Runtime resolution is still required for an offence target.
    """

    citation_path: tuple[str, ...]
    source_kind: str
    declaration_index: int
    outcome_kind: str
    target: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "citation_path": list(self.citation_path),
            "source_kind": self.source_kind,
            "declaration_index": self.declaration_index,
            "outcome_kind": self.outcome_kind,
            "target": self.target,
        }


@dataclass(frozen=True)
class CanonicalProvision:
    """One scoped provision.  A child inherits its ancestor requirement path."""

    citation_path: tuple[str, ...]
    definitions: tuple[CanonicalNode, ...]
    elements: tuple[CanonicalRequirement, ...]
    penalties: tuple[CanonicalNode, ...]
    exceptions: tuple[CanonicalNode, ...]
    outcomes: tuple[CanonicalOutcomeTransition, ...]
    dependencies: tuple[CanonicalDependency, ...]
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
            "outcomes": [outcome.to_dict() for outcome in self.outcomes],
            "dependencies": [dependency.to_dict() for dependency in self.dependencies],
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
class CanonicalSourceNode:
    """A canonical node bound to the provision path that supplies it."""

    citation_path: tuple[str, ...]
    declaration_index: int
    node: CanonicalNode

    def to_dict(self) -> dict[str, Any]:
        return {
            "citation_path": list(self.citation_path),
            "declaration_index": self.declaration_index,
            "node": self.node.to_dict(),
        }


@dataclass(frozen=True)
class CanonicalRuleBranch:
    """An executable subsection leaf and its inherited requirements.

    A rule branch is selected if every inherited requirement evaluates true.
    Sibling branches are alternatives.  This is a structural composition rule,
    not an inference about prose-only cross references between provisions.
    """

    citation_path: tuple[str, ...]
    requirements: tuple[CanonicalRequirement, ...]
    penalties: tuple[CanonicalSourceNode, ...]
    exceptions: tuple[CanonicalSourceNode, ...]
    outcomes: tuple[CanonicalOutcomeTransition, ...]
    dependencies: tuple[CanonicalDependency, ...]

    @property
    def citation(self) -> str:
        section, *subsections = self.citation_path
        return f"s{section}{''.join(subsections)}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "citation_path": list(self.citation_path),
            "requirements": [requirement.to_dict() for requirement in self.requirements],
            "penalties": [penalty.to_dict() for penalty in self.penalties],
            "exceptions": [exception.to_dict() for exception in self.exceptions],
            "outcomes": [outcome.to_dict() for outcome in self.outcomes],
            "dependencies": [dependency.to_dict() for dependency in self.dependencies],
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
        "criminal_outcome": CapabilityStatus.MODELED,
        "cross_section_dependency": CapabilityStatus.MODELED,
        "penalty": CapabilityStatus.AST_ADAPTER,
        "civil_primitive": CapabilityStatus.AST_ADAPTER,
    },
    "runtime": {
        "statute": CapabilityStatus.MODELED,
        "subsection": CapabilityStatus.MODELED,
        "expression": CapabilityStatus.AST_ADAPTER,
        "exception": CapabilityStatus.AST_ADAPTER,
        "criminal_outcome": CapabilityStatus.MODELED,
        "cross_section_dependency": CapabilityStatus.MODELED,
        "penalty": CapabilityStatus.AST_ADAPTER,
        "civil_primitive": CapabilityStatus.UNSUPPORTED,
    },
    "z3": {
        "statute": CapabilityStatus.AST_ADAPTER,
        "subsection": CapabilityStatus.UNSUPPORTED,
        "expression": CapabilityStatus.AST_ADAPTER,
        "exception": CapabilityStatus.AST_ADAPTER,
        "criminal_outcome": CapabilityStatus.UNSUPPORTED,
        "cross_section_dependency": CapabilityStatus.MODELED,
        "penalty": CapabilityStatus.AST_ADAPTER,
        "civil_primitive": CapabilityStatus.UNSUPPORTED,
    },
    "alloy": {
        "statute": CapabilityStatus.AST_ADAPTER,
        "subsection": CapabilityStatus.UNSUPPORTED,
        "expression": CapabilityStatus.UNSUPPORTED,
        "exception": CapabilityStatus.UNSUPPORTED,
        "criminal_outcome": CapabilityStatus.UNSUPPORTED,
        "cross_section_dependency": CapabilityStatus.UNSUPPORTED,
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
        "criminal_outcome": CapabilityStatus.UNSUPPORTED,
        "cross_section_dependency": CapabilityStatus.UNSUPPORTED,
        "penalty": CapabilityStatus.UNSUPPORTED,
        "civil_primitive": CapabilityStatus.UNSUPPORTED,
    },
    "export": {
        "statute": CapabilityStatus.AST_ADAPTER,
        "subsection": CapabilityStatus.AST_ADAPTER,
        "expression": CapabilityStatus.AST_ADAPTER,
        "exception": CapabilityStatus.AST_ADAPTER,
        "criminal_outcome": CapabilityStatus.AST_ADAPTER,
        "cross_section_dependency": CapabilityStatus.AST_ADAPTER,
        "penalty": CapabilityStatus.AST_ADAPTER,
        "civil_primitive": CapabilityStatus.AST_ADAPTER,
    },
}


def lower_module(ast: nodes.ModuleNode, *, source: Optional[str] = None) -> CanonicalIR:
    """Lower an immutable AST module into canonical IR version ``1.2``."""
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


def rule_branches(statute: CanonicalStatute) -> tuple[CanonicalRuleBranch, ...]:
    """Return the statute's executable structural rule branches.

    A child inherits every ancestor requirement, exception, outcome, and penalty source.
    Element-bearing sibling leaves are alternatives.  Element-free provisions
    add definitions or other metadata but do not create a satisfiable branch.
    A provision with executable descendants is not itself a leaf; its elements
    instead constrain each executable child.  The empty result classifies the
    statute as ``definition_only`` at runtime.
    """

    branches: list[CanonicalRuleBranch] = []

    def has_executable_descendant(provision: CanonicalProvision) -> bool:
        return bool(provision.elements) or any(
            has_executable_descendant(child) for child in provision.children
        )

    def walk(
        provision: CanonicalProvision,
        inherited_requirements: tuple[CanonicalRequirement, ...],
        inherited_penalties: tuple[CanonicalSourceNode, ...],
        inherited_exceptions: tuple[CanonicalSourceNode, ...],
        inherited_outcomes: tuple[CanonicalOutcomeTransition, ...],
        inherited_dependencies: tuple[CanonicalDependency, ...],
    ) -> None:
        requirements = inherited_requirements + provision.elements
        penalties = inherited_penalties + tuple(
            CanonicalSourceNode(provision.citation_path, index, penalty)
            for index, penalty in enumerate(provision.penalties)
        )
        exceptions = inherited_exceptions + tuple(
            CanonicalSourceNode(provision.citation_path, index, exception)
            for index, exception in enumerate(provision.exceptions)
        )
        outcomes = inherited_outcomes + provision.outcomes
        dependencies = inherited_dependencies + provision.dependencies
        executable_children = tuple(
            child for child in provision.children if has_executable_descendant(child)
        )
        if executable_children:
            for child in executable_children:
                walk(child, requirements, penalties, exceptions, outcomes, dependencies)
            return
        if requirements:
            branches.append(
                CanonicalRuleBranch(
                    citation_path=provision.citation_path,
                    requirements=requirements,
                    penalties=penalties,
                    exceptions=exceptions,
                    outcomes=outcomes,
                    dependencies=dependencies,
                )
            )

    walk(statute.root, (), (), (), (), ())
    return tuple(branches)


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
    if provision.outcomes:
        features.append("criminal_outcome")
    if provision.dependencies:
        features.append("cross_section_dependency")
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
    outcomes = tuple(
        CanonicalOutcomeTransition(
            citation_path=citation_path,
            source_kind="exception",
            declaration_index=index,
            outcome_kind=exception.outcome.kind,
            target=exception.outcome.target,
        )
        for index, exception in enumerate(node.exceptions)
        if exception.outcome is not None
    ) + tuple(
        CanonicalOutcomeTransition(
            citation_path=citation_path,
            source_kind="outcome",
            declaration_index=index,
            outcome_kind=outcome.kind,
            target=outcome.target,
        )
        for index, outcome in enumerate(node.outcomes)
    )
    dependencies = tuple(
        CanonicalDependency(
            citation_path=citation_path,
            source_kind="exception",
            declaration_index=index,
            reference_kind=reference_kind,
            target_section=target_section,
        )
        for index, exception in enumerate(node.exceptions)
        for reference_kind, target_section in _guard_dependencies(exception.guard)
    )
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
        outcomes=outcomes,
        dependencies=dependencies,
        children=children,
        metadata=_metadata(
            node,
            exclude={
                "definitions",
                "elements",
                "penalty",
                "additional_penalties",
                "exceptions",
                "outcomes",
                "subsections",
            },
        ),
    )


def _guard_dependencies(
    guard: Optional[nodes.ASTNode],
) -> tuple[tuple[str, str], ...]:
    """Return explicit section references occurring in one exception guard.

    ``IsInfringedNode`` and ``ApplyScopeNode`` are produced only for grammar
    forms whose first argument is a statically known section reference.  This
    deliberately excludes prose and ordinary function calls from the rule
    graph.
    """
    if guard is None:
        return ()

    references: list[tuple[str, str]] = []
    stack: list[nodes.ASTNode] = [guard]
    while stack:
        current = stack.pop()
        if isinstance(current, nodes.IsInfringedNode):
            references.append(("is_infringed", current.section_ref))
        elif isinstance(current, nodes.ApplyScopeNode):
            references.append(("apply_scope", current.section_ref))
        stack.extend(child for child in current.children() if isinstance(child, nodes.ASTNode))
    return tuple(references)


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
