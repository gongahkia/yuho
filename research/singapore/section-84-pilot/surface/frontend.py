"""Closed, source-aware research surface slice for the section 84 prototype.

This is an authoring frontend for one reviewed model, not the legacy v5 parser
or a new kernel protocol. The executable tree is lowered from named syntax;
the locked source packet supplies only exact source bytes and spans.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import importlib.util
import json
from pathlib import Path
import re
import stat
import sys
import tempfile


HERE = Path(__file__).resolve().parent
PILOT = HERE.parent
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
                propositions.append(Leaf(leaf_id, proposition, quote))
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
        assignments: list[Assignment] = []
        while self.tokens[self.index].text != "}":
            assignment_id = self.word()
            self.take("=")
            status = self.word()
            reason = None
            if self.tokens[self.index].text == "(":
                self.take("(")
                reason = self.word()
                self.take(")")
            self.take(";")
            assignments.append(Assignment(assignment_id, status, reason))
            if len(assignments) > MAX_NODES:
                raise FrontendError(
                    "SFE016", self.path, assignment_id, "assignment limit exceeded"
                )
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
            tuple(assignments),
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

    if (
        model.identifier.text
        != "SingaporePenalCodeSection84Post2022ResearchPrototype-v1"
        or model.variant.text != "SuppliedProofStatus-v1"
        or model.jurisdiction.text != "Singapore"
        or model.purpose.text != "research_prototype"
    ):
        fail("SFE004", model.identifier, "unsupported model, variant or scope")
    if (
        model.reference_date.text != "2026-09-13"
        or model.max_nodes.text != "1024"
        or not re.fullmatch(r"[A-Z][0-9]{2}", model.request_id.text)
    ):
        fail("SFE004", model.reference_date, "unsupported request policy or ID")
    if (
        model.root_rule.text != "r:section84"
        or model.program.text != "p:section84"
        or model.path.text != "section84"
    ):
        fail("SFE007", model.root_rule, "unsupported or missing root declaration")
    if tuple(token.text for token in model.burden) != (
        "section107",
        "defence",
        "legal",
        "balance_of_probabilities",
    ):
        fail("SFE011", model.burden[0], "invalid contextual burden or standard")
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
        if isinstance(item, Leaf) and item.quote.text not in quote_spans:
            raise FrontendError("SFE003", path, item.quote, "unknown source quote")
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
            needle = quote_by_id[item.quote.text].encode("utf-8")
            start = extracted.index(needle)
            if (
                pilot.span(extracted, start, start + len(needle))
                not in row["supporting_spans"]
            ):
                raise FrontendError(
                    "SFE014",
                    path,
                    item.quote,
                    "quote span differs from reviewed mapping",
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
            "code": "SFE014",
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
