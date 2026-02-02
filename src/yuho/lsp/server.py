"""
Yuho Language Server Protocol implementation using pygls.
"""

from typing import Dict, List, Optional, Any, Tuple
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
        
        # Workspace folders for cross-file operations
        self._workspace_folders: List[str] = []
        
        # Symbol index for workspace-wide lookups
        self._symbol_index: Dict[str, Dict[str, Any]] = {}

        # Register handlers
        self._register_handlers()
    
    def _index_workspace_symbols(self, folder_uri: str) -> None:
        """Index all Yuho files in workspace folder."""
        from pathlib import Path
        from urllib.parse import urlparse, unquote
        
        parsed = urlparse(folder_uri)
        folder_path = Path(unquote(parsed.path))
        
        if not folder_path.exists():
            return
        
        for yh_file in folder_path.rglob("*.yh"):
            file_uri = f"file://{yh_file}"
            if file_uri not in self._documents:
                try:
                    content = yh_file.read_text()
                    doc_state = DocumentState(file_uri, content)
                    doc_state._parse()
                    
                    # Index symbols
                    if doc_state.ast:
                        for struct in doc_state.ast.type_defs:
                            self._symbol_index[struct.name] = {
                                "kind": "struct",
                                "uri": file_uri,
                                "location": struct.source_location,
                            }
                        for func in doc_state.ast.function_defs:
                            self._symbol_index[func.name] = {
                                "kind": "function", 
                                "uri": file_uri,
                                "location": func.source_location,
                            }
                except Exception:
                    pass


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

        @self.feature(lsp.TEXT_DOCUMENT_RANGE_FORMATTING)
        def range_formatting(params: lsp.DocumentRangeFormattingParams) -> List[lsp.TextEdit]:
            """Format a selection of the document."""
            uri = params.text_document.uri
            range_ = params.range

            return self._format_range(uri, range_)

        @self.feature(lsp.TEXT_DOCUMENT_RENAME)
        def rename(params: lsp.RenameParams) -> Optional[lsp.WorkspaceEdit]:
            """Rename symbol across workspace."""
            uri = params.text_document.uri
            position = params.position
            new_name = params.new_name

            return self._rename_symbol(uri, position, new_name)

        @self.feature(lsp.TEXT_DOCUMENT_PREPARE_RENAME)
        def prepare_rename(params: lsp.PrepareRenameParams) -> Optional[lsp.PrepareRenameResult_Type1]:
            """Check if rename is valid at position."""
            uri = params.text_document.uri
            position = params.position

            return self._prepare_rename(uri, position)

        @self.feature(lsp.WORKSPACE_SYMBOL)
        def workspace_symbol(params: lsp.WorkspaceSymbolParams) -> List[lsp.SymbolInformation]:
            """Search for symbols across workspace."""
            query = params.query

            return self._workspace_symbol_search(query)

        @self.feature(lsp.TEXT_DOCUMENT_CODE_ACTION)
        def code_action(params: lsp.CodeActionParams) -> List[lsp.CodeAction]:
            """Provide quick fixes and refactorings."""
            uri = params.text_document.uri
            range_ = params.range
            context = params.context

            return self._get_code_actions(uri, range_, context)

        @self.feature(lsp.TEXT_DOCUMENT_CODE_LENS)
        def code_lens(params: lsp.CodeLensParams) -> List[lsp.CodeLens]:
            """Provide code lens annotations."""
            uri = params.text_document.uri

            return self._get_code_lenses(uri)

        @self.feature(lsp.TEXT_DOCUMENT_FOLDING_RANGE)
        def folding_range(params: lsp.FoldingRangeParams) -> List[lsp.FoldingRange]:
            """Provide folding ranges for code folding."""
            uri = params.text_document.uri

            return self._get_folding_ranges(uri)

        @self.feature(lsp.WORKSPACE_DID_CHANGE_CONFIGURATION)
        def did_change_configuration(params: lsp.DidChangeConfigurationParams):
            """Handle configuration changes."""
            settings = params.settings
            self._update_configuration(settings)

        @self.feature(
            lsp.TEXT_DOCUMENT_SEMANTIC_TOKENS_FULL,
            lsp.SemanticTokensOptions(
                legend=lsp.SemanticTokensLegend(
                    token_types=[
                        "namespace", "type", "class", "enum", "interface",
                        "struct", "typeParameter", "parameter", "variable",
                        "property", "enumMember", "event", "function", "method",
                        "macro", "keyword", "modifier", "comment", "string",
                        "number", "regexp", "operator",
                    ],
                    token_modifiers=[
                        "declaration", "definition", "readonly", "static",
                        "deprecated", "abstract", "async", "modification",
                        "documentation", "defaultLibrary",
                    ],
                ),
                full=True,
            ),
        )
        def semantic_tokens_full(params: lsp.SemanticTokensParams) -> Optional[lsp.SemanticTokens]:
            """Provide semantic tokens for enhanced syntax highlighting."""
            uri = params.text_document.uri

            return self._get_semantic_tokens(uri)

        @self.feature(lsp.TEXT_DOCUMENT_INLAY_HINT)
        def inlay_hint(params: lsp.InlayHintParams) -> List[lsp.InlayHint]:
            """Provide inlay hints showing inferred types inline."""
            uri = params.text_document.uri
            range_ = params.range

            return self._get_inlay_hints(uri, range_)

        @self.feature(lsp.TEXT_DOCUMENT_SIGNATURE_HELP)
        def signature_help(params: lsp.SignatureHelpParams) -> Optional[lsp.SignatureHelp]:
            """Provide signature help for function parameters."""
            uri = params.text_document.uri
            position = params.position

            return self._get_signature_help(uri, position)

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

    def _get_signature_help(
        self, uri: str, position: lsp.Position
    ) -> Optional[lsp.SignatureHelp]:
        """Get signature help for function call at position."""
        doc_state = self._documents.get(uri)
        if not doc_state:
            return None
        
        # Get the line up to cursor
        lines = doc_state.source.splitlines()
        if position.line >= len(lines):
            return None
        
        line = lines[position.line]
        line_to_cursor = line[:position.character]
        
        # Find function call context
        func_name, param_index = self._parse_function_call_context(line_to_cursor)
        if not func_name:
            return None
        
        # Find the function definition
        if doc_state.ast:
            for func in doc_state.ast.function_defs:
                if func.name == func_name:
                    return self._build_signature_help(func, param_index)
        
        return None
    
    def _parse_function_call_context(self, line_to_cursor: str) -> tuple:
        """
        Parse the line to find function call context.
        
        Returns:
            Tuple of (function_name, parameter_index) or (None, 0)
        """
        # Find the last unclosed parenthesis
        paren_depth = 0
        func_end = -1
        
        for i in range(len(line_to_cursor) - 1, -1, -1):
            char = line_to_cursor[i]
            if char == ')':
                paren_depth += 1
            elif char == '(':
                if paren_depth == 0:
                    func_end = i
                    break
                paren_depth -= 1
        
        if func_end < 0:
            return (None, 0)
        
        # Extract function name before the opening paren
        func_name_part = line_to_cursor[:func_end].rstrip()
        
        # Find start of identifier
        func_start = len(func_name_part)
        while func_start > 0 and (func_name_part[func_start - 1].isalnum() or 
                                   func_name_part[func_start - 1] == '_'):
            func_start -= 1
        
        func_name = func_name_part[func_start:]
        if not func_name or not func_name[0].isalpha():
            return (None, 0)
        
        # Count commas to determine parameter index
        args_part = line_to_cursor[func_end + 1:]
        param_index = 0
        paren_depth = 0
        
        for char in args_part:
            if char == '(':
                paren_depth += 1
            elif char == ')':
                paren_depth -= 1
            elif char == ',' and paren_depth == 0:
                param_index += 1
        
        return (func_name, param_index)
    
    def _build_signature_help(self, func, active_param: int) -> lsp.SignatureHelp:
        """Build SignatureHelp from function definition."""
        # Build parameter info
        parameters = []
        params_str_parts = []
        
        for param in func.params:
            type_str = self._type_to_str(param.type_annotation)
            param_str = f"{param.name}: {type_str}"
            params_str_parts.append(param_str)
            
            parameters.append(lsp.ParameterInformation(
                label=param_str,
                documentation=f"Parameter `{param.name}` of type `{type_str}`",
            ))
        
        # Build full signature string
        params_str = ", ".join(params_str_parts)
        ret_str = ""
        if func.return_type:
            ret_str = f" -> {self._type_to_str(func.return_type)}"
        
        signature_str = f"fn {func.name}({params_str}){ret_str}"
        
        signature = lsp.SignatureInformation(
            label=signature_str,
            parameters=parameters,
            active_parameter=min(active_param, len(parameters) - 1) if parameters else None,
        )
        
        return lsp.SignatureHelp(
            signatures=[signature],
            active_signature=0,
            active_parameter=active_param,
        )

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

    def _format_range(self, uri: str, range_: lsp.Range) -> List[lsp.TextEdit]:
        """Format a range of the document."""
        doc_state = self._documents.get(uri)
        if not doc_state:
            return []

        # For now, format the entire document - proper range formatting
        # would require parsing and reformatting just the selection
        return self._format_document(uri)

    def _rename_symbol(
        self, uri: str, position: lsp.Position, new_name: str
    ) -> Optional[lsp.WorkspaceEdit]:
        """Rename symbol at position across all documents."""
        doc_state = self._documents.get(uri)
        if not doc_state:
            return None

        word = self._get_word_at_position(doc_state.source, position)
        if not word:
            return None

        # Validate new name is a valid identifier
        if not new_name or not new_name[0].isalpha() and new_name[0] != '_':
            return None
        if not all(c.isalnum() or c == '_' for c in new_name):
            return None

        # Check if this is a renameable symbol (struct, function, variable, statute)
        is_renameable = False
        if doc_state.ast:
            for struct in doc_state.ast.type_defs:
                if struct.name == word:
                    is_renameable = True
                    break
            for func in doc_state.ast.function_defs:
                if func.name == word:
                    is_renameable = True
                    break

        if not is_renameable:
            return None

        # Collect edits across all open documents
        changes: Dict[str, List[lsp.TextEdit]] = {}

        for doc_uri, doc in self._documents.items():
            edits = self._find_and_replace_symbol(doc, word, new_name)
            if edits:
                changes[doc_uri] = edits
        
        # Also search workspace files not currently open
        for folder_uri in self._workspace_folders:
            self._search_workspace_for_symbol(folder_uri, word, new_name, changes)

        if not changes:
            return None

        return lsp.WorkspaceEdit(changes=changes)
    
    def _search_workspace_for_symbol(
        self,
        folder_uri: str,
        old_name: str,
        new_name: str,
        changes: Dict[str, List[lsp.TextEdit]],
    ) -> None:
        """Search workspace folder for symbol occurrences."""
        from pathlib import Path
        from urllib.parse import urlparse, unquote
        
        parsed = urlparse(folder_uri)
        folder_path = Path(unquote(parsed.path))
        
        if not folder_path.exists():
            return
        
        for yh_file in folder_path.rglob("*.yh"):
            file_uri = f"file://{yh_file}"
            
            # Skip already-open documents
            if file_uri in self._documents:
                continue
            
            try:
                content = yh_file.read_text()
                
                # Quick check if symbol appears in file
                if old_name not in content:
                    continue
                
                # Create temporary doc state for editing
                temp_doc = DocumentState(file_uri, content)
                edits = self._find_and_replace_symbol(temp_doc, old_name, new_name)
                
                if edits:
                    changes[file_uri] = edits
                    
            except Exception:
                pass


    def _find_and_replace_symbol(
        self, doc_state: DocumentState, old_name: str, new_name: str
    ) -> List[lsp.TextEdit]:
        """Find all occurrences of symbol and create edits to replace with new name."""
        edits: List[lsp.TextEdit] = []
        lines = doc_state.source.splitlines()

        for line_num, line in enumerate(lines):
            col = 0
            while True:
                pos = line.find(old_name, col)
                if pos == -1:
                    break

                # Check if it's a whole word
                before_ok = pos == 0 or not (line[pos - 1].isalnum() or line[pos - 1] == '_')
                after_pos = pos + len(old_name)
                after_ok = after_pos >= len(line) or not (line[after_pos].isalnum() or line[after_pos] == '_')

                if before_ok and after_ok:
                    edits.append(lsp.TextEdit(
                        range=lsp.Range(
                            start=lsp.Position(line=line_num, character=pos),
                            end=lsp.Position(line=line_num, character=after_pos),
                        ),
                        new_text=new_name,
                    ))

                col = after_pos

        return edits

    def _prepare_rename(
        self, uri: str, position: lsp.Position
    ) -> Optional[lsp.PrepareRenameResult_Type1]:
        """Check if symbol at position can be renamed."""
        doc_state = self._documents.get(uri)
        if not doc_state:
            return None

        word = self._get_word_at_position(doc_state.source, position)
        if not word:
            return None

        # Check if this is a renameable symbol
        is_renameable = False
        if doc_state.ast:
            for struct in doc_state.ast.type_defs:
                if struct.name == word:
                    is_renameable = True
                    break
            for func in doc_state.ast.function_defs:
                if func.name == word:
                    is_renameable = True
                    break

        if not is_renameable:
            return None

        # Find the range of the word
        lines = doc_state.source.splitlines()
        line = lines[position.line] if position.line < len(lines) else ""
        start = position.character
        end = position.character

        while start > 0 and (line[start - 1].isalnum() or line[start - 1] == '_'):
            start -= 1
        while end < len(line) and (line[end].isalnum() or line[end] == '_'):
            end += 1

        return lsp.PrepareRenameResult_Type1(
            range=lsp.Range(
                start=lsp.Position(line=position.line, character=start),
                end=lsp.Position(line=position.line, character=end),
            ),
            placeholder=word,
        )

    def _workspace_symbol_search(self, query: str) -> List[lsp.SymbolInformation]:
        """Search for symbols matching query across all documents."""
        results: List[lsp.SymbolInformation] = []
        query_lower = query.lower()

        for uri, doc_state in self._documents.items():
            if not doc_state.ast:
                continue

            # Search structs
            for struct in doc_state.ast.type_defs:
                if query_lower in struct.name.lower():
                    loc = struct.source_location
                    if loc:
                        results.append(lsp.SymbolInformation(
                            name=struct.name,
                            kind=lsp.SymbolKind.Struct,
                            location=lsp.Location(
                                uri=uri,
                                range=self._loc_to_range(loc),
                            ),
                        ))

            # Search functions
            for func in doc_state.ast.function_defs:
                if query_lower in func.name.lower():
                    loc = func.source_location
                    if loc:
                        results.append(lsp.SymbolInformation(
                            name=func.name,
                            kind=lsp.SymbolKind.Function,
                            location=lsp.Location(
                                uri=uri,
                                range=self._loc_to_range(loc),
                            ),
                        ))

            # Search statutes
            for statute in doc_state.ast.statutes:
                title = statute.title.value if statute.title else ""
                if query_lower in f"s{statute.section_number}".lower() or query_lower in title.lower():
                    loc = statute.source_location
                    if loc:
                        results.append(lsp.SymbolInformation(
                            name=f"S{statute.section_number}: {title}",
                            kind=lsp.SymbolKind.Module,
                            location=lsp.Location(
                                uri=uri,
                                range=self._loc_to_range(loc),
                            ),
                        ))

        return results

    def _get_code_actions(
        self, uri: str, range_: lsp.Range, context: lsp.CodeActionContext
    ) -> List[lsp.CodeAction]:
        """Provide code actions (quick fixes, refactorings)."""
        actions: List[lsp.CodeAction] = []
        doc_state = self._documents.get(uri)

        if not doc_state:
            return actions

        # Check diagnostics for quick fixes
        for diagnostic in context.diagnostics:
            msg = diagnostic.message.lower()
            
            # Fix for undefined symbol
            if "undefined" in msg:
                word = self._extract_undefined_symbol(diagnostic.message)
                if word:
                    actions.append(lsp.CodeAction(
                        title=f"Add import for '{word}'",
                        kind=lsp.CodeActionKind.QuickFix,
                        diagnostics=[diagnostic],
                        edit=lsp.WorkspaceEdit(
                            changes={
                                uri: [lsp.TextEdit(
                                    range=lsp.Range(
                                        start=lsp.Position(line=0, character=0),
                                        end=lsp.Position(line=0, character=0),
                                    ),
                                    new_text=f"import {word}\n",
                                )],
                            },
                        ),
                    ))
            
            # Fix for missing match arms (non-exhaustive match)
            if "non-exhaustive" in msg or "missing" in msg and "arm" in msg:
                actions.append(lsp.CodeAction(
                    title="Add wildcard pattern '_ =>'",
                    kind=lsp.CodeActionKind.QuickFix,
                    diagnostics=[diagnostic],
                    edit=lsp.WorkspaceEdit(
                        changes={
                            uri: [lsp.TextEdit(
                                range=lsp.Range(
                                    start=lsp.Position(
                                        line=diagnostic.range.end.line,
                                        character=0,
                                    ),
                                    end=lsp.Position(
                                        line=diagnostic.range.end.line,
                                        character=0,
                                    ),
                                ),
                                new_text="        _ => pass\n",
                            )],
                        },
                    ),
                ))
            
            # Fix for type mismatch
            if "type mismatch" in msg or "expected" in msg and "got" in msg:
                # Try to suggest conversion
                import re
                match = re.search(r"expected\s+(\w+).*got\s+(\w+)", msg)
                if match:
                    expected, got = match.groups()
                    conversion = self._get_type_conversion(got, expected)
                    if conversion:
                        actions.append(lsp.CodeAction(
                            title=f"Convert to {expected}",
                            kind=lsp.CodeActionKind.QuickFix,
                            diagnostics=[diagnostic],
                            # Note: Full edit would wrap expression in conversion
                        ))
            
            # Fix for missing struct fields
            if "missing field" in msg:
                import re
                field_match = re.search(r"missing field[s]?\s*['\"]?(\w+)", msg)
                if field_match:
                    field = field_match.group(1)
                    actions.append(lsp.CodeAction(
                        title=f"Add missing field '{field}'",
                        kind=lsp.CodeActionKind.QuickFix,
                        diagnostics=[diagnostic],
                        edit=lsp.WorkspaceEdit(
                            changes={
                                uri: [lsp.TextEdit(
                                    range=lsp.Range(
                                        start=diagnostic.range.end,
                                        end=diagnostic.range.end,
                                    ),
                                    new_text=f", {field}: TODO",
                                )],
                            },
                        ),
                    ))
            
            # Fix for enum variant typos (unknown variant)
            if "unknown variant" in msg or "invalid variant" in msg:
                import re
                variant_match = re.search(r"variant[:\s]+['\"]?(\w+)['\"]?", msg)
                if variant_match:
                    typo = variant_match.group(1)
                    # Find similar variants using fuzzy matching
                    suggestions = self._find_similar_variants(doc_state, typo)
                    for suggestion in suggestions[:3]:  # Top 3 suggestions
                        actions.append(lsp.CodeAction(
                            title=f"Change to '{suggestion}'",
                            kind=lsp.CodeActionKind.QuickFix,
                            diagnostics=[diagnostic],
                            edit=lsp.WorkspaceEdit(
                                changes={
                                    uri: [lsp.TextEdit(
                                        range=diagnostic.range,
                                        new_text=suggestion,
                                    )],
                                },
                            ),
                        ))
        

        # Context-based refactorings (not tied to diagnostics)
        if doc_state.ast:
            line_text = self._get_line_text(doc_state.source, range_.start.line)

            # If inside a match expression, offer to add case
            if "match" in line_text.lower():
                actions.append(lsp.CodeAction(
                    title="Add match case",
                    kind=lsp.CodeActionKind.Refactor,
                    edit=lsp.WorkspaceEdit(
                        changes={
                            uri: [lsp.TextEdit(
                                range=lsp.Range(
                                    start=lsp.Position(line=range_.end.line + 1, character=0),
                                    end=lsp.Position(line=range_.end.line + 1, character=0),
                                ),
                                new_text="    case TODO => pass\n",
                            )],
                        },
                    ),
                ))

            # Extract match arm to named pattern
            pattern_info = self._extract_match_arm_pattern(doc_state, range_)
            if pattern_info:
                pattern_text, pattern_range = pattern_info
                suggested_name = self._suggest_pattern_name(pattern_text, doc_state)
                actions.append(lsp.CodeAction(
                    title=f"Extract to named pattern '{suggested_name}'",
                    kind=lsp.CodeActionKind.RefactorExtract,
                    edit=lsp.WorkspaceEdit(
                        changes={
                            uri: [
                                # Add pattern definition at top
                                lsp.TextEdit(
                                    range=lsp.Range(
                                        start=lsp.Position(line=0, character=0),
                                        end=lsp.Position(line=0, character=0),
                                    ),
                                    new_text=f"pattern {suggested_name} = {pattern_text}\n\n",
                                ),
                                # Replace pattern with name reference
                                lsp.TextEdit(
                                    range=pattern_range,
                                    new_text=suggested_name,
                                ),
                            ],
                        },
                    ),
                ))

        return actions
    
    def _get_type_conversion(self, from_type: str, to_type: str) -> Optional[str]:
        """Get conversion function name for type conversion."""
        conversions = {
            ("int", "float"): "to_float",
            ("float", "int"): "to_int",
            ("string", "int"): "parse_int",
            ("string", "float"): "parse_float",
            ("int", "string"): "to_string",
            ("float", "string"): "to_string",
            ("bool", "string"): "to_string",
        }
        return conversions.get((from_type.lower(), to_type.lower()))
    
    def _get_line_text(self, source: str, line: int) -> str:
        """Get text of a specific line."""
        lines = source.splitlines()
        if 0 <= line < len(lines):
            return lines[line]
        return ""


    def _extract_undefined_symbol(self, message: str) -> Optional[str]:
        """Extract undefined symbol name from error message."""
        import re
        match = re.search(r"undefined[:\s]+['\"]?(\w+)['\"]?", message, re.IGNORECASE)
        if match:
            return match.group(1)
        return None
    
    def _extract_match_arm_pattern(
        self, doc_state: DocumentState, range_: lsp.Range
    ) -> Optional[Tuple[str, lsp.Range]]:
        """
        Extract pattern text from a match arm at cursor position.

        Returns:
            Tuple of (pattern_text, pattern_range) if on a case pattern, else None
        """
        import re

        line = range_.start.line
        line_text = self._get_line_text(doc_state.source, line)

        # Look for case pattern: "case <pattern> =>"
        case_match = re.match(r'^(\s*)case\s+(.+?)\s*=>', line_text)
        if not case_match:
            return None

        indent = case_match.group(1)
        pattern = case_match.group(2).strip()

        # Don't extract trivial patterns (wildcards, simple variables)
        if pattern in ('_', 'true', 'false') or re.match(r'^\w+$', pattern):
            return None

        # Calculate pattern range
        pattern_start_char = len(indent) + len("case ")
        pattern_end_char = pattern_start_char + len(pattern)

        pattern_range = lsp.Range(
            start=lsp.Position(line=line, character=pattern_start_char),
            end=lsp.Position(line=line, character=pattern_end_char),
        )

        return (pattern, pattern_range)

    def _suggest_pattern_name(self, pattern_text: str, doc_state: DocumentState) -> str:
        """
        Suggest a name for an extracted pattern based on its content.

        Args:
            pattern_text: The pattern being extracted
            doc_state: Document state for checking existing names

        Returns:
            A suggested snake_case pattern name
        """
        import re

        # Extract meaningful parts from pattern
        # e.g., "Person { name: \"John\" }" -> "john_person"
        # e.g., "Amount > 100" -> "large_amount"

        name_parts = []

        # Look for struct/enum type name
        struct_match = re.match(r'^(\w+)\s*\{', pattern_text)
        if struct_match:
            name_parts.append(struct_match.group(1).lower())

        # Look for literal values
        string_values = re.findall(r'"([^"]+)"', pattern_text)
        for val in string_values[:2]:  # Max 2 string parts
            # Convert to snake_case
            clean_val = re.sub(r'[^a-zA-Z0-9]', '_', val.lower())
            clean_val = re.sub(r'_+', '_', clean_val).strip('_')
            if clean_val and len(clean_val) <= 20:
                name_parts.insert(0, clean_val)

        # Look for numeric comparisons
        if '>' in pattern_text or '>=' in pattern_text:
            name_parts.insert(0, "large")
        elif '<' in pattern_text or '<=' in pattern_text:
            name_parts.insert(0, "small")

        # Fallback if no meaningful parts
        if not name_parts:
            name_parts = ["extracted_pattern"]

        suggested = "_".join(name_parts)

        # Ensure uniqueness by checking existing pattern names
        existing_patterns = self._get_existing_pattern_names(doc_state)
        base_name = suggested
        counter = 1
        while suggested in existing_patterns:
            suggested = f"{base_name}_{counter}"
            counter += 1

        return suggested

    def _get_existing_pattern_names(self, doc_state: DocumentState) -> set:
        """Get set of existing pattern names in document."""
        import re
        names = set()
        for line in doc_state.source.splitlines():
            match = re.match(r'^\s*pattern\s+(\w+)\s*=', line)
            if match:
                names.add(match.group(1))
        return names

    def _find_similar_variants(self, doc_state: DocumentState, typo: str) -> List[str]:
        """Find enum variants similar to a typo using Levenshtein distance."""
        if not doc_state.ast:
            return []
        
        # Collect all enum variant names from AST
        variants = []
        for type_def in doc_state.ast.type_defs:
            # Check if this is an enum (has variants)
            if hasattr(type_def, 'variants'):
                for variant in type_def.variants:
                    variants.append(variant.name)
        
        # Simple similarity score (case-insensitive prefix/substring match)
        def similarity(a: str, b: str) -> int:
            a_lower, b_lower = a.lower(), b.lower()
            if a_lower == b_lower:
                return 100
            if a_lower.startswith(b_lower) or b_lower.startswith(a_lower):
                return 80
            if a_lower in b_lower or b_lower in a_lower:
                return 60
            # Count matching characters
            common = sum(1 for c in a_lower if c in b_lower)
            return int(common * 100 / max(len(a), len(b)))
        
        # Score and sort variants
        scored = [(v, similarity(v, typo)) for v in variants]
        scored.sort(key=lambda x: -x[1])
        
        # Return variants with score > 40
        return [v for v, score in scored if score > 40]

    def _get_code_lenses(self, uri: str) -> List[lsp.CodeLens]:
        """Provide code lenses (actionable annotations)."""
        lenses: List[lsp.CodeLens] = []
        doc_state = self._documents.get(uri)

        if not doc_state or not doc_state.ast:
            return lenses

        # Add "Run tests" lens above statute definitions
        for statute in doc_state.ast.statutes:
            loc = statute.source_location
            if loc:
                lenses.append(lsp.CodeLens(
                    range=lsp.Range(
                        start=lsp.Position(line=loc.line - 1, character=0),
                        end=lsp.Position(line=loc.line - 1, character=0),
                    ),
                    command=lsp.Command(
                        title=f"▶ Run tests for S{statute.section_number}",
                        command="yuho.runStatuteTests",
                        arguments=[uri, statute.section_number],
                    ),
                ))

        # Add "Transpile" lens above statute definitions
        for statute in doc_state.ast.statutes:
            loc = statute.source_location
            if loc:
                lenses.append(lsp.CodeLens(
                    range=lsp.Range(
                        start=lsp.Position(line=loc.line - 1, character=0),
                        end=lsp.Position(line=loc.line - 1, character=0),
                    ),
                    command=lsp.Command(
                        title="📄 Transpile to English",
                        command="yuho.transpileStatute",
                        arguments=[uri, statute.section_number, "english"],
                    ),
                ))

        return lenses

    def _get_folding_ranges(self, uri: str) -> List[lsp.FoldingRange]:
        """Provide folding ranges for code folding."""
        ranges: List[lsp.FoldingRange] = []
        doc_state = self._documents.get(uri)

        if not doc_state or not doc_state.ast:
            return ranges

        # Fold structs
        for struct in doc_state.ast.type_defs:
            loc = struct.source_location
            if loc and loc.end_line > loc.line:
                ranges.append(lsp.FoldingRange(
                    start_line=loc.line - 1,
                    end_line=loc.end_line - 1,
                    kind=lsp.FoldingRangeKind.Region,
                ))

        # Fold functions
        for func in doc_state.ast.function_defs:
            loc = func.source_location
            if loc and loc.end_line > loc.line:
                ranges.append(lsp.FoldingRange(
                    start_line=loc.line - 1,
                    end_line=loc.end_line - 1,
                    kind=lsp.FoldingRangeKind.Region,
                ))

        # Fold statutes
        for statute in doc_state.ast.statutes:
            loc = statute.source_location
            if loc and loc.end_line > loc.line:
                ranges.append(lsp.FoldingRange(
                    start_line=loc.line - 1,
                    end_line=loc.end_line - 1,
                    kind=lsp.FoldingRangeKind.Region,
                ))

        return ranges

    def _update_configuration(self, settings: Any) -> None:
        """Update server configuration from client settings."""
        if not settings:
            return

        # Handle yuho-specific settings
        yuho_settings = settings.get("yuho", {})
        if yuho_settings:
            # Update logging level
            if "logLevel" in yuho_settings:
                level = yuho_settings["logLevel"].upper()
                if level in ("DEBUG", "INFO", "WARNING", "ERROR"):
                    logger.setLevel(getattr(logging, level))

            # Could add more configuration options here

    def _get_semantic_tokens(self, uri: str) -> Optional[lsp.SemanticTokens]:
        """Compute semantic tokens for the document."""
        doc_state = self._documents.get(uri)
        if not doc_state or not doc_state.ast:
            return None

        # Token type indices (matching the legend defined in handler)
        TOKEN_TYPES = {
            "namespace": 0, "type": 1, "class": 2, "enum": 3, "interface": 4,
            "struct": 5, "typeParameter": 6, "parameter": 7, "variable": 8,
            "property": 9, "enumMember": 10, "event": 11, "function": 12,
            "method": 13, "macro": 14, "keyword": 15, "modifier": 16,
            "comment": 17, "string": 18, "number": 19, "regexp": 20, "operator": 21,
        }

        # Modifier bit flags
        MODIFIERS = {
            "declaration": 0, "definition": 1, "readonly": 2, "static": 3,
            "deprecated": 4, "abstract": 5, "async": 6, "modification": 7,
            "documentation": 8, "defaultLibrary": 9,
        }

        tokens: List[tuple] = []  # (line, col, length, type_idx, modifier_bits)

        # Collect tokens from structs
        for struct in doc_state.ast.type_defs:
            loc = struct.source_location
            if loc:
                # Struct name token
                tokens.append((
                    loc.line - 1,  # 0-indexed
                    loc.col - 1,
                    len(struct.name),
                    TOKEN_TYPES["struct"],
                    (1 << MODIFIERS["definition"]),
                ))

        # Collect tokens from functions
        for func in doc_state.ast.function_defs:
            loc = func.source_location
            if loc:
                tokens.append((
                    loc.line - 1,
                    loc.col - 1,
                    len(func.name),
                    TOKEN_TYPES["function"],
                    (1 << MODIFIERS["definition"]),
                ))

            # Parameters
            for param in func.params:
                if param.source_location:
                    tokens.append((
                        param.source_location.line - 1,
                        param.source_location.col - 1,
                        len(param.name),
                        TOKEN_TYPES["parameter"],
                        0,
                    ))

        # Collect tokens from statutes
        for statute in doc_state.ast.statutes:
            loc = statute.source_location
            if loc:
                tokens.append((
                    loc.line - 1,
                    loc.col - 1,
                    len(f"statute"),
                    TOKEN_TYPES["keyword"],
                    0,
                ))

        # Sort tokens by position
        tokens.sort(key=lambda t: (t[0], t[1]))

        # Encode as relative positions (LSP semantic tokens format)
        data: List[int] = []
        prev_line = 0
        prev_col = 0

        for line, col, length, type_idx, modifiers in tokens:
            delta_line = line - prev_line
            delta_col = col if delta_line > 0 else col - prev_col

            data.extend([delta_line, delta_col, length, type_idx, modifiers])

            prev_line = line
            prev_col = col

        return lsp.SemanticTokens(data=data)

    def _get_inlay_hints(self, uri: str, range_: lsp.Range) -> List[lsp.InlayHint]:
        """Provide inlay hints for inferred types and parameter names."""
        hints: List[lsp.InlayHint] = []
        doc_state = self._documents.get(uri)

        if not doc_state or not doc_state.ast:
            return hints

        # Add type hints for variable declarations without explicit types
        for var in doc_state.ast.variables:
            loc = var.source_location
            if not loc:
                continue

            # Check if in range
            if loc.line - 1 < range_.start.line or loc.line - 1 > range_.end.line:
                continue

            # If variable has a value but type could be inferred
            if var.value and var.type_annotation:
                type_str = self._type_to_str(var.type_annotation)
                hints.append(lsp.InlayHint(
                    position=lsp.Position(
                        line=loc.line - 1,
                        character=loc.col + len(var.name),
                    ),
                    label=f": {type_str}",
                    kind=lsp.InlayHintKind.Type,
                    padding_left=False,
                    padding_right=True,
                ))

        # Add parameter name hints for function calls
        # (Requires deeper AST traversal - simplified for now)

        return hints

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
