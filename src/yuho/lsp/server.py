"""
Yuho Language Server Protocol implementation using pygls.
"""

from typing import Dict, List, Optional, Any
import logging

try:
    from lsprotocol import types as lsp
    from pygls.server import LanguageServer
    from pygls.workspace import TextDocument
except ImportError:
    raise ImportError(
        "LSP dependencies not installed. Install with: pip install yuho[lsp]"
    )

from yuho.parser import Parser, SourceLocation
from yuho.parser.wrapper import ParseError, ParseResult
from yuho.ast import ASTBuilder, ModuleNode

logger = logging.getLogger(__name__)


# Yuho keywords for completion
YUHO_KEYWORDS = [
    "struct", "fn", "match", "case", "consequence", "pass", "return",
    "statute", "definitions", "elements", "penalty", "illustration",
    "import", "from", "actus_reus", "mens_rea", "circumstance",
    "imprisonment", "fine", "supplementary", "TRUE", "FALSE",
]

# Yuho built-in types
YUHO_TYPES = [
    "int", "float", "bool", "string", "money", "percent", "date", "duration", "void",
]


class DocumentState:
    """Cached state for a document."""

    def __init__(self, uri: str, source: str):
        self.uri = uri
        self.source = source
        self.parse_result: Optional[ParseResult] = None
        self.ast: Optional[ModuleNode] = None
        self.version = 0

    def update(self, source: str, version: int):
        """Update document source."""
        self.source = source
        self.version = version
        self._parse()

    def _parse(self):
        """Parse the document and build AST."""
        parser = Parser()
        self.parse_result = parser.parse(self.source, file=self.uri)

        if self.parse_result.is_valid:
            try:
                builder = ASTBuilder(self.source, self.uri)
                self.ast = builder.build(self.parse_result.root_node)
            except Exception as e:
                logger.warning(f"AST build error: {e}")
                self.ast = None
        else:
            self.ast = None


class YuhoLanguageServer(LanguageServer):
    """
    Language Server for Yuho .yh files.

    Provides:
    - Diagnostics from parsing and semantic analysis
    - Completion for keywords, types, and symbols
    - Hover information
    - Go to definition
    - Find references
    """

    def __init__(self):
        super().__init__(name="yuho-lsp", version="5.0.0")

        # Document cache
        self._documents: Dict[str, DocumentState] = {}

        # Register handlers
        self._register_handlers()

    def _register_handlers(self):
        """Register LSP request/notification handlers."""

        @self.feature(lsp.TEXT_DOCUMENT_DID_OPEN)
        def did_open(params: lsp.DidOpenTextDocumentParams):
            """Handle document open."""
            uri = params.text_document.uri
            text = params.text_document.text
            version = params.text_document.version

            doc_state = DocumentState(uri, text)
            doc_state.update(text, version)
            self._documents[uri] = doc_state

            self._publish_diagnostics(uri, doc_state)

        @self.feature(lsp.TEXT_DOCUMENT_DID_CHANGE)
        def did_change(params: lsp.DidChangeTextDocumentParams):
            """Handle document change."""
            uri = params.text_document.uri
            version = params.text_document.version

            if uri not in self._documents:
                return

            doc_state = self._documents[uri]

            # Apply changes (incremental)
            for change in params.content_changes:
                if isinstance(change, lsp.TextDocumentContentChangeEvent_Type1):
                    # Full document update
                    doc_state.update(change.text, version)
                else:
                    # Incremental update - for now, just use full text
                    doc_state.update(change.text, version)

            self._publish_diagnostics(uri, doc_state)

        @self.feature(lsp.TEXT_DOCUMENT_DID_CLOSE)
        def did_close(params: lsp.DidCloseTextDocumentParams):
            """Handle document close."""
            uri = params.text_document.uri
            if uri in self._documents:
                del self._documents[uri]

        @self.feature(lsp.TEXT_DOCUMENT_DID_SAVE)
        def did_save(params: lsp.DidSaveTextDocumentParams):
            """Handle document save."""
            # Re-parse on save if text included
            if params.text:
                uri = params.text_document.uri
                if uri in self._documents:
                    self._documents[uri].update(params.text, self._documents[uri].version + 1)
                    self._publish_diagnostics(uri, self._documents[uri])

        @self.feature(lsp.TEXT_DOCUMENT_COMPLETION)
        def completion(params: lsp.CompletionParams) -> lsp.CompletionList:
            """Provide code completion."""
            uri = params.text_document.uri
            position = params.position

            return self._get_completions(uri, position)

        @self.feature(lsp.TEXT_DOCUMENT_HOVER)
        def hover(params: lsp.HoverParams) -> Optional[lsp.Hover]:
            """Provide hover information."""
            uri = params.text_document.uri
            position = params.position

            return self._get_hover(uri, position)

        @self.feature(lsp.TEXT_DOCUMENT_DEFINITION)
        def definition(params: lsp.DefinitionParams) -> Optional[lsp.Location]:
            """Go to definition."""
            uri = params.text_document.uri
            position = params.position

            return self._get_definition(uri, position)

        @self.feature(lsp.TEXT_DOCUMENT_REFERENCES)
        def references(params: lsp.ReferenceParams) -> List[lsp.Location]:
            """Find all references."""
            uri = params.text_document.uri
            position = params.position

            return self._get_references(uri, position)

        @self.feature(lsp.TEXT_DOCUMENT_DOCUMENT_SYMBOL)
        def document_symbol(params: lsp.DocumentSymbolParams) -> List[lsp.DocumentSymbol]:
            """Get document symbols."""
            uri = params.text_document.uri

            return self._get_document_symbols(uri)

        @self.feature(lsp.TEXT_DOCUMENT_FORMATTING)
        def formatting(params: lsp.DocumentFormattingParams) -> List[lsp.TextEdit]:
            """Format document."""
            uri = params.text_document.uri

            return self._format_document(uri)

    def _publish_diagnostics(self, uri: str, doc_state: DocumentState):
        """Publish diagnostics for a document."""
        diagnostics: List[lsp.Diagnostic] = []

        # Parser errors
        if doc_state.parse_result and doc_state.parse_result.errors:
            for error in doc_state.parse_result.errors:
                diag = self._error_to_diagnostic(error)
                diagnostics.append(diag)

        # Semantic errors (TODO: implement type checker)

        self.publish_diagnostics(uri, diagnostics)

    def _error_to_diagnostic(self, error: ParseError) -> lsp.Diagnostic:
        """Convert ParseError to LSP Diagnostic."""
        loc = error.location

        return lsp.Diagnostic(
            range=lsp.Range(
                start=lsp.Position(line=loc.line - 1, character=loc.col - 1),
                end=lsp.Position(line=loc.end_line - 1, character=loc.end_col - 1),
            ),
            message=error.message,
            severity=lsp.DiagnosticSeverity.Error,
            source="yuho",
        )

    def _get_completions(self, uri: str, position: lsp.Position) -> lsp.CompletionList:
        """Get completion items for position."""
        items: List[lsp.CompletionItem] = []

        # Keywords
        for kw in YUHO_KEYWORDS:
            items.append(lsp.CompletionItem(
                label=kw,
                kind=lsp.CompletionItemKind.Keyword,
                detail="keyword",
            ))

        # Built-in types
        for typ in YUHO_TYPES:
            items.append(lsp.CompletionItem(
                label=typ,
                kind=lsp.CompletionItemKind.TypeParameter,
                detail="built-in type",
            ))

        # Symbols from current document
        doc_state = self._documents.get(uri)
        if doc_state and doc_state.ast:
            # Struct names
            for struct in doc_state.ast.type_defs:
                items.append(lsp.CompletionItem(
                    label=struct.name,
                    kind=lsp.CompletionItemKind.Struct,
                    detail=f"struct {struct.name}",
                ))

            # Function names
            for func in doc_state.ast.function_defs:
                params = ", ".join(p.name for p in func.params)
                items.append(lsp.CompletionItem(
                    label=func.name,
                    kind=lsp.CompletionItemKind.Function,
                    detail=f"fn {func.name}({params})",
                ))

            # Statute sections
            for statute in doc_state.ast.statutes:
                title = statute.title.value if statute.title else ""
                items.append(lsp.CompletionItem(
                    label=f"S{statute.section_number}",
                    kind=lsp.CompletionItemKind.Module,
                    detail=f"statute {statute.section_number}: {title}",
                ))

        return lsp.CompletionList(is_incomplete=False, items=items)

    def _get_hover(self, uri: str, position: lsp.Position) -> Optional[lsp.Hover]:
        """Get hover information for position."""
        doc_state = self._documents.get(uri)
        if not doc_state or not doc_state.ast:
            return None

        # TODO: Implement proper position-to-node lookup
        # For now, return None
        return None

    def _get_definition(self, uri: str, position: lsp.Position) -> Optional[lsp.Location]:
        """Get definition location for identifier at position."""
        doc_state = self._documents.get(uri)
        if not doc_state or not doc_state.ast:
            return None

        # TODO: Implement proper definition lookup
        return None

    def _get_references(self, uri: str, position: lsp.Position) -> List[lsp.Location]:
        """Get all references to symbol at position."""
        doc_state = self._documents.get(uri)
        if not doc_state or not doc_state.ast:
            return []

        # TODO: Implement reference finding
        return []

    def _get_document_symbols(self, uri: str) -> List[lsp.DocumentSymbol]:
        """Get document symbol hierarchy."""
        doc_state = self._documents.get(uri)
        if not doc_state or not doc_state.ast:
            return []

        symbols: List[lsp.DocumentSymbol] = []

        # Structs
        for struct in doc_state.ast.type_defs:
            loc = struct.source_location
            if loc:
                symbols.append(lsp.DocumentSymbol(
                    name=struct.name,
                    kind=lsp.SymbolKind.Struct,
                    range=self._loc_to_range(loc),
                    selection_range=self._loc_to_range(loc),
                ))

        # Functions
        for func in doc_state.ast.function_defs:
            loc = func.source_location
            if loc:
                symbols.append(lsp.DocumentSymbol(
                    name=func.name,
                    kind=lsp.SymbolKind.Function,
                    range=self._loc_to_range(loc),
                    selection_range=self._loc_to_range(loc),
                ))

        # Statutes
        for statute in doc_state.ast.statutes:
            loc = statute.source_location
            if loc:
                title = statute.title.value if statute.title else statute.section_number
                symbols.append(lsp.DocumentSymbol(
                    name=f"S{statute.section_number}: {title}",
                    kind=lsp.SymbolKind.Module,
                    range=self._loc_to_range(loc),
                    selection_range=self._loc_to_range(loc),
                ))

        return symbols

    def _format_document(self, uri: str) -> List[lsp.TextEdit]:
        """Format the entire document."""
        doc_state = self._documents.get(uri)
        if not doc_state or not doc_state.ast:
            return []

        # Use the formatter from CLI
        try:
            from yuho.cli.commands.fmt import _format_module
            formatted = _format_module(doc_state.ast)

            # Create edit replacing entire document
            lines = doc_state.source.splitlines()
            return [lsp.TextEdit(
                range=lsp.Range(
                    start=lsp.Position(line=0, character=0),
                    end=lsp.Position(line=len(lines), character=0),
                ),
                new_text=formatted,
            )]
        except Exception as e:
            logger.warning(f"Format error: {e}")
            return []

    def _loc_to_range(self, loc: SourceLocation) -> lsp.Range:
        """Convert SourceLocation to LSP Range."""
        return lsp.Range(
            start=lsp.Position(line=loc.line - 1, character=loc.col - 1),
            end=lsp.Position(line=loc.end_line - 1, character=loc.end_col - 1),
        )

    def start_io(self):
        """Start the server using stdio."""
        self.start_io()

    def start_tcp(self, host: str, port: int):
        """Start the server on TCP."""
        self.start_tcp(host, port)
