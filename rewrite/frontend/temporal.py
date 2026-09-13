"""Synthetic YuhoSurface-v0.3 civil-date selection over complete module graphs."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date
from pathlib import Path
import re

from . import core, modules


LANGUAGE = "YuhoSurface-v0.3"
LOCK_COMPILER = "yuho.rewrite.frontend/v0.3"
SELECTION_SCHEMA = "yuho.temporal-selection/v0.1"
MAX_EXPRESSIONS = 16
EXPRESSION_ID = re.compile(r"[a-z][a-z0-9-]*")
CALENDAR_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")


@dataclass(frozen=True)
class Expression:
    identifier: core.Token
    version: core.Token
    start: core.Token
    end: core.Token | None
    model_alias: core.Token
    supersedes: core.Token | None


@dataclass(frozen=True)
class Root:
    path: str
    source_bytes: bytes
    language: core.Token
    module_id: core.Token
    module_version: core.Token
    jurisdiction: core.Token
    purpose: core.Token
    family: core.Token
    imports: tuple[modules.Import, ...]
    expressions: tuple[Expression, ...]
    limitations: tuple[core.Token, ...]


@dataclass(frozen=True)
class Scenario:
    path: str
    identifier: core.Token
    family: core.Token
    conduct_date: core.Token
    assignments: tuple[core.Assignment, ...]


@dataclass(frozen=True)
class Resolved:
    root: Root
    candidates: tuple[tuple[Expression, modules.Resolved], ...]
    lock: bytes
    vocabulary: frozenset[str]


@dataclass(frozen=True)
class Selected:
    expression: Expression
    model: core.SyntheticModel
    request: bytes
    record: bytes


def _fail(code: str, path: str, token: core.Token, message: str) -> None:
    raise core.FrontendError(code, path, token, message)


def _date(path: str, token: core.Token) -> date:
    if not CALENDAR_DATE.fullmatch(token.text):
        _fail("SFE040", path, token, "exact YYYY-MM-DD civil date required")
    try:
        return date.fromisoformat(token.text)
    except ValueError as error:
        raise core.FrontendError(
            "SFE040", path, token, "nonexistent calendar date"
        ) from error


def parse_root(source: bytes, path: str) -> Root:
    if len(source) > core.MAX_SOURCE_BYTES:
        _fail(
            "SFE036",
            path,
            core.Token("error", "", 1, 1),
            "module source limit exceeded",
        )
    try:
        text = source.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise core.FrontendError(
            "SFE001", path, core.Token("error", "", 1, 1), "module is not strict UTF-8"
        ) from error
    p = core.Parser(core.lex(text, path), path)
    p.take("language", "SFE049")
    language = p.word()
    p.take(";")
    p.take("module", "SFE038")
    module_id = p.word()
    p.take("version", "SFE024")
    version = p.word()
    p.take(";")
    p.take("{")
    p.take("kind", "SFE038")
    p.take("temporal", "SFE038")
    p.take(";")
    p.take("jurisdiction")
    jurisdiction = p.word()
    p.take(";")
    p.take("purpose")
    purpose = p.word()
    p.take(";")
    p.take("rule-family", "SFE038")
    family = p.word()
    p.take(";")
    imports: list[modules.Import] = []
    while p.tokens[p.index].text == "import":
        p.take("import")
        target = p.word()
        p.take("version", "SFE024")
        requested = p.word()
        p.take("as")
        alias = p.word()
        p.take(";")
        imports.append(modules.Import(target, requested, alias))
    expressions: list[Expression] = []
    while p.tokens[p.index].text == "expression":
        p.take("expression")
        identifier = p.word()
        p.take("version", "SFE024")
        expression_version = p.word()
        p.take("{")
        p.take("effective", "SFE040")
        p.take("from", "SFE040")
        start = p.word()
        end = None
        if p.tokens[p.index].text == "until":
            p.take("until")
            end = p.word()
        p.take(";")
        supersedes = None
        if p.tokens[p.index].text == "supersedes":
            p.take("supersedes")
            supersedes = p.word()
            p.take(";")
        p.take("model", "SFE038")
        model_alias = p.word()
        p.take(";")
        p.take("}")
        expressions.append(
            Expression(
                identifier, expression_version, start, end, model_alias, supersedes
            )
        )
        if len(expressions) > MAX_EXPRESSIONS:
            _fail("SFE036", path, identifier, "expression count limit exceeded")
    p.take("limitations", "SFE038")
    p.take("{")
    limitations: list[core.Token] = []
    while p.tokens[p.index].text != "}":
        limitations.append(p.take("string"))
        p.take(";")
    p.take("}")
    p.take("}")
    p.take("eof")
    root = Root(
        path,
        source,
        language,
        module_id,
        version,
        jurisdiction,
        purpose,
        family,
        tuple(imports),
        tuple(expressions),
        tuple(limitations),
    )
    check_root(root)
    return root


def check_root(root: Root) -> None:
    path = root.path
    if root.language.text != LANGUAGE:
        _fail("SFE049", path, root.language, "unsupported temporal language version")
    if not modules.MODULE_ID.fullmatch(
        root.module_id.text
    ) or not modules.SEMVER.fullmatch(root.module_version.text):
        _fail("SFE038", path, root.module_id, "invalid temporal module identity")
    if not modules.MODULE_ID.fullmatch(root.family.text):
        _fail("SFE038", path, root.family, "invalid rule-family identity")
    if (
        root.jurisdiction.text != "Fictional"
        or root.purpose.text != "compiler_fixture"
        or len(root.limitations) < 2
    ):
        _fail(
            "SFE021",
            path,
            root.jurisdiction,
            "temporal fixture must be fictional and limited",
        )
    if not root.expressions or len(root.imports) != len(root.expressions):
        _fail(
            "SFE038",
            path,
            root.family,
            "each complete expression needs one exact imported model",
        )
    aliases: set[str] = set()
    for item in root.imports:
        if not modules.MODULE_ID.fullmatch(
            item.module.text
        ) or not modules.SEMVER.fullmatch(item.version.text):
            _fail("SFE024", path, item.module, "invalid exact temporal import")
        if not EXPRESSION_ID.fullmatch(item.alias.text) or item.alias.text in aliases:
            _fail(
                "SFE028", path, item.alias, "invalid or duplicate temporal import alias"
            )
        aliases.add(item.alias.text)
    identities: dict[str, Expression] = {}
    versions: set[str] = set()
    used_aliases: set[str] = set()
    for expression in root.expressions:
        if not EXPRESSION_ID.fullmatch(
            expression.identifier.text
        ) or not modules.SEMVER.fullmatch(expression.version.text):
            _fail(
                "SFE039",
                path,
                expression.identifier,
                "invalid expression identity or version",
            )
        if (
            expression.identifier.text in identities
            or expression.version.text in versions
        ):
            _fail(
                "SFE039",
                path,
                expression.identifier,
                "duplicate expression ID or version",
            )
        identities[expression.identifier.text] = expression
        versions.add(expression.version.text)
        if (
            expression.model_alias.text not in aliases
            or expression.model_alias.text in used_aliases
        ):
            _fail(
                "SFE038",
                path,
                expression.model_alias,
                "expression must name its own imported complete model",
            )
        used_aliases.add(expression.model_alias.text)
        start = _date(path, expression.start)
        if expression.end is not None and _date(path, expression.end) <= start:
            _fail(
                "SFE042", path, expression.end, "empty or reversed effective interval"
            )
    ordered = sorted(
        root.expressions, key=lambda x: (_date(path, x.start), x.identifier.text)
    )
    for previous, current in zip(ordered, ordered[1:], strict=False):
        if previous.end is None or _date(path, previous.end) > _date(
            path, current.start
        ):
            _fail(
                "SFE043",
                path,
                current.start,
                f"overlap with {previous.identifier.text} at {previous.start.line}:{previous.start.column}",
            )
    active: set[str] = set()
    done: set[str] = set()

    def lineage(expression: Expression) -> None:
        key = expression.identifier.text
        if key in active:
            _fail(
                "SFE047",
                path,
                expression.supersedes or expression.identifier,
                "supersession cycle",
            )
        if key in done:
            return
        active.add(key)
        predecessor = expression.supersedes
        if predecessor is not None:
            name = predecessor.text
            if "::" in name:
                family, name = name.split("::", 1)
                if family != root.family.text:
                    _fail(
                        "SFE046",
                        path,
                        predecessor,
                        "cross-family supersession is unsupported",
                    )
            if name not in identities:
                _fail("SFE046", path, predecessor, "unknown superseded expression")
            prior = identities[name]
            if name in active:
                _fail("SFE047", path, predecessor, "supersession cycle")
            lineage(prior)
            if (
                _date(path, prior.start) >= _date(path, expression.start)
                or prior.end is None
                or _date(path, prior.end) > _date(path, expression.start)
            ):
                _fail(
                    "SFE048",
                    path,
                    predecessor,
                    "supersession chronology is inconsistent",
                )
        active.remove(key)
        done.add(key)

    for expression in root.expressions:
        lineage(expression)


def parse_scenario(source: str, path: str) -> Scenario:
    if len(source.encode("utf-8")) > core.MAX_SOURCE_BYTES:
        _fail(
            "SFE016",
            path,
            core.Token("error", "", 1, 1),
            "scenario source limit exceeded",
        )
    tokens = core.lex(source, path)
    declared_dates = [
        token
        for token in tokens
        if token.kind == "word" and token.text == "conduct_date"
    ]
    if len(declared_dates) > 1:
        _fail("SFE041", path, declared_dates[1], "duplicate conduct_date")
    p = core.Parser(tokens, path)
    p.take("scenario")
    identifier = p.word()
    p.take("for")
    family = p.word()
    p.take("{")
    if p.tokens[p.index].text != "conduct_date":
        _fail("SFE041", path, p.tokens[p.index], "explicit conduct_date required")
    p.take("conduct_date")
    conduct_date = p.word()
    p.take(";")
    if p.tokens[p.index].text == "conduct_date":
        _fail("SFE041", path, p.tokens[p.index], "duplicate conduct_date")
    p.take("proof_assignments")
    p.take("{")
    assignments = p.assignments()
    p.take("}")
    if p.tokens[p.index].text == "conduct_date":
        _fail("SFE041", path, p.tokens[p.index], "duplicate conduct_date")
    p.take("}")
    p.take("eof")
    _date(path, conduct_date)
    return Scenario(path, identifier, family, conduct_date, assignments)


def _vocabulary(
    model: core.SyntheticModel, path: str, token: core.Token
) -> dict[str, str]:
    result: dict[str, str] = {}
    for rule in (model.offence, model.exception):
        for element in rule.elements:
            local = "f:" + element.identifier.text.rsplit(".", 1)[-1]
            if local in result:
                _fail(
                    "SFE038",
                    path,
                    token,
                    "duplicate stable supplied-input name across expression modules",
                )
            result[local] = element.identifier.text
    return result


def resolve(root_file: Path, module_root: Path) -> Resolved:
    base = modules._regular_directory(module_root)
    selected = root_file.resolve(strict=False)
    if (
        ".." in root_file.parts
        or not selected.is_relative_to(base)
        or root_file.is_symlink()
    ):
        _fail(
            "SFE035",
            str(root_file),
            core.Token("error", "", 1, 1),
            "temporal root escapes module directory",
        )
    files = modules._module_files(base)
    if selected not in files:
        _fail(
            "SFE035",
            str(root_file),
            core.Token("error", "", 1, 1),
            "temporal root must be a regular .yh file",
        )
    root = parse_root(selected.read_bytes(), selected.relative_to(base).as_posix())
    indexed: dict[tuple[str, str], tuple[Path, modules.Module]] = {}
    for path in files:
        if path == selected:
            continue
        module = modules.parse_module(
            path.read_bytes(), path.relative_to(base).as_posix()
        )
        key = (module.identifier.text, module.version.text)
        if key in indexed:
            _fail(
                "SFE027", module.path, module.identifier, "duplicate module ID/version"
            )
        indexed[key] = (path, module)
    if (root.module_id.text, root.module_version.text) in indexed:
        _fail(
            "SFE027",
            root.path,
            root.module_id,
            "temporal root duplicates another module ID/version",
        )
    aliases: dict[str, tuple[Path, modules.Module]] = {}
    for item in root.imports:
        key = item.module.text, item.version.text
        if key not in indexed:
            code = (
                "SFE026"
                if any(identifier == key[0] for identifier, _ in indexed)
                else "SFE025"
            )
            _fail(code, root.path, item.module, "unresolved exact temporal import")
        path, module = indexed[key]
        if module.kind.text != "composition":
            _fail(
                "SFE033",
                root.path,
                item.module,
                "temporal expression requires a complete composition module",
            )
        if not any(
            export.kind.text == "output" and export.symbol.text == "final_rule"
            for export in module.exports
        ):
            _fail(
                "SFE030",
                root.path,
                item.module,
                "complete composition final output is private",
            )
        aliases[item.alias.text] = path, module
    candidates: list[tuple[Expression, modules.Resolved]] = []
    for expression in root.expressions:
        path, _ = aliases[expression.model_alias.text]
        candidates.append(
            (expression, modules.resolve(path, base, ignored=frozenset({selected})))
        )
    baseline = frozenset(
        _vocabulary(candidates[0][1].model, root.path, candidates[0][0].identifier)
    )
    for expression, candidate in candidates:
        if (
            frozenset(_vocabulary(candidate.model, root.path, expression.identifier))
            != baseline
        ):
            _fail(
                "SFE038",
                root.path,
                expression.identifier,
                "dated expressions must use identical supplied input vocabulary",
            )
    all_modules: dict[tuple[str, str], modules.Module] = {}
    topological: list[str] = []
    for _, candidate in sorted(
        candidates,
        key=lambda pair: (pair[1].root.identifier.text, pair[1].root.version.text),
    ):
        for module in candidate.ordered:
            key = module.identifier.text, module.version.text
            if key not in all_modules:
                all_modules[key] = module
                topological.append(f"{key[0]}@{key[1]}")
    topological.append(f"{root.module_id.text}@{root.module_version.text}")

    def row(
        identifier: str,
        version: str,
        source: bytes,
        imports: tuple[modules.Import, ...],
    ) -> dict:
        return {
            "id": identifier,
            "version": version,
            "byte_length": len(source),
            "sha256": core.sha(source),
            "imports": sorted(
                [
                    {
                        "id": item.module.text,
                        "version": item.version.text,
                        "alias": item.alias.text,
                    }
                    for item in imports
                ],
                key=lambda item: (item["id"], item["version"], item["alias"]),
            ),
        }

    rows = [
        row(
            module.identifier.text,
            module.version.text,
            module.source_bytes,
            module.imports,
        )
        for module in all_modules.values()
    ]
    rows.append(
        row(
            root.module_id.text,
            root.module_version.text,
            root.source_bytes,
            root.imports,
        )
    )
    lock = core.canonical(
        {
            "schema": modules.LOCK_SCHEMA,
            "language_version": LANGUAGE,
            "compiler": LOCK_COMPILER,
            "root": {"id": root.module_id.text, "version": root.module_version.text},
            "modules": sorted(rows, key=lambda item: (item["id"], item["version"])),
            "topological_order": topological,
        }
    )
    return Resolved(root, tuple(candidates), lock, baseline)


def select(resolved: Resolved, scenario: Scenario) -> Selected:
    root = resolved.root
    if scenario.family.text != root.family.text:
        _fail(
            "SFE038",
            scenario.path,
            scenario.family,
            "scenario rule family differs from temporal root",
        )
    day = _date(scenario.path, scenario.conduct_date)
    matches = [
        (expression, candidate)
        for expression, candidate in resolved.candidates
        if _date(root.path, expression.start) <= day
        and (expression.end is None or day < _date(root.path, expression.end))
    ]
    if not matches:
        _fail(
            "SFE044",
            scenario.path,
            scenario.conduct_date,
            "no applicable authored expression",
        )
    if len(matches) != 1:
        _fail(
            "SFE045",
            scenario.path,
            scenario.conduct_date,
            "multiple authored expressions match conduct date",
        )
    expression, candidate = matches[0]
    vocabulary = _vocabulary(candidate.model, root.path, expression.identifier)
    assignment_map: dict[str, core.Assignment] = {}
    for assignment in scenario.assignments:
        key = assignment.identifier.text
        if key in assignment_map:
            _fail(
                "SFE002",
                scenario.path,
                assignment.identifier,
                "duplicate supplied input",
            )
        if key not in vocabulary:
            _fail(
                "SFE009",
                scenario.path,
                assignment.identifier,
                "unexpected supplied input",
            )
        assignment_map[key] = replace(
            assignment, identifier=replace(assignment.identifier, text=vocabulary[key])
        )
    if frozenset(assignment_map) != resolved.vocabulary:
        _fail("SFE009", scenario.path, scenario.identifier, "missing supplied input")
    lowered = core.Scenario(
        scenario.identifier,
        candidate.model.identifier,
        tuple(assignment_map[key] for key in sorted(assignment_map)),
    )
    request = core.lower_synthetic(
        candidate.model, lowered, candidate.root.path, scenario.path
    )
    record = core.canonical(
        {
            "schema": SELECTION_SCHEMA,
            "root": {"id": root.module_id.text, "version": root.module_version.text},
            "rule_family": root.family.text,
            "conduct_date": scenario.conduct_date.text,
            "candidates": [
                {
                    "id": item.identifier.text,
                    "version": item.version.text,
                    "effective_from": item.start.text,
                    "effective_to": {"kind": "open"}
                    if item.end is None
                    else {"kind": "date", "value": item.end.text},
                }
                for item, _ in sorted(
                    resolved.candidates,
                    key=lambda pair: (
                        _date(root.path, pair[0].start),
                        pair[0].identifier.text,
                    ),
                )
            ],
            "selected": {
                "id": expression.identifier.text,
                "version": expression.version.text,
            },
            "selected_source_module_sha256": core.sha(candidate.root.source_bytes),
            "module_lock_sha256": core.sha(resolved.lock),
            "reason": "conduct_date_within_effective_interval",
        }
    )
    return Selected(expression, candidate.model, request, record)


def verify_selection(actual: bytes, expected: bytes, path: str) -> None:
    if actual != expected:
        _fail(
            "SFE051",
            path,
            core.Token("error", "", 1, 1),
            "temporal selection record or module lock differs",
        )


def verify_lock(actual: bytes, expected: bytes, path: str) -> None:
    if actual != expected:
        _fail(
            "SFE051",
            path,
            core.Token("error", "", 1, 1),
            "temporal module lock differs from resolved source bytes or imports",
        )
