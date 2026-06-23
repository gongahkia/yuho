"""LegalRuleML v1.0 compact XML transpiler."""

from __future__ import annotations

from decimal import Decimal
from html import escape
from typing import Iterable, List, Optional, Sequence, Union

from yuho.ast import nodes
from yuho.transpile.base import TranspileResult, TranspileTarget, TranspilerBase


_LRML_NS = "http://docs.oasis-open.org/legalruleml/ns/v1.0/"
_RULEML_NS = "http://ruleml.org/spec"
_SCHEMA_LOCATION = (
    "http://docs.oasis-open.org/legalruleml/ns/v1.0/ "
    "https://docs.oasis-open.org/legalruleml/legalruleml-core-spec/v1.0/os/"
    "xsd-schema/compact/lrml-compact.xsd"
)
_DEONTIC = {
    "obligation": "Obligation",
    "prohibition": "Prohibition",
    "permission": "Permission",
}


class LegalRuleMLTranspiler(TranspilerBase):
    def __init__(
        self,
        *,
        base_iri: str = "https://github.com/gongahkia/yuho",
        indent: int = 2,
    ) -> None:
        self.base_iri = base_iri.rstrip("/")
        self.indent = indent
        self._depth = 0

    @property
    def target(self) -> TranspileTarget:
        return TranspileTarget.LEGALRULEML

    def transpile(self, ast: nodes.ModuleNode) -> TranspileResult:
        self._depth = 0
        lines: List[str] = ['<?xml version="1.0" encoding="UTF-8"?>']
        lines.append(
            f'<lrml:LegalRuleML xml:base="{escape(self.base_iri)}/legalruleml" '
            'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
            f'xmlns:lrml="{_LRML_NS}" xmlns:ruleml="{_RULEML_NS}" '
            f'xsi:schemaLocation="{escape(_SCHEMA_LOCATION)}">'
        )
        self._depth = 1
        lines.extend(self._legal_sources(ast.statutes))
        lines.extend(self._sources(ast.statutes))
        lines.extend(self._contexts(ast.statutes))
        lines.append(self._pad('<lrml:Statements key="yuho_statements">'))
        self._depth += 1
        for statute in ast.statutes:
            lines.extend(self._statute_statement(statute))
            lines.extend(self._subsection_statements(statute))
            lines.extend(self._facts(statute))
            lines.extend(self._penalties(statute))
            lines.extend(self._exceptions(statute))
            lines.extend(self._subsection_exceptions(statute))
        self._depth -= 1
        lines.append(self._pad("</lrml:Statements>"))
        self._depth = 0
        lines.append("</lrml:LegalRuleML>")
        return self.result(
            "\n".join(lines) + "\n",
            manifest={"format": "legalruleml", "namespace": _LRML_NS},
            source_ast=ast,
        )

    def _legal_sources(self, statutes: Sequence[nodes.StatuteNode]) -> List[str]:
        if not statutes:
            return []
        lines = [self._pad('<lrml:LegalSources key="legal_sources">')]
        self._depth += 1
        for statute in statutes:
            key = self._statute_key(statute)
            lines.append(
                self._pad(
                    f'<lrml:LegalSource key="ls_{key}" '
                    f'sameAs="{escape(self.base_iri)}/section/{escape(statute.section_number)}"/>'
                )
            )
        self._depth -= 1
        lines.append(self._pad("</lrml:LegalSources>"))
        return lines

    def _sources(self, statutes: Sequence[nodes.StatuteNode]) -> List[str]:
        if not statutes:
            return []
        lines = [self._pad('<lrml:Sources key="yuho_sources">')]
        self._depth += 1
        for statute in statutes:
            key = self._statute_key(statute)
            lines.append(self._pad(f'<lrml:Source key="src_{key}" sameAs="#ls_{key}"/>'))
        self._depth -= 1
        lines.append(self._pad("</lrml:Sources>"))
        return lines

    def _contexts(self, statutes: Sequence[nodes.StatuteNode]) -> List[str]:
        lines: List[str] = []
        for statute in statutes:
            key = self._statute_key(statute)
            lines.extend(self._context(f"ctx_{key}", "StrictStrength", f"ps_{key}"))
            for sub in self._iter_subsections(statute.subsections):
                sub_key = self._subsection_key(statute, sub)
                lines.extend(self._context(f"ctx_{sub_key}", "StrictStrength", f"ps_{sub_key}"))
                for exc in sub.exceptions:
                    exc_key = self._subsection_exception_key(statute, sub, exc)
                    lines.extend(self._context(f"ctx_{exc_key}", "Defeater", f"ps_{exc_key}"))
            for exc in statute.exceptions:
                exc_key = self._exception_key(statute, exc)
                lines.extend(self._context(f"ctx_{exc_key}", "Defeater", f"ps_{exc_key}"))
        return lines

    def _context(self, key: str, strength: str, scope: str) -> List[str]:
        strength_key = f"str_{self._slug(key)}"
        lines = [self._pad(f'<lrml:Context key="{escape(key)}">')]
        self._depth += 1
        lines.append(self._pad("<lrml:appliesStrength>"))
        self._depth += 1
        lines.append(self._pad(f'<lrml:{strength} key="{escape(strength_key)}"/>'))
        self._depth -= 1
        lines.append(self._pad("</lrml:appliesStrength>"))
        lines.append(self._pad(f'<lrml:inScope keyref="#{escape(scope)}"/>'))
        self._depth -= 1
        lines.append(self._pad("</lrml:Context>"))
        return lines

    def _statute_statement(self, statute: nodes.StatuteNode) -> List[str]:
        key = self._statute_key(statute)
        lines = [self._pad(f'<lrml:PrescriptiveStatement key="ps_{escape(key)}">')]
        self._depth += 1
        lines.extend(
            self._rule(
                key=f"rule_{key}",
                body=statute.elements,
                head=self._prohibition(
                    key=f"prohib_{key}",
                    rel=f"offence_{key}",
                    text=self._title(statute),
                ),
                strength="defeasible" if statute.exceptions else "StrictStrength",
            )
        )
        self._depth -= 1
        lines.append(self._pad("</lrml:PrescriptiveStatement>"))
        return lines

    def _subsection_statements(self, statute: nodes.StatuteNode) -> List[str]:
        lines: List[str] = []
        for sub in self._iter_subsections(statute.subsections):
            key = self._subsection_key(statute, sub)
            lines.append(self._pad(f'<lrml:PrescriptiveStatement key="ps_{escape(key)}">'))
            self._depth += 1
            lines.extend(
                self._rule(
                    key=f"rule_{key}",
                    body=sub.elements,
                    head=self._prohibition(
                        key=f"prohib_{key}",
                        rel=f"offence_{key}",
                        text=f"section {statute.section_number} {sub.number}",
                    ),
                    strength="defeasible" if sub.exceptions else "StrictStrength",
                )
            )
            self._depth -= 1
            lines.append(self._pad("</lrml:PrescriptiveStatement>"))
        return lines

    def _facts(self, statute: nodes.StatuteNode) -> List[str]:
        lines: List[str] = []
        key = self._statute_key(statute)
        for definition in statute.definitions:
            fact_key = f"fact_{key}_def_{self._slug(definition.term)}"
            lines.extend(
                self._fact(
                    fact_key,
                    "definition",
                    [definition.term, self._expr_text(definition.definition)],
                )
            )
        for case in statute.case_law:
            fact_key = f"fact_{key}_case_{self._slug(self._expr_text(case.case_name))}"
            args = [self._expr_text(case.case_name), self._expr_text(case.holding)]
            if case.citation:
                args.append(self._expr_text(case.citation))
            if case.element_ref:
                args.append(case.element_ref)
            lines.extend(self._fact(fact_key, "case_law", args))
        return lines

    def _fact(self, key: str, rel: str, args: Sequence[str]) -> List[str]:
        lines = [self._pad(f'<lrml:FactualStatement key="{escape(key)}">')]
        self._depth += 1
        lines.append(self._pad("<lrml:hasTemplate>"))
        self._depth += 1
        lines.extend(self._atom(f"atom_{key}", rel, args))
        self._depth -= 1
        lines.append(self._pad("</lrml:hasTemplate>"))
        self._depth -= 1
        lines.append(self._pad("</lrml:FactualStatement>"))
        return lines

    def _penalties(self, statute: nodes.StatuteNode) -> List[str]:
        all_penalties = [p for p in (statute.penalty, *statute.additional_penalties) if p]
        lines: List[str] = []
        for idx, penalty in enumerate(all_penalties, start=1):
            key = f"pen_{self._statute_key(statute)}_{idx}"
            lines.append(self._pad(f'<lrml:PenaltyStatement key="{escape(key)}">'))
            self._depth += 1
            lines.extend(
                self._obligation(
                    key=f"oblig_{key}",
                    rel=f"penalty_{self._statute_key(statute)}",
                    text=self._penalty_text(penalty),
                )
            )
            self._depth -= 1
            lines.append(self._pad("</lrml:PenaltyStatement>"))
            lines.append(self._pad(f'<lrml:ReparationStatement key="rep_{escape(key)}">'))
            self._depth += 1
            lines.append(self._pad(f'<lrml:Reparation key="rep_link_{escape(key)}">'))
            self._depth += 1
            lines.append(self._pad(f'<lrml:appliesPenalty keyref="#{escape(key)}"/>'))
            lines.append(
                self._pad(
                    f'<lrml:toPrescriptiveStatement keyref="#ps_{escape(self._statute_key(statute))}"/>'
                )
            )
            self._depth -= 1
            lines.append(self._pad("</lrml:Reparation>"))
            self._depth -= 1
            lines.append(self._pad("</lrml:ReparationStatement>"))
        return lines

    def _exceptions(self, statute: nodes.StatuteNode) -> List[str]:
        lines: List[str] = []
        for exc in statute.exceptions:
            key = self._exception_key(statute, exc)
            target = self._exception_target_key(statute, exc)
            lines.append(self._pad(f'<lrml:PrescriptiveStatement key="ps_{escape(key)}">'))
            self._depth += 1
            body = [self._exception_atom(statute, exc)]
            lines.extend(
                self._rule(
                    key=f"rule_{key}",
                    body=body,
                    head=self._negated_offence(statute),
                    strength="defeater",
                )
            )
            self._depth -= 1
            lines.append(self._pad("</lrml:PrescriptiveStatement>"))
            lines.append(self._pad(f'<lrml:OverrideStatement key="ovr_{escape(key)}">'))
            self._depth += 1
            lines.append(
                self._pad(f'<lrml:Override over="#ps_{escape(key)}" under="#ps_{escape(target)}"/>')
            )
            self._depth -= 1
            lines.append(self._pad("</lrml:OverrideStatement>"))
        return lines

    def _subsection_exceptions(self, statute: nodes.StatuteNode) -> List[str]:
        lines: List[str] = []
        for sub in self._iter_subsections(statute.subsections):
            sub_key = self._subsection_key(statute, sub)
            for exc in sub.exceptions:
                key = self._subsection_exception_key(statute, sub, exc)
                target = self._subsection_exception_target_key(statute, sub, exc)
                lines.append(self._pad(f'<lrml:PrescriptiveStatement key="ps_{escape(key)}">'))
                self._depth += 1
                body = [self._exception_atom_for_key(sub_key, exc)]
                lines.extend(
                    self._rule(
                        key=f"rule_{key}",
                        body=body,
                        head=self._negated_offence(statute),
                        strength="defeater",
                    )
                )
                self._depth -= 1
                lines.append(self._pad("</lrml:PrescriptiveStatement>"))
                lines.append(self._pad(f'<lrml:OverrideStatement key="ovr_{escape(key)}">'))
                self._depth += 1
                lines.append(
                    self._pad(
                        f'<lrml:Override over="#ps_{escape(key)}" under="#ps_{escape(target)}"/>'
                    )
                )
                self._depth -= 1
                lines.append(self._pad("</lrml:OverrideStatement>"))
        return lines

    def _rule(
        self,
        *,
        key: str,
        body: Sequence[Union[nodes.ElementNode, nodes.ElementGroupNode, List[str]]],
        head: List[str],
        strength: str,
    ) -> List[str]:
        lines = [
            self._pad(
                f'<ruleml:Rule key=":{escape(key)}" closure="universal" '
                f'strength="{escape(strength)}">'
            )
        ]
        self._depth += 1
        lines.append(self._pad("<ruleml:if>"))
        self._depth += 1
        lines.extend(self._body(body))
        self._depth -= 1
        lines.append(self._pad("</ruleml:if>"))
        lines.append(self._pad("<ruleml:then>"))
        self._depth += 1
        lines.extend(head)
        self._depth -= 1
        lines.append(self._pad("</ruleml:then>"))
        self._depth -= 1
        lines.append(self._pad("</ruleml:Rule>"))
        return lines

    def _body(
        self,
        body: Sequence[Union[nodes.ElementNode, nodes.ElementGroupNode, List[str]]],
    ) -> List[str]:
        if len(body) == 1 and isinstance(body[0], list):
            return body[0]
        return self._group("And", body)

    def _group(
        self,
        tag: str,
        members: Iterable[Union[nodes.ElementNode, nodes.ElementGroupNode, List[str]]],
    ) -> List[str]:
        lines = [self._pad(f"<ruleml:{tag}>")]
        self._depth += 1
        for member in members:
            if isinstance(member, list):
                lines.extend(member)
            elif isinstance(member, nodes.ElementGroupNode):
                child_tag = "And" if member.combinator == "all_of" else "Or"
                lines.extend(self._group(child_tag, member.members))
            else:
                lines.extend(self._element(member))
        self._depth -= 1
        lines.append(self._pad(f"</ruleml:{tag}>"))
        return lines

    def _element(self, el: nodes.ElementNode) -> List[str]:
        rel = f"{self._slug(el.element_type)}_{self._slug(el.name)}"
        args = [self._expr_text(el.description)]
        agent = el.agent or el.actor
        if agent:
            args.append(f"actor:{agent}")
        if el.patient:
            args.append(f"patient:{el.patient}")
        atom = self._atom(f"atom_{rel}", rel, args)
        deontic = _DEONTIC.get(el.element_type)
        if not deontic:
            return atom
        key = f"{deontic.lower()}_{self._slug(el.name)}"
        lines = [self._pad(f'<lrml:{deontic} key="{escape(key)}">')]
        self._depth += 1
        if agent:
            lines.extend(self._bearer(agent))
        lines.extend(atom)
        self._depth -= 1
        lines.append(self._pad(f"</lrml:{deontic}>"))
        return lines

    def _prohibition(self, *, key: str, rel: str, text: str) -> List[str]:
        lines = [self._pad(f'<lrml:Prohibition key="{escape(key)}">')]
        self._depth += 1
        lines.extend(self._atom(f"atom_{key}", rel, [text]))
        self._depth -= 1
        lines.append(self._pad("</lrml:Prohibition>"))
        return lines

    def _obligation(self, *, key: str, rel: str, text: str) -> List[str]:
        lines = [self._pad(f'<lrml:Obligation key="{escape(key)}">')]
        self._depth += 1
        lines.extend(self._atom(f"atom_{key}", rel, [text]))
        self._depth -= 1
        lines.append(self._pad("</lrml:Obligation>"))
        return lines

    def _bearer(self, value: str) -> List[str]:
        lines = [self._pad("<ruleml:slot>")]
        self._depth += 1
        lines.append(self._pad('<lrml:Bearer iri="yuho:actor"/>'))
        lines.append(self._pad(f"<ruleml:Ind>{escape(value)}</ruleml:Ind>"))
        self._depth -= 1
        lines.append(self._pad("</ruleml:slot>"))
        return lines

    def _atom(self, key: str, rel: str, args: Sequence[str]) -> List[str]:
        lines = [self._pad(f'<ruleml:Atom key=":{escape(self._slug(key))}">')]
        self._depth += 1
        lines.append(self._pad(f'<ruleml:Rel iri=":{escape(self._slug(rel))}"/>'))
        for arg in args:
            lines.append(self._pad(f"<ruleml:Ind>{escape(str(arg))}</ruleml:Ind>"))
        self._depth -= 1
        lines.append(self._pad("</ruleml:Atom>"))
        return lines

    def _exception_atom(self, statute: nodes.StatuteNode, exc: nodes.ExceptionNode) -> List[str]:
        return self._exception_atom_for_key(self._statute_key(statute), exc)

    def _exception_atom_for_key(self, base_key: str, exc: nodes.ExceptionNode) -> List[str]:
        args = [self._expr_text(exc.condition)]
        if exc.effect:
            args.append(self._expr_text(exc.effect))
        if exc.guard:
            args.append(f"guard:{self._expr_text(exc.guard)}")
        if exc.priority is not None:
            args.append(f"priority:{exc.priority}")
        rel = f"exception_{base_key}_{self._slug(exc.label or 'unlabeled')}"
        return self._atom(f"atom_{rel}", rel, args)

    def _negated_offence(self, statute: nodes.StatuteNode) -> List[str]:
        lines = [self._pad("<ruleml:Neg>")]
        self._depth += 1
        lines.extend(
            self._atom(
                f"atom_not_offence_{self._statute_key(statute)}",
                f"offence_{self._statute_key(statute)}",
                [self._title(statute)],
            )
        )
        self._depth -= 1
        lines.append(self._pad("</ruleml:Neg>"))
        return lines

    def _exception_target_key(self, statute: nodes.StatuteNode, exc: nodes.ExceptionNode) -> str:
        if exc.defeats:
            for other in statute.exceptions:
                if other.label == exc.defeats:
                    return self._exception_key(statute, other)
            return self._slug(exc.defeats)
        return self._statute_key(statute)

    def _penalty_text(self, penalty: nodes.PenaltyNode) -> str:
        bits: List[str] = []
        if penalty.imprisonment_min or penalty.imprisonment_max:
            bits.append(
                f"imprisonment {self._duration(penalty.imprisonment_min)}.."
                f"{self._duration(penalty.imprisonment_max)}"
            )
        if penalty.fine_unlimited:
            bits.append("fine unlimited")
        elif penalty.fine_min or penalty.fine_max:
            bits.append(f"fine {self._money(penalty.fine_min)}..{self._money(penalty.fine_max)}")
        if penalty.caning_unspecified:
            bits.append("caning unspecified")
        elif penalty.caning_min is not None or penalty.caning_max is not None:
            bits.append(f"caning {penalty.caning_min or 0}..{penalty.caning_max or ''}")
        if penalty.death_penalty:
            bits.append("death")
        if penalty.supplementary:
            bits.append(self._expr_text(penalty.supplementary))
        if penalty.sentencing:
            bits.append(f"sentencing {penalty.sentencing}")
        if penalty.combinator:
            bits.append(f"combinator {penalty.combinator}")
        if penalty.condition:
            bits.append(f"condition {penalty.condition}")
        if penalty.nested:
            bits.append(f"nested {self._penalty_text(penalty.nested)}")
        return "; ".join(bits) if bits else "penalty"

    def _duration(self, duration: Optional[nodes.DurationNode]) -> str:
        if duration is None:
            return ""
        parts = []
        for attr in ("years", "months", "days", "hours", "minutes", "seconds"):
            value = getattr(duration, attr)
            if value:
                parts.append(f"{value} {attr}")
        return " ".join(parts) if parts else "0 seconds"

    def _money(self, money: Optional[nodes.MoneyNode]) -> str:
        if money is None:
            return ""
        return f"{money.currency.name} {self._decimal(money.amount)}"

    @staticmethod
    def _decimal(value: Decimal) -> str:
        return format(value.normalize(), "f")

    def _expr_text(self, node: object) -> str:
        if node is None:
            return ""
        if isinstance(node, nodes.StringLit):
            return node.value
        if isinstance(node, nodes.IntLit):
            return str(node.value)
        if isinstance(node, nodes.FloatLit):
            return str(node.value)
        if isinstance(node, nodes.BoolLit):
            return "true" if node.value else "false"
        if isinstance(node, nodes.IdentifierNode):
            return node.name
        if isinstance(node, nodes.FieldAccessNode):
            return f"{self._expr_text(node.base)}.{node.field_name}"
        if isinstance(node, nodes.FunctionCallNode):
            args = ", ".join(self._expr_text(arg) for arg in node.args)
            return f"{self._expr_text(node.callee)}({args})"
        if isinstance(node, nodes.BinaryExprNode):
            return f"{self._expr_text(node.left)} {node.operator} {self._expr_text(node.right)}"
        if isinstance(node, nodes.UnaryExprNode):
            return f"{node.operator}{self._expr_text(node.operand)}"
        if isinstance(node, nodes.DateNode):
            return node.value.isoformat()
        if isinstance(node, nodes.DurationNode):
            return self._duration(node)
        if isinstance(node, nodes.MoneyNode):
            return self._money(node)
        return type(node).__name__

    def _title(self, statute: nodes.StatuteNode) -> str:
        if statute.title:
            return statute.title.value
        return f"section {statute.section_number}"

    def _statute_key(self, statute: nodes.StatuteNode) -> str:
        return f"s_{self._slug(statute.section_number)}"

    def _subsection_key(self, statute: nodes.StatuteNode, sub: nodes.SubsectionNode) -> str:
        return f"{self._statute_key(statute)}_sub_{self._slug(sub.number)}"

    def _exception_key(self, statute: nodes.StatuteNode, exc: nodes.ExceptionNode) -> str:
        return f"{self._statute_key(statute)}_exc_{self._slug(exc.label or 'unlabeled')}"

    def _subsection_exception_key(
        self,
        statute: nodes.StatuteNode,
        sub: nodes.SubsectionNode,
        exc: nodes.ExceptionNode,
    ) -> str:
        return f"{self._subsection_key(statute, sub)}_exc_{self._slug(exc.label or 'unlabeled')}"

    def _subsection_exception_target_key(
        self,
        statute: nodes.StatuteNode,
        sub: nodes.SubsectionNode,
        exc: nodes.ExceptionNode,
    ) -> str:
        if exc.defeats:
            for other in sub.exceptions:
                if other.label == exc.defeats:
                    return self._subsection_exception_key(statute, sub, other)
            return self._slug(exc.defeats)
        return self._subsection_key(statute, sub)

    def _iter_subsections(
        self,
        subsections: Sequence[nodes.SubsectionNode],
    ) -> Iterable[nodes.SubsectionNode]:
        for sub in subsections:
            yield sub
            yield from self._iter_subsections(sub.subsections)

    @staticmethod
    def _slug(value: str) -> str:
        out = "".join(ch if ch.isalnum() else "_" for ch in str(value)).strip("_")
        if not out:
            return "x"
        if out[0].isdigit():
            return f"x_{out}"
        return out

    def _pad(self, line: str) -> str:
        return " " * (self.indent * self._depth) + line
