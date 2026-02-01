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
        """Get hover information for position showing type info and doc-comments."""
        doc_state = self._documents.get(uri)
        if not doc_state:
            return None
        
        # Get word at position
        word = self._get_word_at_position(doc_state.source, position)
        if not word:
            return None
        
        hover_content: List[str] = []
        
        # Check if it's a keyword
        if word in YUHO_KEYWORDS:
            hover_content.append(f"**keyword** `{word}`")
            keyword_docs = {
                "struct": "Defines a structured type with named fields.",
                "fn": "Defines a function.",
                "match": "Pattern matching expression.",
                "case": "Case arm in a match expression.",
                "statute": "Defines a legal statute with elements and penalties.",
                "elements": "Section containing the elements of an offense.",
                "penalty": "Section specifying the punishment for an offense.",
                "actus_reus": "Physical/conduct element of an offense (guilty act).",
                "mens_rea": "Mental element of an offense (guilty mind).",
                "circumstance": "Circumstantial element required for the offense.",
            }
            if word in keyword_docs:
                hover_content.append(keyword_docs[word])
        
        # Check if it's a built-in type
        elif word in YUHO_TYPES:
            hover_content.append(f"**type** `{word}`")
            type_docs = {
                "int": "Integer number type (whole numbers).",
                "float": "Floating-point number type (decimals).",
                "bool": "Boolean type: TRUE or FALSE.",
                "string": "Text string type.",
                "money": "Monetary amount with currency (e.g., $1000.00 SGD).",
                "percent": "Percentage value (0-100%).",
                "date": "Calendar date (YYYY-MM-DD).",
                "duration": "Time duration (years, months, days, etc.).",
                "void": "No value type (for procedures).",
            }
            if word in type_docs:
                hover_content.append(type_docs[word])
        
        # Check AST for user-defined symbols
        elif doc_state.ast:
            # Check structs
            for struct in doc_state.ast.type_defs:
                if struct.name == word:
                    fields = ", ".join(f"{f.name}: {self._type_to_str(f.type_annotation)}" 
                                       for f in struct.fields)
                    hover_content.append(f"```yuho\nstruct {struct.name} {{\n  {fields}\n}}\n```")
                    break
            
            # Check functions
            for func in doc_state.ast.function_defs:
                if func.name == word:
                    params = ", ".join(f"{p.name}: {self._type_to_str(p.type_annotation)}" 
                                      for p in func.params)
                    ret = f" -> {self._type_to_str(func.return_type)}" if func.return_type else ""
                    hover_content.append(f"```yuho\nfn {func.name}({params}){ret}\n```")
                    # TODO: Add doc-comment if available
                    break
            
            # Check statutes
            for statute in doc_state.ast.statutes:
                if statute.section_number == word or f"S{statute.section_number}" == word:
                    title = statute.title.value if statute.title else "Untitled"
                    hover_content.append(f"**Statute Section {statute.section_number}**: {title}")
                    
                    # Add element summary
                    if statute.elements:
                        hover_content.append("\n**Elements:**")
                        for elem in statute.elements:
                            hover_content.append(f"- {elem.element_type}: {elem.name}")
                    
                    # Add penalty summary
                    if statute.penalty:
                        hover_content.append("\n**Penalty:**")
                        if statute.penalty.imprisonment_max:
                            hover_content.append(f"- Imprisonment: up to {statute.penalty.imprisonment_max}")
                        if statute.penalty.fine_max:
                            hover_content.append(f"- Fine: up to {statute.penalty.fine_max}")
                    break
        
        if not hover_content:
            return None
        
        return lsp.Hover(
            contents=lsp.MarkupContent(
                kind=lsp.MarkupKind.Markdown,
                value="\n".join(hover_content),
            )
        )

    def _get_definition(self, uri: str, position: lsp.Position) -> Optional[lsp.Location]:
        """Get definition location for identifier at position."""
        doc_state = self._documents.get(uri)
        if not doc_state:
            return None
        
        word = self._get_word_at_position(doc_state.source, position)
        if not word:
            return None
        
        # Check AST for definitions
        if doc_state.ast:
            # Check struct definitions
            for struct in doc_state.ast.type_defs:
                if struct.name == word and struct.source_location:
                    return lsp.Location(
                        uri=uri,
                        range=self._loc_to_range(struct.source_location),
                    )
            
            # Check function definitions
            for func in doc_state.ast.function_defs:
                if func.name == word and func.source_location:
                    return lsp.Location(
                        uri=uri,
                        range=self._loc_to_range(func.source_location),
                    )
            
            # Check statute definitions (by section number)
            for statute in doc_state.ast.statutes:
                if (statute.section_number == word or 
                    f"S{statute.section_number}" == word) and statute.source_location:
                    return lsp.Location(
                        uri=uri,
                        range=self._loc_to_range(statute.source_location),
                    )
            
            # Check imports - navigate to the .yh file
            for imp in doc_state.ast.imports:
                # If user clicked on an imported name
                if imp.imported_names and word in imp.imported_names:
                    # Try to resolve the import path
                    import_location = self._resolve_import_path(uri, imp.path)
                    if import_location:
                        return lsp.Location(
                            uri=import_location,
                            range=lsp.Range(
                                start=lsp.Position(line=0, character=0),
                                end=lsp.Position(line=0, character=0),
                            ),
                        )
        
        return None

    def _get_references(self, uri: str, position: lsp.Position) -> List[lsp.Location]:
        """Get all references to symbol at position."""
        doc_state = self._documents.get(uri)
        if not doc_state:
            return []
        
        word = self._get_word_at_position(doc_state.source, position)
        if not word:
            return []
        
        locations: List[lsp.Location] = []
        
        # Find all occurrences of the word in the source
        lines = doc_state.source.splitlines()
        for line_num, line in enumerate(lines):
            col = 0
            while True:
                pos = line.find(word, col)
                if pos == -1:
                    break
                
                # Check if it's a whole word (not part of a larger identifier)
                before_ok = (pos == 0 or not (line[pos - 1].isalnum() or line[pos - 1] == '_'))
                after_pos = pos + len(word)
                after_ok = (after_pos >= len(line) or not (line[after_pos].isalnum() or line[after_pos] == '_'))
                
                if before_ok and after_ok:
                    locations.append(lsp.Location(
                        uri=uri,
                        range=lsp.Range(
                            start=lsp.Position(line=line_num, character=pos),
                            end=lsp.Position(line=line_num, character=pos + len(word)),
                        ),
                    ))
                
                col = after_pos
        
        return locations

    def _get_word_at_position(self, source: str, position: lsp.Position) -> Optional[str]:
        """Extract the word/identifier at the given position."""
        lines = source.splitlines()
        if position.line >= len(lines):
            return None
        
        line = lines[position.line]
        if position.character >= len(line):
            return None
        
        # Find word boundaries
        start = position.character
        end = position.character
        
        # Expand backwards
        while start > 0 and (line[start - 1].isalnum() or line[start - 1] == '_'):
            start -= 1
        
        # Expand forwards
        while end < len(line) and (line[end].isalnum() or line[end] == '_'):
            end += 1
        
        if start == end:
            return None
        
        return line[start:end]

    def _type_to_str(self, type_node) -> str:
        """Convert a type node to a string representation."""
        if type_node is None:
            return "unknown"
        
        from yuho.ast import nodes
        if isinstance(type_node, nodes.BuiltinType):
            return type_node.name
        elif isinstance(type_node, nodes.NamedType):
            return type_node.name
        elif isinstance(type_node, nodes.OptionalType):
            return f"{self._type_to_str(type_node.inner)}?"
        elif isinstance(type_node, nodes.ArrayType):
            return f"[{self._type_to_str(type_node.element_type)}]"
        elif isinstance(type_node, nodes.GenericType):
            args = ", ".join(self._type_to_str(a) for a in type_node.type_args)
            return f"{type_node.base}<{args}>"
        return str(type_node)

    def _resolve_import_path(self, current_uri: str, import_path: str) -> Optional[str]:
        """Resolve an import path to a file URI."""
        import os
        from urllib.parse import urlparse, unquote
        
        # Parse current URI to get directory
        parsed = urlparse(current_uri)
        current_path = unquote(parsed.path)
        current_dir = os.path.dirname(current_path)
        
        # Try different resolution strategies
        candidates = [
            os.path.join(current_dir, import_path),
            os.path.join(current_dir, f"{import_path}.yh"),
            os.path.join(current_dir, "lib", import_path),
            os.path.join(current_dir, "lib", f"{import_path}.yh"),
        ]
        
        for candidate in candidates:
            if os.path.isfile(candidate):
                return f"file://{candidate}"
        
        return None


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
