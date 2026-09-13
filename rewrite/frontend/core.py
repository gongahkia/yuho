"""Source-aware YuhoSurface-v0.1 frontend and section 84 compatibility lowering."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import importlib.util
import json
from pathlib import Path
from pathlib import PurePosixPath
import re
import stat
import sys
import tempfile


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PILOT = ROOT / "research/singapore/section-84-pilot"
PROTOTYPE = PILOT / "prototype"
MAX_SOURCE_BYTES = 65536
MAX_TOKENS = 4096
MAX_NODES = 256
WORD = re.compile(r"[A-Za-z0-9_:./-]+")
PUNCTUATION = "{}(),;="
DEFERRED = {"exception", "presumption", "penalty", "sentence", "outcome", "evidence"}


def _pilot():
    spec = importlib.util.spec_from_file_location(
        "s84_surface_pilot", PROTOTYPE / "pilot.py"
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("the locked prototype helper is unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@dataclass(frozen=True)
class Token:
    kind: str
    text: str
    line: int
    column: int


class FrontendError(Exception):
    def __init__(self, code: str, path: str, token: Token, message: str):
        self.code, self.path, self.token, self.message = code, path, token, message
        super().__init__(f"{path}:{token.line}:{token.column}: {code}: {message}")

    def diagnostic(self) -> dict[str, object]:
        return {
            "code": self.code,
            "path": self.path,
            "line": self.token.line,
            "column": self.token.column,
            "message": self.message,
        }


def lex(source: str, path: str) -> tuple[Token, ...]:
    tokens: list[Token] = []
    index, line, column = 0, 1, 1
    while index < len(source):
        char = source[index]
        if char in " \t\n":
            if char == "\n":
                line, column = line + 1, 1
            else:
                column += len(char.encode("utf-8"))
            index += 1
            continue
        if char == "\r" or char == "\x00":
            raise FrontendError(
                "SFE001",
                path,
                Token("error", char, line, column),
                "only LF UTF-8 source without NUL is supported",
            )
        if source.startswith("//", index):
            end = source.find("\n", index)
            if end == -1:
                end = len(source)
            if "\r" in source[index:end] or "\x00" in source[index:end]:
                raise FrontendError(
                    "SFE001",
                    path,
                    Token("error", "", line, column),
                    "only LF UTF-8 source without NUL is supported",
                )
            if end == len(source):
                break
            column += len(source[index:end].encode("utf-8"))
            index = end
            continue
        start_line, start_column = line, column
        if char in PUNCTUATION:
            tokens.append(Token(char, char, line, column))
            index, column = index + 1, column + 1
        elif char == '"':
            end = source.find('"', index + 1)
            if end == -1 or "\n" in source[index:end]:
                raise FrontendError(
                    "SFE001",
                    path,
                    Token("error", char, line, column),
                    "unterminated string literal",
                )
            value = source[index + 1 : end]
            if "\\" in value:
                raise FrontendError(
                    "SFE013",
                    path,
                    Token("error", char, line, column),
                    "string escapes are outside this slice",
                )
            tokens.append(Token("string", value, start_line, start_column))
            column += len(source[index : end + 1].encode("utf-8"))
            index = end + 1
        else:
            match = WORD.match(source, index)
            if match is None:
                raise FrontendError(
                    "SFE001",
                    path,
                    Token("error", char, line, column),
                    f"invalid character {char!r}",
                )
            value = match.group()
            tokens.append(Token("word", value, start_line, start_column))
            column += len(value.encode("utf-8"))
            index = match.end()
        if len(tokens) > MAX_TOKENS:
            raise FrontendError("SFE016", path, tokens[-1], "token limit exceeded")
    tokens.append(Token("eof", "", line, column))
    return tuple(tokens)


@dataclass(frozen=True)
class Leaf:
    identifier: Token
    proposition: Token
    quote: Token
    support: Token | None


@dataclass(frozen=True)
class Group:
    identifier: Token
    combinator: Token
    members: tuple[Token, ...]


@dataclass(frozen=True)
class Assignment:
    identifier: Token
    status: Token
    reason: Token | None


@dataclass(frozen=True)
class Model:
    identifier: Token
    variant: Token
    jurisdiction: Token
    purpose: Token
    request_id: Token
    reference_date: Token
    max_nodes: Token
    root_rule: Token
    program: Token
    path: Token
    root_requirement: Token
    sources: tuple[tuple[Token, Token, Token], ...]
    mapping_source: Token
    quotes: tuple[tuple[Token, Token], ...]
    burden: tuple[Token, Token, Token, Token]
    propositions: tuple[Leaf | Group, ...]
    assignments: tuple[Assignment, ...]
    limitations: tuple[Token, ...]


@dataclass(frozen=True)
class SyntheticElement:
    category: Token
    identifier: Token
    quote: Token


@dataclass(frozen=True)
class SyntheticRule:
    kind: Token
    identifier: Token
    target: Token | None
    rule: Token
    program: Token
    path: Token
    elements: tuple[SyntheticElement, ...]
    groups: tuple[Group, ...]


@dataclass(frozen=True)
class SyntheticModel:
    identifier: Token
    variant: Token
    jurisdiction: Token
    purpose: Token
    request_id: Token
    reference_date: Token
    max_nodes: Token
    sources: tuple[tuple[Token, Token, Token], ...]
    quotes: tuple[tuple[Token, Token], ...]
    burden: tuple[Token, Token, Token, Token]
    offence: SyntheticRule
    exception: SyntheticRule
    outputs: tuple[tuple[Token, Token], ...]
    limitations: tuple[Token, ...]


@dataclass(frozen=True)
class Scenario:
    identifier: Token
    model: Token
    assignments: tuple[Assignment, ...]


class Parser:
    def __init__(self, tokens: tuple[Token, ...], path: str):
        self.tokens, self.path, self.index = tokens, path, 0

    def take(self, expected: str, code: str = "SFE001") -> Token:
        token = self.tokens[self.index]
        if token.text != expected and token.kind != expected:
            if token.text in DEFERRED:
                code = "SFE013"
            raise FrontendError(code, self.path, token, f"expected {expected}")
        self.index += 1
        return token

    def word(self) -> Token:
        return self.take("word")

    def statement(self, keyword: str) -> Token:
        return self.take(keyword)

    def assignments(self) -> tuple[Assignment, ...]:
        assignments: list[Assignment] = []
        while self.tokens[self.index].text != "}":
            identifier = self.word()
            self.take("=")
            status = self.word()
            reason = None
            if self.tokens[self.index].text == "(":
                self.take("(")
                reason = self.word()
                self.take(")")
            self.take(";")
            assignments.append(Assignment(identifier, status, reason))
            if len(assignments) > MAX_NODES:
                raise FrontendError(
                    "SFE016", self.path, identifier, "assignment limit exceeded"
                )
        return tuple(assignments)

    def synthetic_rule(self, kind: str, *, attached: bool = True) -> SyntheticRule:
        head = self.take(kind)
        identifier = self.word()
        target = None
        if kind == "exception" and attached:
            self.take("to")
            target = self.word()
        self.take("rule")
        rule = self.word()
        self.take("program")
        program = self.word()
        self.take("path")
        path = self.word()
        self.take("{")
        elements: list[SyntheticElement] = []
        groups: list[Group] = []
        while self.tokens[self.index].text != "}":
            token = self.word()
            if token.text == "element":
                category = self.word()
                item = self.word()
                self.take("quote")
                quote = self.word()
                elements.append(SyntheticElement(category, item, quote))
            elif token.text in {"all", "any"}:
                group = self.word()
                self.take("(")
                members = [self.word()]
                while self.tokens[self.index].text == ",":
                    self.take(",")
                    members.append(self.word())
                self.take(")")
                groups.append(Group(group, token, tuple(members)))
            else:
                raise FrontendError(
                    "SFE013", self.path, token, "unsupported rule declaration"
                )
            self.take(";")
            if len(elements) + len(groups) > MAX_NODES:
                raise FrontendError("SFE016", self.path, token, "node limit exceeded")
        self.take("}")
        return SyntheticRule(
            head,
            identifier,
            target,
            rule,
            program,
            path,
            tuple(elements),
            tuple(groups),
        )

    def synthetic(self) -> SyntheticModel:
        self.take("model")
        identifier = self.word()
        self.take("{")
        self.take("variant")
        variant = self.word()
        self.take(";")
        self.take("jurisdiction")
        jurisdiction = self.word()
        self.take(";")
        self.take("purpose")
        purpose = self.word()
        self.take(";")
        self.take("request")
        request_id = self.word()
        self.take(";")
        self.take("policy")
        reference_date, max_nodes = self.word(), self.word()
        self.take(";")
        self.take("provenance")
        self.take("{")
        sources: list[tuple[Token, Token, Token]] = []
        quotes: list[tuple[Token, Token]] = []
        while self.tokens[self.index].text != "}":
            head = self.word()
            if head.text == "source":
                sources.append((self.word(), self.word(), self.take("string")))
            elif head.text == "quote":
                quotes.append((self.word(), self.take("string")))
            else:
                raise FrontendError("SFE013", self.path, head, "unsupported provenance")
            self.take(";")
        self.take("}")
        self.take("annotations")
        self.take("{")
        self.take("burden")
        burden = (self.word(), self.word(), self.word(), self.word())
        self.take(";")
        self.take("}")
        offence = self.synthetic_rule("offence")
        if self.tokens[self.index].text == "offence":
            raise FrontendError(
                "SFE002", self.path, self.tokens[self.index], "duplicate offence"
            )
        exception = self.synthetic_rule("exception")
        if self.tokens[self.index].text == "exception":
            raise FrontendError(
                "SFE002", self.path, self.tokens[self.index], "duplicate exception"
            )
        self.take("outputs")
        self.take("{")
        outputs: list[tuple[Token, Token]] = []
        while self.tokens[self.index].text != "}":
            label, target = self.word(), self.word()
            self.take(";")
            outputs.append((label, target))
        self.take("}")
        self.take("limitations")
        self.take("{")
        limitations: list[Token] = []
        while self.tokens[self.index].text != "}":
            limitations.append(self.take("string"))
            self.take(";")
        self.take("}")
        self.take("}")
        if self.tokens[self.index].text == "model":
            raise FrontendError(
                "SFE002", self.path, self.tokens[self.index], "duplicate model"
            )
        self.take("eof")
        return SyntheticModel(
            identifier,
            variant,
            jurisdiction,
            purpose,
            request_id,
            reference_date,
            max_nodes,
            tuple(sources),
            tuple(quotes),
            burden,
            offence,
            exception,
            tuple(outputs),
            tuple(limitations),
        )

    def scenario(self) -> Scenario:
        self.take("scenario")
        identifier = self.word()
        self.take("for")
        model = self.word()
        self.take("{")
        assignments = self.assignments()
        self.take("}")
        self.take("eof")
        return Scenario(identifier, model, assignments)

    def parse(self) -> Model:
        self.take("model")
        identifier = self.word()
        self.take("{")
        self.take("variant")
        variant = self.word()
        self.take(";")
        self.take("jurisdiction")
        jurisdiction = self.word()
        self.take(";")
        self.take("purpose")
        purpose = self.word()
        self.take(";")
        self.take("request")
        request_id = self.word()
        self.take(";")
        self.take("policy")
        reference_date, max_nodes = self.word(), self.word()
        self.take(";")
        self.take("root", "SFE007")
        root_rule = self.word()
        self.take("program")
        program = self.word()
        self.take("path")
        path = self.word()
        self.take("requires")
        root_requirement = self.word()
        self.take(";")

        self.take("provenance")
        self.take("{")
        sources: list[tuple[Token, Token, Token]] = []
        quotes: list[tuple[Token, Token]] = []
        mapping_source: Token | None = None
        while self.tokens[self.index].text != "}":
            head = self.word()
            if head.text == "source":
                sources.append((self.word(), self.word(), self.take("string")))
            elif head.text == "mapping_source":
                if mapping_source is not None:
                    raise FrontendError(
                        "SFE002", self.path, head, "duplicate mapping source"
                    )
                mapping_source = self.word()
            elif head.text == "quote":
                quotes.append((self.word(), self.take("string")))
            else:
                raise FrontendError(
                    "SFE013", self.path, head, "unsupported provenance declaration"
                )
            self.take(";")
        self.take("}")

        self.take("annotations")
        self.take("{")
        self.take("burden")
        burden = (self.word(), self.word(), self.word(), self.word())
        self.take(";")
        self.take("}")

        self.take("propositions")
        self.take("{")
        propositions: list[Leaf | Group] = []
        while self.tokens[self.index].text != "}":
            head = self.word()
            if head.text == "leaf":
                leaf_id = self.word()
                self.take("proposition")
                proposition = self.word()
                self.take("quote")
                quote = self.word()
                support = None
                if self.tokens[self.index].text == "support":
                    self.take("support")
                    support = self.word()
                propositions.append(Leaf(leaf_id, proposition, quote, support))
            elif head.text in {"all", "any"}:
                group_id = self.word()
                self.take("(")
                members = [self.word()]
                while self.tokens[self.index].text == ",":
                    self.take(",")
                    members.append(self.word())
                self.take(")")
                propositions.append(Group(group_id, head, tuple(members)))
            else:
                code = "SFE013" if head.text in DEFERRED else "SFE005"
                raise FrontendError(
                    code, self.path, head, "unsupported proposition constructor"
                )
            self.take(";")
            if len(propositions) > MAX_NODES:
                raise FrontendError("SFE016", self.path, head, "node limit exceeded")
        self.take("}")

        self.take("proof_assignments")
        self.take("{")
        assignments = self.assignments()
        self.take("}")

        self.take("limitations")
        self.take("{")
        limitations: list[Token] = []
        while self.tokens[self.index].text != "}":
            limitations.append(self.take("string"))
            self.take(";")
        self.take("}")
        self.take("}")
        self.take("eof")
        if mapping_source is None:
            raise FrontendError(
                "SFE014", self.path, identifier, "mapping source is required"
            )
        return Model(
            identifier,
            variant,
            jurisdiction,
            purpose,
            request_id,
            reference_date,
            max_nodes,
            root_rule,
            program,
            path,
            root_requirement,
            tuple(sources),
            mapping_source,
            tuple(quotes),
            burden,
            tuple(propositions),
            assignments,
            tuple(limitations),
        )


def parse_text(source: str, path: str = "<memory>") -> Model:
    if len(source.encode("utf-8")) > MAX_SOURCE_BYTES:
        raise FrontendError(
            "SFE016", path, Token("error", "", 1, 1), "source byte limit exceeded"
        )
    return Parser(lex(source, path), path).parse()


def check(
    model: Model, path: str
) -> tuple[dict[str, Leaf | Group], dict[str, Assignment]]:
    def fail(code: str, token: Token, message: str):
        raise FrontendError(code, path, token, message)

    for token, expected in (
        (model.identifier, "SingaporePenalCodeSection84Post2022ResearchPrototype-v1"),
        (model.variant, "SuppliedProofStatus-v1"),
        (model.jurisdiction, "Singapore"),
        (model.purpose, "research_prototype"),
        (model.reference_date, "2026-09-13"),
        (model.max_nodes, "1024"),
    ):
        if token.text != expected:
            fail("SFE004", token, "unsupported model, variant, scope or policy")
    if not re.fullmatch(r"[A-Z][0-9]{2}", model.request_id.text):
        fail("SFE004", model.request_id, "unsupported request ID")
    if (
        model.root_rule.text != "r:section84"
        or model.program.text != "p:section84"
        or model.path.text != "section84"
    ):
        fail("SFE007", model.root_rule, "unsupported or missing root declaration")
    for token, expected in zip(
        model.burden,
        ("section107", "defence", "legal", "balance_of_probabilities"),
        strict=True,
    ):
        if token.text != expected:
            fail("SFE011", token, "invalid contextual burden or standard")
    if len(model.limitations) < 2 or not all(t.text for t in model.limitations):
        fail("SFE004", model.identifier, "research limitations are required")

    declarations: dict[str, Leaf | Group] = {}
    for item in model.propositions:
        token = item.identifier
        if token.text in declarations or token.text in {
            model.root_rule.text,
            model.program.text,
        }:
            fail("SFE002", token, "duplicate semantic identifier")
        if isinstance(item, Leaf):
            if not token.text.startswith("f:") or not re.fullmatch(
                r"P84-[0-9]{2}", item.proposition.text
            ):
                fail("SFE005", token, "invalid leaf or proposition type")
        else:
            if not token.text.startswith("g:") or len(item.members) < 2:
                fail("SFE006", token, "invalid combinator or operands")
        declarations[token.text] = item
    if model.root_requirement.text not in declarations:
        fail("SFE007", model.root_requirement, "root proposition is missing")
    if not isinstance(declarations[model.root_requirement.text], Group):
        fail("SFE006", model.root_requirement, "root must be a group")
    usage: dict[str, int] = {key: 0 for key in declarations}
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(identifier: str):
        item = declarations[identifier]
        if identifier in visiting:
            fail("SFE008", item.identifier, "cyclic proposition reference")
        if identifier in visited:
            return
        visiting.add(identifier)
        if isinstance(item, Group):
            for member in item.members:
                if member.text.startswith("ann:") or member.text == "section107":
                    fail("SFE012", member, "contextual annotation is not executable")
                target = declarations.get(member.text)
                if target is None:
                    code = (
                        "SFE006"
                        if not member.text.startswith(("f:", "g:"))
                        else "SFE003"
                    )
                    fail(code, member, "unknown or invalid combinator operand")
                usage[member.text] += 1
                visit(member.text)
        visiting.remove(identifier)
        visited.add(identifier)

    visit(model.root_requirement.text)
    if set(declarations) != visited or any(count > 1 for count in usage.values()):
        fail(
            "SFE006",
            model.root_requirement,
            "every declaration must have exactly one source-ordered tree position",
        )

    assignments: dict[str, Assignment] = {}
    for item in model.assignments:
        identifier = item.identifier.text
        if identifier in assignments:
            fail("SFE002", item.identifier, "duplicate proof assignment")
        assignments[identifier] = item
        if item.status.text not in {"proved", "not_proved", "unresolved"}:
            fail("SFE010", item.status, "invalid supplied proof status")
        if item.status.text == "unresolved":
            if item.reason is None or item.reason.text not in {
                "not_determined",
                "external_decision_pending",
            }:
                fail("SFE010", item.status, "invalid unresolved reason")
        elif item.reason is not None:
            fail("SFE010", item.reason, "resolved status cannot have a reason")
    leaves = {key for key, item in declarations.items() if isinstance(item, Leaf)}
    if leaves != set(assignments):
        extra = set(assignments) - leaves
        token = (
            assignments[sorted(extra)[0]].identifier
            if extra
            else model.root_requirement
        )
        fail("SFE009", token, "missing or unexpected proof assignment")
    return declarations, assignments


def lower(model: Model, input_dir: Path, packet_dir: Path, path: str) -> bytes:
    pilot = _pilot()
    declarations, assignments = check(model, path)
    sources = {
        token.text: (kind.text, location.text)
        for token, kind, location in model.sources
    }
    if (
        len(sources) != len(model.sources)
        or sources
        != {
            "src:pc84-excerpt": ("excerpt", "research/section84/excerpt.txt"),
            "src:synthetic-status": (
                "synthetic_status",
                "research/section84/synthetic-status.txt",
            ),
        }
        or model.mapping_source.text != "src:pc84-extracted"
    ):
        raise FrontendError(
            "SFE014",
            path,
            model.mapping_source,
            "unsupported source or mapping declaration",
        )
    quote_by_id = {identifier.text: value.text for identifier, value in model.quotes}
    if len(quote_by_id) != len(model.quotes):
        raise FrontendError("SFE002", path, model.identifier, "duplicate quote ID")
    html, extracted = pilot.locked_inputs(input_dir, packet_dir)
    del html  # only the locked extraction contributes executable source spans
    text = ("\n".join(value.text for _, value in model.quotes) + "\n").encode("utf-8")
    if text != pilot.excerpt(extracted)[0]:
        raise FrontendError(
            "SFE014",
            path,
            model.identifier,
            "quote bytes or order differ from the locked excerpt",
        )
    quote_spans = {}
    for identifier, value in model.quotes:
        encoded = value.text.encode("utf-8")
        start = text.index(encoded)
        quote_spans[identifier.text] = pilot.span(text, start, start + len(encoded))
    for item in declarations.values():
        if isinstance(item, Leaf):
            for quote in (item.quote, item.support):
                if quote is not None and quote.text not in quote_spans:
                    raise FrontendError("SFE003", path, quote, "unknown source quote")
    mapping = json.loads((PROTOTYPE / "mapping.json").read_bytes())
    mapped = {row["semantic_id"]: row for row in mapping["leaf_mappings"]}
    for key, item in declarations.items():
        if isinstance(item, Leaf):
            row = mapped.get(key)
            if (
                row is None
                or row["proposition_id"] != item.proposition.text
                or (row["source_id"] != model.mapping_source.text)
            ):
                raise FrontendError(
                    "SFE014",
                    path,
                    item.identifier,
                    "proposition mapping differs from reviewed mapping",
                )
            expected_spans = []
            for quote in (item.quote, item.support):
                if quote is None:
                    continue
                needle = quote_by_id[quote.text].encode("utf-8")
                start = extracted.index(needle)
                expected_spans.append(pilot.span(extracted, start, start + len(needle)))
            expected_spans.sort(key=lambda span: span["start"])
            if expected_spans != row["supporting_spans"]:
                raise FrontendError(
                    "SFE014",
                    path,
                    item.quote,
                    "quote support spans differ from reviewed mapping",
                )
    if set(mapped) != {
        key for key, item in declarations.items() if isinstance(item, Leaf)
    }:
        raise FrontendError(
            "SFE014",
            path,
            model.identifier,
            "reviewed mapping and source leaves differ",
        )
    if {row["semantic_id"] for row in mapping["group_mappings"]} != {
        key for key, item in declarations.items() if isinstance(item, Group)
    } | {model.root_rule.text, model.program.text}:
        raise FrontendError(
            "SFE014",
            path,
            model.root_requirement,
            "reviewed mapping and source groups differ",
        )

    burden = {"holder": model.burden[1].text, "kind": model.burden[2].text}
    standard = model.burden[3].text
    whole_span = pilot.span(text, 0, len(text))

    def requirement(identifier: str) -> dict:
        item = declarations[identifier]
        if isinstance(item, Leaf):
            return {
                "id": identifier,
                "kind": "leaf",
                "path": [model.path.text],
                "span": quote_spans[item.quote.text],
                "declared_metadata": {
                    "burden": burden.copy(),
                    "standard_of_proof": standard,
                },
            }
        return {
            "id": identifier,
            "kind": item.combinator.text,
            "path": [model.path.text],
            "span": whole_span,
            "members": [requirement(member.text) for member in item.members],
        }

    status_bytes = pilot.STATUS_TEXT.encode("utf-8")
    facts = {}
    for identifier, assignment in assignments.items():
        proof_status = {"kind": assignment.status.text}
        if assignment.reason is not None:
            proof_status["reason"] = assignment.reason.text
        facts[identifier] = {
            "proof_status": proof_status,
            "burden": burden.copy(),
            "standard_of_proof": standard,
            "status_source": {
                "assignment_id": "assignment:" + identifier.removeprefix("f:"),
                "issuer_label": "synthetic research fixture",
                "origin": "synthetic_fixture",
                "source_id": "src:synthetic-status",
                "span": pilot.span(status_bytes, 0, len(status_bytes)),
            },
        }
    request = {
        "protocol": "yuho.kernel-protocol/v1",
        "request_id": model.request_id.text,
        "operation": "evaluate",
        "input_schema": "yuho.kernel-input/v1",
        "fragment": model.variant.text,
        "root_rule": model.root_rule.text,
        "policy": {
            "max_nodes": int(model.max_nodes.text),
            "reference_date": model.reference_date.text,
        },
        "sources": [
            {
                "id": "src:pc84-excerpt",
                "path": sources["src:pc84-excerpt"][1],
                "text": text.decode("utf-8"),
                "sha256": pilot.sha(text),
            },
            {
                "id": "src:synthetic-status",
                "path": sources["src:synthetic-status"][1],
                "text": pilot.STATUS_TEXT,
                "sha256": pilot.sha(status_bytes),
            },
        ],
        "registry": [
            {
                "id": model.root_rule.text,
                "source_id": "src:pc84-excerpt",
                "program": {
                    "id": model.program.text,
                    "path": [model.path.text],
                    "span": whole_span,
                    "definitions": False,
                    "requirements": [requirement(model.root_requirement.text)],
                    "children": [],
                    "penalties": [],
                },
                "exceptions": [],
            }
        ],
        "facts": facts,
    }
    return pilot.canonical(request)


def compile_text(source: str, path: str, input_dir: Path, packet_dir: Path) -> bytes:
    return lower(parse_text(source, path), input_dir, packet_dir, path)


def _regular_source(path: Path) -> str:
    if not stat.S_ISREG(path.lstat().st_mode):
        raise FrontendError(
            "SFE015",
            str(path),
            Token("error", "", 1, 1),
            "source must be a regular file, not a symlink",
        )
    if path.stat().st_size > MAX_SOURCE_BYTES:
        raise FrontendError(
            "SFE016", str(path), Token("error", "", 1, 1), "source byte limit exceeded"
        )
    try:
        return path.read_bytes().decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise FrontendError(
            "SFE001", str(path), Token("error", "", 1, 1), "source is not strict UTF-8"
        ) from error


def _safe_output(path: Path) -> None:
    if ".." in path.parts or path.exists() or path.is_symlink():
        raise FrontendError(
            "SFE015",
            str(path),
            Token("error", "", 1, 1),
            "output path is unsafe or already exists",
        )
    parent = path.parent
    if not parent.is_dir():
        raise FrontendError(
            "SFE015", str(path), Token("error", "", 1, 1), "output parent must exist"
        )
    for candidate in (parent, *parent.parents):
        if candidate.is_symlink():
            raise FrontendError(
                "SFE015",
                str(path),
                Token("error", "", 1, 1),
                "symlinked output parent is unsupported",
            )


def compile_file(
    source: Path, output: Path, input_dir: Path, packet_dir: Path
) -> bytes:
    text = _regular_source(source)
    _safe_output(output)
    result = compile_text(text, str(source), input_dir, packet_dir)
    pilot = _pilot()
    with tempfile.TemporaryDirectory(
        prefix=".yuho-surface-", dir=output.parent
    ) as temp:
        temporary = Path(temp) / "request.json"
        temporary.write_bytes(result)
        pilot.rename_without_replace(temporary, output)
    return result


LANGUAGE_VERSION = "yuho.surface/v0.1"
SYNTHETIC_STATUS_TEXT = "synthetic proof classifications only\n"


def canonical(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def span(data: bytes, start: int, end: int) -> dict[str, int]:
    if not 0 <= start <= end <= len(data):
        raise ValueError("invalid source span")

    def position(offset: int) -> tuple[int, int]:
        before = data[:offset]
        return before.count(b"\n") + 1, len(before.rsplit(b"\n", 1)[-1]) + 1

    first_line, first_col = position(start)
    last_line, last_col = position(end)
    return {
        "start": start,
        "end": end,
        "start_line": first_line,
        "start_col": first_col,
        "end_line": last_line,
        "end_col": last_col,
    }


def parse_synthetic(source: str, path: str = "<memory>") -> SyntheticModel:
    if len(source.encode("utf-8")) > MAX_SOURCE_BYTES:
        raise FrontendError(
            "SFE016", path, Token("error", "", 1, 1), "source byte limit exceeded"
        )
    return Parser(lex(source, path), path).synthetic()


def parse_scenario(source: str, path: str = "<memory>") -> Scenario:
    if len(source.encode("utf-8")) > MAX_SOURCE_BYTES:
        raise FrontendError(
            "SFE016", path, Token("error", "", 1, 1), "source byte limit exceeded"
        )
    return Parser(lex(source, path), path).scenario()


def check_synthetic(model: SyntheticModel, path: str) -> dict[str, object]:
    def fail(code: str, token: Token, message: str):
        raise FrontendError(code, path, token, message)

    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9-]*-v0\.[12]", model.identifier.text):
        fail("SFE004", model.identifier, "invalid bounded YuhoSurface model ID")
    if model.variant.text != "SuppliedProofStatus-v1":
        fail("SFE004", model.variant, "this subset requires SuppliedProofStatus-v1")
    if (
        model.jurisdiction.text != "Fictional"
        or model.purpose.text != "compiler_fixture"
    ):
        fail(
            "SFE021", model.jurisdiction, "this subset accepts fictional fixtures only"
        )
    if not re.fullmatch(r"[A-Z][0-9]{2}", model.request_id.text):
        fail("SFE004", model.request_id, "invalid request ID")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", model.reference_date.text):
        fail("SFE004", model.reference_date, "invalid policy date")
    if model.max_nodes.text != "1024":
        fail("SFE004", model.max_nodes, "unsupported node policy")
    if tuple(token.text for token in model.burden[1:]) != (
        "none",
        "none",
        "not_applicable",
    ) or model.burden[0].text not in {"none", "synthetic_context"}:
        fail("SFE011", model.burden[0], "invalid contextual annotation")
    if len(model.limitations) < 2 or any(not item.text for item in model.limitations):
        fail("SFE004", model.identifier, "synthetic limitations required")

    source_ids: set[str] = set()
    source_by_kind: dict[str, tuple[str, str]] = {}
    for identifier, kind, location in model.sources:
        if identifier.text in source_ids or kind.text in source_by_kind:
            fail("SFE002", identifier, "duplicate source identifier or role")
        if kind.text not in {"source_text", "synthetic_status"}:
            fail("SFE014", kind, "unsupported source role")
        place = PurePosixPath(location.text)
        if place.is_absolute() or ".." in place.parts or not location.text:
            fail("SFE015", location, "unsafe source locator")
        if not location.text.startswith("fictional/"):
            fail("SFE021", location, "synthetic fixture cannot claim another source")
        source_ids.add(identifier.text)
        source_by_kind[kind.text] = identifier.text, location.text
    if set(source_by_kind) != {"source_text", "synthetic_status"}:
        fail("SFE014", model.identifier, "source text and status source required")

    quote_map: dict[str, str] = {}
    for identifier, value in model.quotes:
        if identifier.text in quote_map:
            fail("SFE002", identifier, "duplicate quote ID")
        if not identifier.text.startswith("q:") or not value.text:
            fail("SFE014", identifier, "invalid source quote")
        quote_map[identifier.text] = value.text
    if len(quote_map) < 5:
        fail("SFE014", model.identifier, "source support is incomplete")

    offence, exception = model.offence, model.exception
    if not offence.identifier.text.startswith(
        "o:"
    ) or not exception.identifier.text.startswith("x:"):
        fail("SFE017", offence.identifier, "invalid offence or exception ID")
    if exception.target is None or exception.target.text != offence.identifier.text:
        fail(
            "SFE018",
            exception.target or exception.identifier,
            "unknown exception target",
        )
    if not offence.rule.text.startswith("r:") or not exception.rule.text.startswith(
        "r:"
    ):
        fail("SFE017", offence.rule, "invalid rule ID")
    if not offence.program.text.startswith(
        "p:"
    ) or not exception.program.text.startswith("p:"):
        fail("SFE017", offence.program, "invalid program ID")
    identities: set[str] = set()
    for token in (
        offence.identifier,
        exception.identifier,
        offence.rule,
        exception.rule,
        offence.program,
        exception.program,
    ):
        if token.text in identities:
            fail("SFE002", token, "duplicate declaration ID")
        identities.add(token.text)

    rules: dict[str, tuple[dict[str, SyntheticElement | Group], Group]] = {}
    for rule, allowed, required in (
        (
            offence,
            {"conduct", "circumstance", "fault"},
            {"conduct", "circumstance", "fault"},
        ),
        (exception, {"circumstance", "purpose"}, {"circumstance", "purpose"}),
    ):
        declarations: dict[str, SyntheticElement | Group] = {}
        categories: set[str] = set()
        for item in (*rule.elements, *rule.groups):
            token = item.identifier
            if token.text in identities:
                fail("SFE002", token, "duplicate semantic ID")
            identities.add(token.text)
            declarations[token.text] = item
            if isinstance(item, SyntheticElement):
                if not token.text.startswith("f:") or item.category.text not in allowed:
                    fail("SFE017", item.category, "invalid element category or ID")
                if item.category.text in categories:
                    fail("SFE017", item.category, "duplicate typed element category")
                categories.add(item.category.text)
                if item.quote.text not in quote_map:
                    fail("SFE003", item.quote, "unknown support quote")
            elif not token.text.startswith("g:") or len(item.members) < 2:
                fail("SFE006", token, "invalid combinator or operands")
        if categories != required:
            fail("SFE017", rule.identifier, "required typed elements missing")
        if not rule.groups:
            fail("SFE007", rule.identifier, "root proposition missing")
        root = rule.groups[-1]
        visiting: set[str] = set()
        visited: set[str] = set()
        uses = {key: 0 for key in declarations}

        def visit(key: str) -> None:
            item = declarations[key]
            if key in visiting:
                fail("SFE008", item.identifier, "cyclic proposition reference")
            if key in visited:
                return
            visiting.add(key)
            if isinstance(item, Group):
                for member in item.members:
                    if (
                        member.text.startswith("ann:")
                        or member.text == model.burden[0].text
                    ):
                        fail(
                            "SFE012", member, "contextual annotation is not executable"
                        )
                    if member.text not in declarations:
                        all_declared = {
                            item.identifier.text
                            for candidate in (offence, exception)
                            for item in (*candidate.elements, *candidate.groups)
                        }
                        code = (
                            "SFE019"
                            if member.text in identities | all_declared
                            else "SFE003"
                        )
                        fail(code, member, "unknown or type-incompatible reference")
                    uses[member.text] += 1
                    visit(member.text)
            visiting.remove(key)
            visited.add(key)

        visit(root.identifier.text)
        if set(declarations) != visited or any(count > 1 for count in uses.values()):
            fail(
                "SFE006",
                root.identifier,
                "declarations must form one source-ordered tree",
            )
        rules[rule.kind.text] = declarations, root

    outputs = {label.text: target for label, target in model.outputs}
    expected = {
        "offence_requirements": rules["offence"][1].identifier.text,
        "exception_applicable": rules["exception"][1].identifier.text,
        "defeated_branch": offence.program.text,
        "final_rule": offence.rule.text,
    }
    if len(outputs) != len(model.outputs) or set(outputs) != set(expected):
        fail("SFE020", model.identifier, "invalid output declarations")
    for key, value in expected.items():
        if outputs[key].text != value:
            fail("SFE020", outputs[key], "output has wrong target type")
    return {"sources": source_by_kind, "quotes": quote_map, "rules": rules}


def check_scenario(
    scenario: Scenario, model: SyntheticModel, path: str
) -> dict[str, Assignment]:
    if scenario.model.text != model.identifier.text:
        raise FrontendError("SFE004", path, scenario.model, "scenario model mismatch")
    if scenario.identifier.text != model.request_id.text:
        raise FrontendError(
            "SFE004", path, scenario.identifier, "scenario request mismatch"
        )
    leaves = {
        item.identifier.text
        for rule in (model.offence, model.exception)
        for item in rule.elements
    }
    assignments: dict[str, Assignment] = {}
    for item in scenario.assignments:
        key = item.identifier.text
        if key in assignments:
            raise FrontendError(
                "SFE002", path, item.identifier, "duplicate proof assignment"
            )
        if key not in leaves:
            raise FrontendError(
                "SFE009", path, item.identifier, "unexpected proof assignment"
            )
        if item.status.text not in {"proved", "not_proved", "unresolved"}:
            raise FrontendError("SFE010", path, item.status, "invalid proof status")
        if item.status.text == "unresolved":
            if item.reason is None or item.reason.text not in {
                "not_determined",
                "external_decision_pending",
            }:
                raise FrontendError(
                    "SFE010", path, item.status, "invalid unresolved reason"
                )
        elif item.reason is not None:
            raise FrontendError(
                "SFE010", path, item.reason, "resolved status has reason"
            )
        assignments[key] = item
    if leaves != set(assignments):
        raise FrontendError(
            "SFE009", path, scenario.identifier, "missing proof assignment"
        )
    return assignments


def lower_synthetic(
    model: SyntheticModel, scenario: Scenario, model_path: str, scenario_path: str
) -> bytes:
    checked = check_synthetic(model, model_path)
    assignments = check_scenario(scenario, model, scenario_path)
    sources = checked["sources"]
    source_id, source_path = sources["source_text"]
    status_id, status_path = sources["synthetic_status"]
    text = ("\n".join(value.text for _, value in model.quotes) + "\n").encode("utf-8")
    positions: dict[str, dict[str, int]] = {}
    offset = 0
    for identifier, value in model.quotes:
        length = len(value.text.encode("utf-8"))
        positions[identifier.text] = span(text, offset, offset + length)
        offset += length + 1
    whole = span(text, 0, len(text))
    status_bytes = SYNTHETIC_STATUS_TEXT.encode("utf-8")

    def program(rule: SyntheticRule) -> dict:
        declarations, root = checked["rules"][rule.kind.text]

        def requirement(key: str) -> dict:
            item = declarations[key]
            if isinstance(item, SyntheticElement):
                return {
                    "id": key,
                    "kind": "leaf",
                    "path": [rule.path.text],
                    "span": positions[item.quote.text],
                }
            return {
                "id": key,
                "kind": item.combinator.text,
                "path": [rule.path.text],
                "span": whole,
                "members": [requirement(member.text) for member in item.members],
            }

        return {
            "id": rule.program.text,
            "path": [rule.path.text],
            "span": whole,
            "definitions": False,
            "requirements": [requirement(root.identifier.text)],
            "children": [],
            "penalties": [],
        }

    facts = {}
    for key, item in assignments.items():
        proof = {"kind": item.status.text}
        if item.reason is not None:
            proof["reason"] = item.reason.text
        facts[key] = {
            "proof_status": proof,
            "status_source": {
                "assignment_id": "assignment:" + key.removeprefix("f:"),
                "issuer_label": "fictional compiler fixture",
                "origin": "synthetic_fixture",
                "source_id": status_id,
                "span": span(status_bytes, 0, len(status_bytes)),
            },
        }
    offence, exception = model.offence, model.exception
    request = {
        "protocol": "yuho.kernel-protocol/v1",
        "request_id": model.request_id.text,
        "operation": "evaluate",
        "input_schema": "yuho.kernel-input/v1",
        "fragment": model.variant.text,
        "root_rule": offence.rule.text,
        "policy": {
            "max_nodes": int(model.max_nodes.text),
            "reference_date": model.reference_date.text,
        },
        "sources": [
            {
                "id": source_id,
                "path": source_path,
                "text": text.decode("utf-8"),
                "sha256": sha(text),
            },
            {
                "id": status_id,
                "path": status_path,
                "text": SYNTHETIC_STATUS_TEXT,
                "sha256": sha(status_bytes),
            },
        ],
        "registry": [
            {
                "id": offence.rule.text,
                "source_id": source_id,
                "program": program(offence),
                "exceptions": [
                    {
                        "id": exception.identifier.text,
                        "branch_id": offence.program.text,
                        "source_id": source_id,
                        "span": whole,
                        "guard": {
                            "kind": "is_infringed",
                            "target": exception.rule.text,
                        },
                        "effect": "defeat",
                    }
                ],
            },
            {
                "id": exception.rule.text,
                "source_id": source_id,
                "program": program(exception),
                "exceptions": [],
            },
        ],
        "facts": facts,
    }
    return canonical(request)


def compile_synthetic_text(
    model_source: str, scenario_source: str, model_path: str, scenario_path: str
) -> bytes:
    model = parse_synthetic(model_source, model_path)
    scenario = parse_scenario(scenario_source, scenario_path)
    return lower_synthetic(model, scenario, model_path, scenario_path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["compile"])
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--packet-dir", required=True, type=Path)
    args = parser.parse_args()
    try:
        compile_file(args.source, args.output, args.input_dir, args.packet_dir)
    except FrontendError as error:
        print(
            json.dumps(
                error.diagnostic(),
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ),
            file=sys.stderr,
        )
        return 1
    except (OSError, ValueError, KeyError) as error:
        diagnostic = {
            "code": "SFE015" if isinstance(error, OSError) else "SFE014",
            "path": str(args.source),
            "line": 1,
            "column": 1,
            "message": str(error),
        }
        print(
            json.dumps(
                diagnostic, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            ),
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
