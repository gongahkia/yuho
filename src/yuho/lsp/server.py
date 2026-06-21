"""pygls-backed Yuho language server."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from urllib.parse import unquote, urlparse

from lsprotocol import types
from pygls.lsp.server import LanguageServer

from yuho import __version__
from yuho.ast import ASTBuilder
from yuho.ast.nodes import (
    ASTNode,
    ApplyScopeNode,
    IsInfringedNode,
    ModuleNode,
    StatuteNode,
)
from yuho.library.reference_graph import ReferenceGraph, _normalise_section, build_reference_graph
from yuho.parser import get_parser
from yuho.parser.source_location import SourceLocation
from yuho.parser.wrapper import ParseResult, Parser
from yuho.resolver.module_resolver import ModuleResolutionError, ModuleResolver
from yuho.services.analysis import AnalysisResult, analyze_source

DEFAULT_LIBRARY_DIR = Path("library/penal_code")


@dataclass(frozen=True)
class ParsedDocument:
    uri: str
    file: str
    source: str
    result: ParseResult
    ast: Optional[ModuleNode] = None
    analysis: Optional[AnalysisResult] = None


class YuhoLanguageServer(LanguageServer):
    def __init__(self, parser: Optional[Parser] = None) -> None:
        super().__init__("yuho-lsp", __version__)
        self.parser = parser or get_parser()
        self.parsed_documents: dict[str, ParsedDocument] = {}
        self.reference_graphs: dict[str, ReferenceGraph] = {}

    def parse_source(self, uri: str, source: str) -> ParsedDocument:
        file = uri_to_file(uri)
        result = self.parser.parse(source, file=file)
        analysis = analyze_source(source, file=file, run_semantic=True)
        ast = analysis.ast or build_ast(source, file, result)
        parsed = ParsedDocument(
            uri=uri,
            file=file,
            source=source,
            result=result,
            ast=ast,
            analysis=analysis,
        )
        self.parsed_documents[uri] = parsed
        return parsed

    def parse_text_document(self, uri: str) -> Optional[ParsedDocument]:
        document = self.workspace.get_text_document(uri)
        if document is None:
            return None
        return self.parse_source(uri, document.source)

    def cached_parse(self, uri: str) -> Optional[ParsedDocument]:
        return self.parsed_documents.get(uri)

    def drop_document(self, uri: str) -> None:
        self.parsed_documents.pop(uri, None)

    def diagnostics_for_uri(self, uri: str) -> list[types.Diagnostic]:
        parsed = self.cached_parse(uri) or self.parse_text_document(uri)
        if parsed is None or parsed.analysis is None:
            return []
        return analysis_to_diagnostics(parsed.analysis)

    def publish_diagnostics_for_uri(self, uri: str) -> None:
        self.text_document_publish_diagnostics(
            types.PublishDiagnosticsParams(uri=uri, diagnostics=self.diagnostics_for_uri(uri))
        )

    def hover_at(self, uri: str, line: int, character: int) -> Optional[types.Hover]:
        parsed = self.cached_parse(uri) or self.parse_text_document(uri)
        if parsed is None or parsed.ast is None:
            return None
        node = ast_node_at_lsp_position(parsed.ast, line, character)
        if node is None or node.source_location is None:
            return None
        return types.Hover(
            contents=types.MarkupContent(
                kind=types.MarkupKind.Markdown,
                value=hover_markdown(node),
            ),
            range=location_to_range(node.source_location),
        )

    def definition_at(
        self,
        uri: str,
        line: int,
        character: int,
    ) -> Optional[list[types.Location]]:
        parsed = self.cached_parse(uri) or self.parse_text_document(uri)
        if parsed is None or parsed.ast is None:
            return None
        section = cross_section_ref_at_lsp_position(parsed, line, character)
        if section is None:
            return None
        location = resolve_section_definition(self, parsed, section)
        return [location] if location is not None else None

    def reference_graph(self, library_dir: Path = DEFAULT_LIBRARY_DIR) -> Optional[ReferenceGraph]:
        resolved = library_dir.resolve()
        if not resolved.exists():
            return None
        key = str(resolved)
        graph = self.reference_graphs.get(key)
        if graph is None:
            graph = build_reference_graph(resolved)
            self.reference_graphs[key] = graph
        return graph


def create_server() -> YuhoLanguageServer:
    server = YuhoLanguageServer()
    register_features(server)
    return server


def register_features(server: YuhoLanguageServer) -> None:
    @server.feature(types.TEXT_DOCUMENT_DID_OPEN)
    def did_open(params: types.DidOpenTextDocumentParams) -> None:
        server.parse_source(params.text_document.uri, params.text_document.text)
        server.publish_diagnostics_for_uri(params.text_document.uri)

    @server.feature(types.TEXT_DOCUMENT_DID_CHANGE)
    def did_change(params: types.DidChangeTextDocumentParams) -> None:
        document = server.workspace.get_text_document(params.text_document.uri)
        if document is not None:
            server.parse_source(params.text_document.uri, document.source)
            server.publish_diagnostics_for_uri(params.text_document.uri)

    @server.feature(types.TEXT_DOCUMENT_DID_SAVE)
    def did_save(params: types.DidSaveTextDocumentParams) -> None:
        server.parse_text_document(params.text_document.uri)
        server.publish_diagnostics_for_uri(params.text_document.uri)

    @server.feature(types.TEXT_DOCUMENT_DID_CLOSE)
    def did_close(params: types.DidCloseTextDocumentParams) -> None:
        server.drop_document(params.text_document.uri)
        server.text_document_publish_diagnostics(
            types.PublishDiagnosticsParams(uri=params.text_document.uri, diagnostics=[])
        )

    @server.feature(types.TEXT_DOCUMENT_HOVER)
    def hover(params: types.HoverParams) -> Optional[types.Hover]:
        return server.hover_at(
            params.text_document.uri,
            params.position.line,
            params.position.character,
        )

    @server.feature(types.TEXT_DOCUMENT_DEFINITION)
    def definition(params: types.DefinitionParams) -> Optional[list[types.Location]]:
        return server.definition_at(
            params.text_document.uri,
            params.position.line,
            params.position.character,
        )


def build_ast(source: str, file: str, result: ParseResult) -> Optional[ModuleNode]:
    if not result.is_valid or result.root_node is None:
        return None
    try:
        return ASTBuilder(source, file).build(result.root_node)
    except Exception:
        return None


def ast_node_at_lsp_position(
    root: ASTNode,
    line: int,
    character: int,
) -> Optional[ASTNode]:
    user_line = line + 1
    user_col = character + 1
    best: Optional[ASTNode] = None
    stack = [root]
    while stack:
        node = stack.pop()
        loc = node.source_location
        if loc is not None and location_contains_lsp_position(loc, user_line, user_col):
            if best is None or location_size(loc) <= location_size(best.source_location):
                best = node
            stack.extend(child for child in node.children() if child is not None)
    return best


def cross_section_ref_at_lsp_position(
    parsed: ParsedDocument,
    line: int,
    character: int,
) -> Optional[str]:
    if parsed.ast is None:
        return None
    word = word_at_lsp_position(parsed.source, line, character)
    if not word:
        return None
    ref = _normalise_section(word)
    stack = [parsed.ast]
    while stack:
        node = stack.pop()
        loc = node.source_location
        if loc is None or not location_contains_lsp_position(loc, line + 1, character + 1):
            continue
        if ref in cross_section_refs(node):
            return ref
        stack.extend(child for child in node.children() if child is not None)
    return None


def cross_section_refs(node: ASTNode) -> tuple[str, ...]:
    if isinstance(node, (ApplyScopeNode, IsInfringedNode)):
        return (_normalise_section(node.section_ref),)
    if isinstance(node, StatuteNode):
        refs = []
        if node.subsumes:
            refs.append(_normalise_section(node.subsumes))
        if node.amends:
            refs.append(_normalise_section(node.amends))
        return tuple(refs)
    return ()


def word_at_lsp_position(source: str, line: int, character: int) -> str:
    lines = source.splitlines()
    if line < 0 or line >= len(lines):
        return ""
    row = lines[line]
    if not row:
        return ""
    idx = min(max(character, 0), len(row) - 1)
    if not is_section_word_char(row[idx]) and idx > 0 and is_section_word_char(row[idx - 1]):
        idx -= 1
    if not is_section_word_char(row[idx]):
        return ""
    start = idx
    end = idx + 1
    while start > 0 and is_section_word_char(row[start - 1]):
        start -= 1
    while end < len(row) and is_section_word_char(row[end]):
        end += 1
    return row[start:end]


def is_section_word_char(char: str) -> bool:
    return char.isalnum() or char in "._"


def resolve_section_definition(
    server: YuhoLanguageServer,
    parsed: ParsedDocument,
    section: str,
) -> Optional[types.Location]:
    if parsed.ast is None:
        return None
    current = find_statute(parsed.ast, section)
    if current is not None and current.source_location is not None:
        return location_from_node(parsed.uri, current)

    imported = resolve_imported_section_definition(parsed, section)
    if imported is not None:
        return imported

    return resolve_library_section_definition(server, section)


def resolve_imported_section_definition(
    parsed: ParsedDocument,
    section: str,
) -> Optional[types.Location]:
    if parsed.ast is None:
        return None
    from_file = Path(parsed.file)
    resolver = ModuleResolver(search_paths=resolver_search_paths(from_file))
    for module, module_path in resolved_dependency_modules(resolver, parsed.ast, from_file):
        statute = find_statute(module, section)
        if statute is not None and statute.source_location is not None:
            return location_from_node(file_to_uri(module_path), statute)
    return None


def resolved_dependency_modules(
    resolver: ModuleResolver,
    ast: ModuleNode,
    from_file: Path,
) -> list[tuple[ModuleNode, Path]]:
    modules = []
    for import_node in ast.imports:
        try:
            module = resolver.resolve(import_node, from_file)
        except ModuleResolutionError:
            continue
        path = module_path(resolver, module)
        if path is not None:
            modules.append((module, path))
    for reference in ast.references:
        try:
            module = resolver.resolve_reference(reference, from_file)
        except ModuleResolutionError:
            continue
        path = module_path(resolver, module)
        if path is not None:
            modules.append((module, path))
    return modules


def resolver_search_paths(from_file: Path) -> list[Path]:
    paths = [Path.cwd()]
    if str(from_file):
        paths.append(from_file.resolve().parent)
    return paths


def module_path(resolver: ModuleResolver, module: ModuleNode) -> Optional[Path]:
    for path, cached in resolver.cached_modules.items():
        if cached is module:
            return Path(path)
    return None


def resolve_library_section_definition(
    server: YuhoLanguageServer,
    section: str,
) -> Optional[types.Location]:
    library_dir = DEFAULT_LIBRARY_DIR
    graph = server.reference_graph(library_dir)
    if graph is None or section not in graph.nodes:
        return None
    for path in library_section_candidates(library_dir, section):
        location = section_location_in_file(path, section)
        if location is not None:
            return location
    return None


def library_section_candidates(library_dir: Path, section: str) -> list[Path]:
    candidates = []
    direct = library_dir / f"s{section}" / "statute.yh"
    if direct.exists():
        candidates.append(direct)
    candidates.extend(sorted(library_dir.glob(f"s{section}_*/statute.yh")))
    return candidates


def section_location_in_file(path: Path, section: str) -> Optional[types.Location]:
    try:
        source = path.read_text(encoding="utf-8")
    except OSError:
        return None
    analysis = analyze_source(source, file=str(path), run_semantic=False)
    if analysis.ast is None:
        return None
    statute = find_statute(analysis.ast, section)
    if statute is None or statute.source_location is None:
        return None
    return location_from_node(file_to_uri(path), statute)


def find_statute(ast: ModuleNode, section: str) -> Optional[StatuteNode]:
    canonical = _normalise_section(section)
    for statute in ast.statutes:
        if _normalise_section(statute.section_number) == canonical:
            return statute
    return None


def location_from_node(uri: str, node: ASTNode) -> types.Location:
    assert node.source_location is not None
    return types.Location(uri=uri, range=location_to_range(node.source_location))


def location_contains_lsp_position(loc: SourceLocation, line: int, col: int) -> bool:
    starts_before = line > loc.line or (line == loc.line and col >= loc.col)
    ends_after = line < loc.end_line or (line == loc.end_line and col < loc.end_col)
    return starts_before and ends_after


def location_size(loc: Optional[SourceLocation]) -> tuple[int, int]:
    if loc is None:
        return (10**9, 10**9)
    return (loc.end_line - loc.line, loc.end_col - loc.col)


def location_to_range(loc: SourceLocation) -> types.Range:
    return types.Range(
        start=types.Position(line=max(loc.line - 1, 0), character=max(loc.col - 1, 0)),
        end=types.Position(
            line=max(loc.end_line - 1, 0),
            character=max(loc.end_col - 1, 0),
        ),
    )


def analysis_to_diagnostics(analysis: AnalysisResult) -> list[types.Diagnostic]:
    diagnostics = [diagnostic_from_payload(item) for item in analysis.diagnostics()]
    diagnostics.extend(
        lint_warning_to_diagnostic(analysis, warning) for warning in analysis.lint_warnings
    )
    return diagnostics


def diagnostic_from_payload(payload: dict) -> types.Diagnostic:
    line = payload.get("line") or 1
    column = payload.get("column") or 1
    end_line = payload.get("end_line") or line
    end_column = payload.get("end_column") or (column + 1)
    return types.Diagnostic(
        range=range_from_1_based(line, column, end_line, end_column),
        message=payload.get("message", "Yuho diagnostic"),
        severity=diagnostic_severity(payload.get("severity")),
        code=payload.get("error_code"),
        source=f"yuho:{payload.get('stage', 'analysis')}",
    )


def lint_warning_to_diagnostic(analysis: AnalysisResult, warning) -> types.Diagnostic:
    loc = statute_location(analysis.ast, warning.statute_section) if analysis.ast else None
    if loc is None:
        diagnostic_range = range_from_1_based(1, 1, 1, 2)
    else:
        diagnostic_range = location_to_range(loc)
    return types.Diagnostic(
        range=diagnostic_range,
        message=warning.message,
        severity=diagnostic_severity(warning.severity),
        code="statute_lint",
        source="yuho:lint",
    )


def statute_location(ast: Optional[ModuleNode], section: str) -> Optional[SourceLocation]:
    if ast is None:
        return None
    for statute in ast.statutes:
        if statute.section_number == section:
            return statute.source_location
    return None


def range_from_1_based(line: int, col: int, end_line: int, end_col: int) -> types.Range:
    return types.Range(
        start=types.Position(line=max(line - 1, 0), character=max(col - 1, 0)),
        end=types.Position(line=max(end_line - 1, 0), character=max(end_col - 1, 0)),
    )


def diagnostic_severity(severity: Optional[str]) -> types.DiagnosticSeverity:
    if severity == "error":
        return types.DiagnosticSeverity.Error
    if severity == "info":
        return types.DiagnosticSeverity.Information
    return types.DiagnosticSeverity.Warning


def hover_markdown(node: ASTNode) -> str:
    loc = node.source_location
    location = str(loc) if loc else "<unknown>"
    return f"**{type(node).__name__}**\n\n`{location}`"


def uri_to_file(uri: str) -> str:
    parsed = urlparse(uri)
    if parsed.scheme != "file":
        return uri
    path = unquote(parsed.path)
    if parsed.netloc:
        path = f"//{parsed.netloc}{path}"
    return str(Path(path))


def file_to_uri(path: Path) -> str:
    return path.resolve().as_uri()


def main() -> None:
    create_server().start_io()


if __name__ == "__main__":
    main()
