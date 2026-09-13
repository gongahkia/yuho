"""Offline YuhoSurface-v0.2 module resolution and explicit synthetic composition."""

from __future__ import annotations

from dataclasses import dataclass, replace
import os
from pathlib import Path
import re
import stat

from . import core


LANGUAGE = "YuhoSurface-v0.2"
LOCK_SCHEMA = "yuho.module-lock/v0.1"
COMPILER = "yuho.rewrite.frontend/v0.2"
MAX_MODULES = 32
MAX_IMPORT_DEPTH = 16
MAX_AGGREGATE_BYTES = 1024 * 1024
MAX_ROOT_ENTRIES = 128
MODULE_ID = re.compile(r"[a-z][a-z0-9-]*(?:\.[a-z][a-z0-9-]*)+")
SEMVER = re.compile(r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)")
LOCAL_ID = re.compile(r"[a-z]+:[A-Za-z][A-Za-z0-9-]*")


@dataclass(frozen=True)
class Import:
    module: core.Token
    version: core.Token
    alias: core.Token


@dataclass(frozen=True)
class Export:
    kind: core.Token
    symbol: core.Token


@dataclass(frozen=True)
class Composition:
    offence: core.Token
    exception: core.Token
    attached_exception: core.Token
    attached_offence: core.Token
    outputs: tuple[tuple[core.Token, core.Token], ...]


@dataclass(frozen=True)
class Module:
    path: str
    source_bytes: bytes
    language: core.Token
    identifier: core.Token
    version: core.Token
    kind: core.Token
    jurisdiction: core.Token
    purpose: core.Token
    imports: tuple[Import, ...]
    exports: tuple[Export, ...]
    model_id: core.Token | None
    request_id: core.Token | None
    policy_date: core.Token | None
    max_nodes: core.Token | None
    sources: tuple[tuple[core.Token, core.Token, core.Token], ...]
    quotes: tuple[tuple[core.Token, core.Token], ...]
    burden: tuple[core.Token, core.Token, core.Token, core.Token] | None
    rule: core.SyntheticRule | None
    composition: Composition | None
    limitations: tuple[core.Token, ...]


@dataclass(frozen=True)
class Resolved:
    root: Module
    ordered: tuple[Module, ...]
    model: core.SyntheticModel
    lock: bytes


def _fail(code: str, module: Module, token: core.Token, message: str) -> None:
    raise core.FrontendError(code, module.path, token, message)


def parse_module(source: bytes, path: str) -> Module:
    if len(source) > core.MAX_SOURCE_BYTES:
        raise core.FrontendError(
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
    p.take("language", "SFE022")
    language = p.word()
    p.take(";")
    p.take("module", "SFE022")
    identifier = p.word()
    p.take("version", "SFE024")
    version = p.word()
    p.take(";")
    p.take("{")
    p.take("kind")
    kind = p.word()
    p.take(";")
    p.take("jurisdiction")
    jurisdiction = p.word()
    p.take(";")
    p.take("purpose")
    purpose = p.word()
    p.take(";")
    imports: list[Import] = []
    while p.tokens[p.index].text == "import":
        p.take("import")
        target = p.word()
        p.take("version", "SFE024")
        requested = p.word()
        p.take("as", "SFE024")
        alias = p.word()
        p.take(";")
        imports.append(Import(target, requested, alias))
    exports: list[Export] = []
    while p.tokens[p.index].text == "export":
        p.take("export")
        category, symbol = p.word(), p.word()
        p.take(";")
        exports.append(Export(category, symbol))

    model_id = request_id = policy_date = max_nodes = None
    if kind.text == "composition":
        p.take("model")
        model_id = p.word()
        p.take(";")
        p.take("request")
        request_id = p.word()
        p.take(";")
        p.take("policy")
        policy_date, max_nodes = p.word(), p.word()
        p.take(";")
    p.take("provenance")
    p.take("{")
    sources: list[tuple[core.Token, core.Token, core.Token]] = []
    quotes: list[tuple[core.Token, core.Token]] = []
    while p.tokens[p.index].text != "}":
        head = p.word()
        if head.text == "source":
            sources.append((p.word(), p.word(), p.take("string")))
        elif head.text == "quote":
            quotes.append((p.word(), p.take("string")))
        else:
            raise core.FrontendError(
                "SFE013", path, head, "unsupported module provenance"
            )
        p.take(";")
    p.take("}")
    p.take("annotations")
    p.take("{")
    p.take("burden")
    burden = (p.word(), p.word(), p.word(), p.word())
    p.take(";")
    p.take("}")
    rule = None
    composition = None
    if kind.text in {"offence", "exception"}:
        rule = p.synthetic_rule(kind.text, attached=False)
    elif kind.text == "composition":
        p.take("compose")
        p.take("{")
        p.take("offence")
        offence = p.word()
        p.take(";")
        p.take("exception")
        exception = p.word()
        p.take(";")
        p.take("attach")
        attached_exception = p.word()
        p.take("to")
        attached_offence = p.word()
        p.take(";")
        p.take("outputs")
        p.take("{")
        outputs: list[tuple[core.Token, core.Token]] = []
        while p.tokens[p.index].text != "}":
            label, symbol = p.word(), p.word()
            p.take(";")
            outputs.append((label, symbol))
        p.take("}")
        p.take("}")
        composition = Composition(
            offence, exception, attached_exception, attached_offence, tuple(outputs)
        )
    else:
        raise core.FrontendError("SFE022", path, kind, "unsupported module kind")
    p.take("limitations")
    p.take("{")
    limitations: list[core.Token] = []
    while p.tokens[p.index].text != "}":
        limitations.append(p.take("string"))
        p.take(";")
    p.take("}")
    p.take("}")
    p.take("eof")
    module = Module(
        path,
        source,
        language,
        identifier,
        version,
        kind,
        jurisdiction,
        purpose,
        tuple(imports),
        tuple(exports),
        model_id,
        request_id,
        policy_date,
        max_nodes,
        tuple(sources),
        tuple(quotes),
        burden,
        rule,
        composition,
        tuple(limitations),
    )
    check_local(module)
    return module


def _symbols(module: Module) -> dict[str, str]:
    if module.kind.text == "composition":
        return {label.text: "output" for label, _ in module.composition.outputs}
    rule = module.rule
    result = {
        rule.identifier.text: module.kind.text,
        rule.rule.text: "rule",
        rule.program.text: "program",
    }
    result.update((item.identifier.text, "element") for item in rule.elements)
    result.update((item.identifier.text, "proposition") for item in rule.groups)
    return result


def check_local(module: Module) -> None:
    if module.language.text != LANGUAGE:
        _fail("SFE023", module, module.language, "unsupported surface-language version")
    if not MODULE_ID.fullmatch(module.identifier.text):
        _fail(
            "SFE022", module, module.identifier, "invalid canonical module identifier"
        )
    if not SEMVER.fullmatch(module.version.text):
        _fail("SFE024", module, module.version, "exact semantic version required")
    if (
        module.jurisdiction.text != "Fictional"
        or module.purpose.text != "compiler_fixture"
    ):
        _fail(
            "SFE021",
            module,
            module.jurisdiction,
            "modules must be fictional compiler fixtures",
        )
    if len(module.limitations) < 2 or any(not item.text for item in module.limitations):
        _fail("SFE022", module, module.identifier, "fictional limitations required")
    aliases: set[str] = set()
    for item in module.imports:
        if not MODULE_ID.fullmatch(item.module.text):
            _fail("SFE035", module, item.module, "invalid or unsafe module identifier")
        if not SEMVER.fullmatch(item.version.text):
            _fail("SFE024", module, item.version, "exact import version required")
        if not re.fullmatch(r"[a-z][a-z0-9-]*", item.alias.text):
            _fail("SFE028", module, item.alias, "invalid import alias")
        if item.alias.text in aliases:
            _fail("SFE028", module, item.alias, "duplicate import alias")
        aliases.add(item.alias.text)
    if module.kind.text == "composition":
        if (
            module.rule is not None
            or module.composition is None
            or module.model_id is None
        ):
            _fail("SFE022", module, module.kind, "invalid composition declaration")
        if module.quotes or len(module.sources) != 2:
            _fail(
                "SFE022",
                module,
                module.kind,
                "composition requires only two source declarations",
            )
        if not module.imports:
            _fail(
                "SFE025", module, module.kind, "composition requires explicit imports"
            )
    else:
        if module.rule is None or module.composition is not None or module.sources:
            _fail("SFE022", module, module.kind, "invalid child-module declarations")
        expected = (
            {"conduct", "circumstance", "fault"}
            if module.kind.text == "offence"
            else {"circumstance", "purpose"}
        )
        categories = [item.category.text for item in module.rule.elements]
        if set(categories) != expected or len(categories) != len(expected):
            _fail(
                "SFE017",
                module,
                module.rule.identifier,
                "typed element categories differ from the bounded subset",
            )
        quote_ids = [item.text for item, _ in module.quotes]
        if len(set(quote_ids)) != len(quote_ids):
            _fail("SFE002", module, module.identifier, "duplicate quote ID")
        if set(quote_ids) != {item.quote.text for item in module.rule.elements}:
            _fail(
                "SFE003",
                module,
                module.rule.identifier,
                "element quote reference is missing or unused",
            )
        declarations = [module.rule.identifier, module.rule.rule, module.rule.program]
        declarations += [
            item.identifier for item in (*module.rule.elements, *module.rule.groups)
        ]
        if len({item.text for item in declarations}) != len(declarations):
            _fail(
                "SFE002", module, module.rule.identifier, "duplicate local semantic ID"
            )
        for token in declarations:
            if not LOCAL_ID.fullmatch(token.text):
                _fail("SFE017", module, token, "invalid local semantic ID")
        if not module.rule.groups:
            _fail("SFE007", module, module.rule.identifier, "missing root proposition")
        nodes = {
            item.identifier.text: item
            for item in (*module.rule.elements, *module.rule.groups)
        }
        visited: set[str] = set()
        visiting: set[str] = set()
        used = {key: 0 for key in nodes}

        def walk(key: str) -> None:
            item = nodes[key]
            if key in visiting:
                _fail("SFE008", module, item.identifier, "cyclic local proposition")
            if key in visited:
                return
            visiting.add(key)
            if isinstance(item, core.Group):
                for member in item.members:
                    if member.text.startswith("ann:"):
                        _fail("SFE012", module, member, "annotation is not executable")
                    if member.text not in nodes:
                        _fail(
                            "SFE003", module, member, "unknown or nonlocal proposition"
                        )
                    used[member.text] += 1
                    walk(member.text)
            visiting.remove(key)
            visited.add(key)

        walk(module.rule.groups[-1].identifier.text)
        if visited != set(nodes) or any(count > 1 for count in used.values()):
            _fail(
                "SFE006",
                module,
                module.rule.identifier,
                "local declarations must form one tree",
            )
    if tuple(item.text for item in module.burden[1:]) != (
        "none",
        "none",
        "not_applicable",
    ):
        _fail("SFE011", module, module.burden[0], "invalid contextual annotation")
    symbols = _symbols(module)
    seen: set[str] = set()
    for item in module.exports:
        if item.symbol.text in seen:
            _fail("SFE027", module, item.symbol, "duplicate export")
        if symbols.get(item.symbol.text) != item.kind.text:
            _fail("SFE033", module, item.symbol, "export has wrong or unknown type")
        seen.add(item.symbol.text)


def _regular_directory(path: Path) -> Path:
    if ".." in path.parts or not path.is_dir():
        raise core.FrontendError(
            "SFE035", str(path), core.Token("error", "", 1, 1), "invalid module root"
        )
    for component in (path, *path.parents):
        if component.is_symlink():
            raise core.FrontendError(
                "SFE035",
                str(path),
                core.Token("error", "", 1, 1),
                "symlinked module root",
            )
    return path.resolve(strict=True)


def _module_files(root: Path) -> list[Path]:
    files: list[Path] = []
    total = 0
    entries = 0
    for directory, subdirectories, names in os.walk(root, followlinks=False):
        entries += len(subdirectories) + len(names)
        if (
            entries > MAX_ROOT_ENTRIES
            or len(Path(directory).relative_to(root).parts) > MAX_IMPORT_DEPTH
        ):
            raise core.FrontendError(
                "SFE036",
                str(directory),
                core.Token("error", "", 1, 1),
                "module-root entry or directory-depth limit exceeded",
            )
        subdirectories.sort()
        names.sort()
        for name in (*subdirectories, *names):
            candidate = Path(directory) / name
            mode = candidate.lstat().st_mode
            if stat.S_ISLNK(mode):
                raise core.FrontendError(
                    "SFE035",
                    str(candidate),
                    core.Token("error", "", 1, 1),
                    "symlink inside module root",
                )
            if name in names and not stat.S_ISREG(mode):
                raise core.FrontendError(
                    "SFE035",
                    str(candidate),
                    core.Token("error", "", 1, 1),
                    "unsupported module-root entry",
                )
        for name in names:
            if not name.endswith(".yh"):
                continue
            file = Path(directory) / name
            total += file.stat().st_size
            files.append(file)
            if len(files) > MAX_MODULES or total > MAX_AGGREGATE_BYTES:
                raise core.FrontendError(
                    "SFE036",
                    str(file),
                    core.Token("error", "", 1, 1),
                    "module count or aggregate source limit exceeded",
                )
    return files


def _namespace(module: Module, token: core.Token) -> core.Token:
    prefix, local = token.text.split(":", 1)
    version = module.version.text.replace(".", "-")
    return replace(
        token, text=f"{prefix}:{module.identifier.text}.version-{version}.{local}"
    )


def _qualified(
    root: Module, indexed: dict[str, Module], token: core.Token, kind: str
) -> tuple[Module, core.Token]:
    if "::" not in token.text:
        _fail("SFE032", root, token, "imported symbol must be alias-qualified")
    alias, symbol = token.text.split("::", 1)
    if alias not in indexed:
        _fail("SFE031", root, token, "unknown import alias")
    target = indexed[alias]
    symbols = _symbols(target)
    if symbol not in symbols:
        _fail("SFE031", root, token, "unknown qualified symbol")
    if symbol not in {item.symbol.text for item in target.exports}:
        _fail("SFE030", root, token, "symbol is private to imported module")
    if symbols[symbol] != kind:
        _fail("SFE033", root, token, "composition target type mismatch")
    return target, _namespace(target, replace(token, text=symbol))


def _rename_rule(module: Module) -> core.SyntheticRule:
    rule = module.rule
    return replace(
        rule,
        identifier=_namespace(module, rule.identifier),
        rule=_namespace(module, rule.rule),
        program=_namespace(module, rule.program),
        elements=tuple(
            replace(
                item,
                identifier=_namespace(module, item.identifier),
                quote=_namespace(module, item.quote),
            )
            for item in rule.elements
        ),
        groups=tuple(
            replace(
                item,
                identifier=_namespace(module, item.identifier),
                members=tuple(_namespace(module, member) for member in item.members),
            )
            for item in rule.groups
        ),
    )


def _compose(
    root: Module, modules: dict[tuple[str, str], Module]
) -> core.SyntheticModel:
    aliases = {
        item.alias.text: modules[(item.module.text, item.version.text)]
        for item in root.imports
    }
    composition = root.composition
    offence_module, offence_id = _qualified(
        root, aliases, composition.offence, "offence"
    )
    exception_module, exception_id = _qualified(
        root, aliases, composition.exception, "exception"
    )
    attach_module, attach_id = _qualified(
        root, aliases, composition.attached_exception, "exception"
    )
    target_module, target_id = _qualified(
        root, aliases, composition.attached_offence, "offence"
    )
    if (attach_module, attach_id.text, target_module, target_id.text) != (
        exception_module,
        exception_id.text,
        offence_module,
        offence_id.text,
    ):
        _fail(
            "SFE033",
            root,
            composition.attached_exception,
            "attachment differs from selected models",
        )
    if (
        offence_module.kind.text != "offence"
        or exception_module.kind.text != "exception"
    ):
        _fail(
            "SFE033",
            root,
            composition.offence,
            "composition requires offence and exception modules",
        )
    offence = _rename_rule(offence_module)
    exception = replace(_rename_rule(exception_module), target=offence.identifier)
    output_kinds = {
        "offence_requirements": "proposition",
        "exception_applicable": "proposition",
        "defeated_branch": "program",
        "final_rule": "rule",
    }
    expected_modules = {
        "offence_requirements": offence_module,
        "exception_applicable": exception_module,
        "defeated_branch": offence_module,
        "final_rule": offence_module,
    }
    outputs: list[tuple[core.Token, core.Token]] = []
    seen: set[str] = set()
    for label, symbol in composition.outputs:
        if label.text not in output_kinds or label.text in seen:
            _fail("SFE020", root, label, "unknown or duplicate technical output")
        target, renamed = _qualified(root, aliases, symbol, output_kinds[label.text])
        if target != expected_modules[label.text]:
            _fail("SFE033", root, symbol, "output refers to wrong imported model")
        outputs.append((label, renamed))
        seen.add(label.text)
    if seen != set(output_kinds):
        _fail("SFE020", root, root.identifier, "complete technical outputs required")
    quotes = tuple(
        (_namespace(module, identifier), value)
        for module in (offence_module, exception_module)
        for identifier, value in module.quotes
    )
    ids = [
        item.text
        for rule in (offence, exception)
        for item in (
            rule.identifier,
            rule.rule,
            rule.program,
            *(element.identifier for element in rule.elements),
            *(group.identifier for group in rule.groups),
        )
    ]
    if len(ids) != len(set(ids)):
        _fail("SFE034", root, root.identifier, "conflicting composed semantic IDs")
    limitations = tuple(
        [*root.limitations, *offence_module.limitations, *exception_module.limitations]
    )
    model = core.SyntheticModel(
        root.model_id,
        core.Token("word", "SuppliedProofStatus-v1", root.kind.line, root.kind.column),
        root.jurisdiction,
        root.purpose,
        root.request_id,
        root.policy_date,
        root.max_nodes,
        root.sources,
        quotes,
        root.burden,
        offence,
        exception,
        tuple(outputs),
        limitations,
    )
    core.check_synthetic(model, root.path)
    return model


def resolve(root_file: Path, module_root: Path) -> Resolved:
    base = _regular_directory(module_root)
    selected = root_file.resolve(strict=False)
    if (
        ".." in root_file.parts
        or not selected.is_relative_to(base)
        or root_file.is_symlink()
    ):
        raise core.FrontendError(
            "SFE035",
            str(root_file),
            core.Token("error", "", 1, 1),
            "root module escapes configured directory",
        )
    files = _module_files(base)
    if selected not in files:
        raise core.FrontendError(
            "SFE035",
            str(root_file),
            core.Token("error", "", 1, 1),
            "root module is not a regular indexed .yh file",
        )
    index: dict[tuple[str, str], Module] = {}
    by_id: dict[str, set[str]] = {}
    selected_module: Module | None = None
    for path in files:
        raw = path.read_bytes()
        relative = path.relative_to(base).as_posix()
        module = parse_module(raw, relative)
        key = (module.identifier.text, module.version.text)
        if key in index:
            _fail(
                "SFE027",
                module,
                module.identifier,
                "duplicate module ID/version, including differing bytes",
            )
        index[key] = module
        by_id.setdefault(key[0], set()).add(key[1])
        if path == selected:
            selected_module = module
    root = selected_module
    if root is None or root.kind.text != "composition":
        raise core.FrontendError(
            "SFE022",
            str(root_file),
            core.Token("error", "", 1, 1),
            "root must be a composition module",
        )
    visited: set[tuple[str, str]] = set()
    active: list[tuple[str, str]] = []
    order: list[Module] = []

    def walk(module: Module, depth: int) -> None:
        key = (module.identifier.text, module.version.text)
        if depth > MAX_IMPORT_DEPTH:
            _fail("SFE036", module, module.identifier, "import depth limit exceeded")
        if key in active:
            chain = " -> ".join(item[0] for item in (*active, key))
            _fail("SFE029", module, module.identifier, f"import cycle: {chain}")
        if key in visited:
            return
        active.append(key)
        for item in sorted(
            module.imports, key=lambda x: (x.module.text, x.version.text, x.alias.text)
        ):
            target = (item.module.text, item.version.text)
            if target not in index:
                code = "SFE026" if item.module.text in by_id else "SFE025"
                _fail(
                    code,
                    module,
                    item.module,
                    f"unresolved exact import via {' -> '.join(x[0] for x in active)}",
                )
            if target in active:
                chain = " -> ".join(item[0] for item in (*active, target))
                _fail("SFE029", module, item.module, f"import cycle: {chain}")
            walk(index[target], depth + 1)
        active.pop()
        visited.add(key)
        order.append(module)

    walk(root, 1)
    model = _compose(root, index)
    lock = {
        "schema": LOCK_SCHEMA,
        "language_version": LANGUAGE,
        "compiler": COMPILER,
        "root": {"id": root.identifier.text, "version": root.version.text},
        "topological_order": [
            f"{module.identifier.text}@{module.version.text}" for module in order
        ],
        "modules": sorted(
            [
                {
                    "id": module.identifier.text,
                    "version": module.version.text,
                    "byte_length": len(module.source_bytes),
                    "sha256": core.sha(module.source_bytes),
                    "imports": sorted(
                        [
                            {
                                "id": item.module.text,
                                "version": item.version.text,
                                "alias": item.alias.text,
                            }
                            for item in module.imports
                        ],
                        key=lambda row: (row["id"], row["version"], row["alias"]),
                    ),
                }
                for module in order
            ],
            key=lambda row: (row["id"], row["version"]),
        ),
    }
    return Resolved(root, tuple(order), model, core.canonical(lock))


def verify_lock(resolved: Resolved, expected: bytes, path: str) -> None:
    if expected != resolved.lock:
        raise core.FrontendError(
            "SFE037",
            path,
            resolved.root.identifier,
            "module lock differs from exact resolved source bytes or edges",
        )


def compile_resolved(
    resolved: Resolved, scenario_source: str, scenario_path: str
) -> bytes:
    scenario = core.parse_scenario(scenario_source, scenario_path)
    return core.lower_synthetic(
        resolved.model, scenario, resolved.root.path, scenario_path
    )
