"""
Yuho Language Server Protocol implementation using pygls.
"""

from typing import Dict, List, Optional, Any, Tuple
import logging
import threading

try:
    from lsprotocol import types as lsp
    from pygls.lsp.server import LanguageServer
    from pygls.workspace import TextDocument
except ImportError:
    raise ImportError(
        "LSP dependencies not installed. Install with: pip install yuho[lsp]"
    )

from yuho import __version__
from yuho.parser import SourceLocation, get_parser
from yuho.parser.wrapper import ParseError, ParseResult
from yuho.ast import ASTBuilder, ModuleNode

# Import refactored handlers
from yuho.lsp.diagnostics import collect_diagnostics
from yuho.lsp.completion_handler import get_completions, YUHO_KEYWORDS, YUHO_TYPES
from yuho.lsp.hover_handler import get_hover
from yuho.lsp.code_action_handler import (
    get_code_actions,
    get_line_text,
    extract_match_arm_pattern,
    suggest_pattern_name,
    get_struct_literal_info,
    get_inline_variable_info,
    find_similar_variants,
    get_type_conversion,
    extract_undefined_symbol,
)

logger = logging.getLogger(__name__)


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

    def apply_changes(
        self,
        changes: List[Any],
        version: int,
        *,
        parse_immediately: bool = True,
    ) -> None:
        """Apply LSP content changes (full or incremental) before reparsing."""
        updated_source = self.source
        for change in changes:
            updated_source = self._apply_change(updated_source, change)
        self.source = updated_source
        self.version = version
        if parse_immediately:
            self._parse()

    def _apply_change(self, source: str, change: Any) -> str:
        """Apply a single LSP text change to source."""
        change_range = getattr(change, "range", None)
        if change_range is None:
            # Full document replacement.
            return change.text

        start = self._position_to_offset(source, change_range.start)
        end = self._position_to_offset(source, change_range.end)
        if end < start:
            start, end = end, start
        return source[:start] + change.text + source[end:]

    def _position_to_offset(self, source: str, position: lsp.Position) -> int:
        """Convert LSP line/character position to a source-string offset."""
        if position.line < 0:
            return 0

        lines = source.splitlines(keepends=True)
        if not lines:
            return 0
        if position.line >= len(lines):
            return len(source)

        line_start = sum(len(lines[i]) for i in range(position.line))
        line_with_eol = lines[position.line]
        line_text = line_with_eol.rstrip("\r\n")
        character = max(0, min(position.character, len(line_text)))
        return line_start + character

    def _parse(self):
        """Parse the document and build AST."""
        parser = get_parser()
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
        super().__init__(name="yuho-lsp", version=__version__)

        # Document cache
        self._documents: Dict[str, DocumentState] = {}
        
        # Workspace folders for cross-file operations
        self._workspace_folders: List[str] = []
        
        # Symbol index for workspace-wide lookups
        self._symbol_index: Dict[str, Dict[str, Any]] = {}
        self._symbol_index_lock = threading.Lock()
        self._symbol_scan_generation = 0

        # Debounce parse+diagnostic work during rapid did_change updates.
        self._parse_debounce_seconds = 0.15
        self._parse_timers: Dict[str, threading.Timer] = {}
        self._parse_timers_lock = threading.Lock()

        # Register handlers
        self._register_handlers()
    
    def _index_workspace_symbols(self, folder_uri: str) -> None:
        """Index workspace symbols in a background worker."""
        with self._symbol_index_lock:
            self._symbol_scan_generation += 1
            generation = self._symbol_scan_generation

        worker = threading.Thread(
            target=self._index_workspace_symbols_worker,
            args=(folder_uri, generation),
            daemon=True,
        )
        worker.start()

    def _index_workspace_symbols_worker(self, folder_uri: str, generation: int) -> None:
        """Build a symbol index for a workspace folder, canceling stale scans."""
        from pathlib import Path
        from urllib.parse import urlparse, unquote
        
        parsed = urlparse(folder_uri)
        folder_path = Path(unquote(parsed.path))
        
        if not folder_path.exists():
            return

        local_index: Dict[str, Dict[str, Any]] = {}
        
        for yh_file in folder_path.rglob("*.yh"):
            with self._symbol_index_lock:
                if generation != self._symbol_scan_generation:
                    return

            file_uri = f"file://{yh_file}"
            if file_uri in self._documents:
                doc_state = self._documents[file_uri]
            else:
                try:
                    content = yh_file.read_text()
                    doc_state = DocumentState(file_uri, content)
                    doc_state._parse()
                except Exception as exc:
                    logger.warning(
                        "Workspace symbol indexing failed for %s: %s",
                        file_uri,
                        exc,
                    )
                    continue

            if not doc_state.ast:
                continue

            for struct in doc_state.ast.type_defs:
                local_index[struct.name] = {
                    "kind": "struct",
                    "uri": file_uri,
                    "location": struct.source_location,
                }
            for func in doc_state.ast.function_defs:
                local_index[func.name] = {
                    "kind": "function",
                    "uri": file_uri,
                    "location": func.source_location,
                }

        with self._symbol_index_lock:
            if generation != self._symbol_scan_generation:
                return
            self._symbol_index = local_index


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
            self._ensure_workspace_index_for_uri(uri)

        @self.feature(lsp.TEXT_DOCUMENT_DID_CHANGE)
        def did_change(params: lsp.DidChangeTextDocumentParams):
            """Handle document change."""
            uri = params.text_document.uri
            version = params.text_document.version

            if uri not in self._documents:
                return

            doc_state = self._documents[uri]
            doc_state.apply_changes(
                list(params.content_changes),
                version,
                parse_immediately=False,
            )
            self._schedule_parse_and_diagnostics(uri)

        @self.feature(lsp.TEXT_DOCUMENT_DID_CLOSE)
        def did_close(params: lsp.DidCloseTextDocumentParams):
            """Handle document close."""
            uri = params.text_document.uri
            if uri in self._documents:
                self._cancel_parse_timer(uri)
                del self._documents[uri]

        @self.feature(lsp.TEXT_DOCUMENT_DID_SAVE)
        def did_save(params: lsp.DidSaveTextDocumentParams):
            """Handle document save."""
            # Re-parse on save if text included
            if params.text:
                uri = params.text_document.uri
                if uri in self._documents:
                    self._cancel_parse_timer(uri)
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

        @self.feature(lsp.TEXT_DOCUMENT_SELECTION_RANGE)
        def selection_range(params: lsp.SelectionRangeParams) -> Optional[List[lsp.SelectionRange]]:
            """Provide selection ranges for expand/shrink selection."""
            uri = params.text_document.uri
            positions = params.positions

            return self._get_selection_ranges(uri, positions)

    def _schedule_parse_and_diagnostics(self, uri: str) -> None:
        """Debounce parse+diagnostic publication for rapid edits."""
        doc_state = self._documents.get(uri)
        if not doc_state:
            return

        target_version = doc_state.version
        timer: Optional[threading.Timer] = None

        def _flush() -> None:
            with self._parse_timers_lock:
                current = self._parse_timers.get(uri)
                if current is not timer:
                    return
                self._parse_timers.pop(uri, None)

            current_doc = self._documents.get(uri)
            if not current_doc or current_doc.version != target_version:
                return

            current_doc._parse()
            self._publish_diagnostics(uri, current_doc)

        timer = threading.Timer(self._parse_debounce_seconds, _flush)
        timer.daemon = True
        with self._parse_timers_lock:
            old_timer = self._parse_timers.pop(uri, None)
            if old_timer:
                old_timer.cancel()
            self._parse_timers[uri] = timer
        timer.start()

    def _cancel_parse_timer(self, uri: str) -> None:
        """Cancel pending debounced parse work for a URI."""
        with self._parse_timers_lock:
            timer = self._parse_timers.pop(uri, None)
        if timer:
            timer.cancel()

    def _ensure_workspace_index_for_uri(self, uri: str) -> None:
        """Track workspace folder for a URI and trigger background indexing."""
        from pathlib import Path
        from urllib.parse import urlparse, unquote

        parsed = urlparse(uri)
        if parsed.scheme != "file":
            return

        folder_uri = f"file://{Path(unquote(parsed.path)).parent}"
        if folder_uri not in self._workspace_folders:
            self._workspace_folders.append(folder_uri)
        self._index_workspace_symbols(folder_uri)

    def _publish_diagnostics(self, uri: str, doc_state: DocumentState):
        """Publish diagnostics for a document."""
        diagnostics = collect_diagnostics(doc_state)
        self.publish_diagnostics(uri, diagnostics)

    def _get_completions(self, uri: str, position: lsp.Position) -> lsp.CompletionList:
        """Get completion items for position."""
        doc_state = self._documents.get(uri)
        return get_completions(doc_state, uri, position)

    def _get_hover(self, uri: str, position: lsp.Position) -> Optional[lsp.Hover]:
        """Get hover information for position showing type info and doc-comments."""
        doc_state = self._documents.get(uri)
        if not doc_state:
            return None
        
        word = self._get_word_at_position(doc_state.source, position)
        return get_hover(doc_state, word, self._type_to_str)

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

    def _get_selection_ranges(
        self, uri: str, positions: List[lsp.Position]
    ) -> Optional[List[lsp.SelectionRange]]:
        """
        Get selection ranges for expand/shrink selection feature.

        Returns nested ranges from smallest to largest enclosing syntax element.
        """
        doc_state = self._documents.get(uri)
        if not doc_state:
            return None

        results = []
        for position in positions:
            selection_range = self._build_selection_range(doc_state, position)
            results.append(selection_range)

        return results

    def _build_selection_range(
        self, doc_state: DocumentState, position: lsp.Position
    ) -> lsp.SelectionRange:
        """Build nested selection ranges for a position."""
        import re

        line = position.line
        char = position.character
        lines = doc_state.source.splitlines()

        if line >= len(lines):
            # Return minimal range
            return lsp.SelectionRange(
                range=lsp.Range(start=position, end=position)
            )

        line_text = lines[line]
        ranges: List[lsp.Range] = []

        # Level 1: Word at cursor
        word_start = char
        word_end = char

        while word_start > 0 and (line_text[word_start - 1].isalnum() or line_text[word_start - 1] == '_'):
            word_start -= 1
        while word_end < len(line_text) and (line_text[word_end].isalnum() or line_text[word_end] == '_'):
            word_end += 1

        if word_start != word_end:
            ranges.append(lsp.Range(
                start=lsp.Position(line=line, character=word_start),
                end=lsp.Position(line=line, character=word_end),
            ))

        # Level 2: String literal if inside one
        for match in re.finditer(r'"[^"]*"', line_text):
            if match.start() <= char <= match.end():
                ranges.append(lsp.Range(
                    start=lsp.Position(line=line, character=match.start()),
                    end=lsp.Position(line=line, character=match.end()),
                ))
                break

        # Level 3: Bracketed expression (parentheses, braces, brackets)
        for open_char, close_char in [('(', ')'), ('{', '}'), ('[', ']')]:
            bracket_range = self._find_enclosing_brackets(
                lines, line, char, open_char, close_char
            )
            if bracket_range:
                ranges.append(bracket_range)

        # Level 4: Current line (non-whitespace)
        line_content_start = len(line_text) - len(line_text.lstrip())
        line_content_end = len(line_text.rstrip())
        if line_content_end > line_content_start:
            ranges.append(lsp.Range(
                start=lsp.Position(line=line, character=line_content_start),
                end=lsp.Position(line=line, character=line_content_end),
            ))

        # Level 5: Full line including newline
        ranges.append(lsp.Range(
            start=lsp.Position(line=line, character=0),
            end=lsp.Position(line=line + 1, character=0),
        ))

        # Level 6: Block (based on indentation)
        block_range = self._find_indentation_block(lines, line)
        if block_range:
            ranges.append(block_range)

        # Level 7: Entire document
        ranges.append(lsp.Range(
            start=lsp.Position(line=0, character=0),
            end=lsp.Position(line=len(lines), character=0),
        ))

        # Remove duplicates and sort by size (smallest first)
        unique_ranges = []
        seen = set()
        for r in ranges:
            key = (r.start.line, r.start.character, r.end.line, r.end.character)
            if key not in seen:
                seen.add(key)
                unique_ranges.append(r)

        # Sort by range size
        def range_size(r: lsp.Range) -> int:
            start = r.start.line * 10000 + r.start.character
            end = r.end.line * 10000 + r.end.character
            return end - start

        unique_ranges.sort(key=range_size)

        # Build nested SelectionRange (smallest to largest)
        if not unique_ranges:
            return lsp.SelectionRange(
                range=lsp.Range(start=position, end=position)
            )

        # Build from largest to smallest (parent first)
        result = lsp.SelectionRange(range=unique_ranges[-1])
        for r in reversed(unique_ranges[:-1]):
            result = lsp.SelectionRange(range=r, parent=result)

        return result

    def _find_enclosing_brackets(
        self, lines: List[str], line: int, char: int, open_char: str, close_char: str
    ) -> Optional[lsp.Range]:
        """Find the smallest enclosing bracket pair."""
        # Flatten to single string with line tracking
        line_text = lines[line]

        # Search backwards for opening bracket
        open_line, open_char_pos = line, char - 1
        depth = 0

        while open_line >= 0:
            search_line = lines[open_line]
            start_pos = open_char_pos if open_line == line else len(search_line) - 1

            for i in range(start_pos, -1, -1):
                c = search_line[i]
                if c == close_char:
                    depth += 1
                elif c == open_char:
                    if depth == 0:
                        # Found opening bracket, now find closing
                        close_line, close_char_pos = self._find_closing_bracket(
                            lines, open_line, i, open_char, close_char
                        )
                        if close_line is not None:
                            return lsp.Range(
                                start=lsp.Position(line=open_line, character=i),
                                end=lsp.Position(line=close_line, character=close_char_pos + 1),
                            )
                        return None
                    depth -= 1

            open_line -= 1
            open_char_pos = len(lines[open_line]) - 1 if open_line >= 0 else 0

        return None

    def _find_closing_bracket(
        self, lines: List[str], start_line: int, start_char: int, open_char: str, close_char: str
    ) -> Tuple[Optional[int], int]:
        """Find the matching closing bracket."""
        depth = 1
        line_num = start_line
        char_pos = start_char + 1

        while line_num < len(lines):
            search_line = lines[line_num]
            start_pos = char_pos if line_num == start_line else 0

            for i in range(start_pos, len(search_line)):
                c = search_line[i]
                if c == open_char:
                    depth += 1
                elif c == close_char:
                    depth -= 1
                    if depth == 0:
                        return (line_num, i)

            line_num += 1

        return (None, 0)

    def _find_indentation_block(self, lines: List[str], line: int) -> Optional[lsp.Range]:
        """Find block based on indentation level."""
        if line >= len(lines):
            return None

        current_line = lines[line]
        if not current_line.strip():
            return None

        current_indent = len(current_line) - len(current_line.lstrip())

        # Find block start (first line with same or less indentation)
        block_start = line
        for i in range(line - 1, -1, -1):
            l = lines[i]
            if not l.strip():
                continue
            indent = len(l) - len(l.lstrip())
            if indent < current_indent:
                break
            block_start = i

        # Find block end
        block_end = line
        for i in range(line + 1, len(lines)):
            l = lines[i]
            if not l.strip():
                continue
            indent = len(l) - len(l.lstrip())
            if indent < current_indent:
                break
            block_end = i

        if block_start == block_end:
            return None

        return lsp.Range(
            start=lsp.Position(line=block_start, character=0),
            end=lsp.Position(line=block_end + 1, character=0),
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
                    
            except Exception as exc:
                logger.warning(
                    "Workspace symbol rename scan failed for %s: %s",
                    file_uri,
                    exc,
                )


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
        seen: set[tuple[str, str, int, int]] = set()

        for uri, doc_state in self._documents.items():
            if not doc_state.ast:
                continue

            # Search structs
            for struct in doc_state.ast.type_defs:
                if query_lower in struct.name.lower():
                    loc = struct.source_location
                    if loc:
                        key = (uri, struct.name, loc.line, loc.col)
                        if key not in seen:
                            seen.add(key)
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
                        key = (uri, func.name, loc.line, loc.col)
                        if key not in seen:
                            seen.add(key)
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
                        symbol_name = f"S{statute.section_number}: {title}"
                        key = (uri, symbol_name, loc.line, loc.col)
                        if key not in seen:
                            seen.add(key)
                            results.append(lsp.SymbolInformation(
                                name=symbol_name,
                                kind=lsp.SymbolKind.Module,
                                location=lsp.Location(
                                    uri=uri,
                                    range=self._loc_to_range(loc),
                                ),
                            ))

        with self._symbol_index_lock:
            indexed_symbols = list(self._symbol_index.items())

        for symbol_name, entry in indexed_symbols:
            if query_lower not in symbol_name.lower():
                continue
            uri = entry.get("uri")
            loc = entry.get("location")
            kind = entry.get("kind", "")
            if not uri or not loc:
                continue

            key = (uri, symbol_name, loc.line, loc.col)
            if key in seen:
                continue
            seen.add(key)

            symbol_kind = (
                lsp.SymbolKind.Struct
                if kind == "struct"
                else lsp.SymbolKind.Function
            )
            results.append(
                lsp.SymbolInformation(
                    name=symbol_name,
                    kind=symbol_kind,
                    location=lsp.Location(
                        uri=uri,
                        range=self._loc_to_range(loc),
                    ),
                )
            )

        return results

    def _get_code_actions(
        self, uri: str, range_: lsp.Range, context: lsp.CodeActionContext
    ) -> List[lsp.CodeAction]:
        """Provide code actions (quick fixes, refactorings)."""
        doc_state = self._documents.get(uri)
        return get_code_actions(doc_state, uri, range_, context)

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
        super().start_io()

    def start_tcp(self, host: str, port: int):
        """Start the server on TCP."""
        super().start_tcp(host, port)
