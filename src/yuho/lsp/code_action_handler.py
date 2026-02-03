"""
Code action handler for Yuho LSP.

Provides quick fixes and refactorings for Yuho code.
"""

from typing import List, Optional, Tuple, TYPE_CHECKING
import re

try:
    from lsprotocol import types as lsp
except ImportError:
    raise ImportError(
        "LSP dependencies not installed. Install with: pip install yuho[lsp]"
    )

if TYPE_CHECKING:
    from yuho.lsp.server import DocumentState


def get_type_conversion(from_type: str, to_type: str) -> Optional[str]:
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


def get_line_text(source: str, line: int) -> str:
    """Get text of a specific line."""
    lines = source.splitlines()
    if 0 <= line < len(lines):
        return lines[line]
    return ""


def extract_undefined_symbol(message: str) -> Optional[str]:
    """Extract undefined symbol name from error message."""
    match = re.search(r"undefined[:\s]+['\"]?(\w+)['\"]?", message, re.IGNORECASE)
    if match:
        return match.group(1)
    return None


def extract_match_arm_pattern(
    doc_state: "DocumentState", range_: lsp.Range
) -> Optional[Tuple[str, lsp.Range]]:
    """
    Extract pattern text from a match arm at cursor position.

    Returns:
        Tuple of (pattern_text, pattern_range) if on a case pattern, else None
    """
    line = range_.start.line
    line_text = get_line_text(doc_state.source, line)

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


def get_existing_pattern_names(doc_state: "DocumentState") -> set:
    """Get set of existing pattern names in document."""
    names = set()
    for line in doc_state.source.splitlines():
        match = re.match(r'^\s*pattern\s+(\w+)\s*=', line)
        if match:
            names.add(match.group(1))
    return names


def suggest_pattern_name(pattern_text: str, doc_state: "DocumentState") -> str:
    """
    Suggest a name for an extracted pattern based on its content.

    Args:
        pattern_text: The pattern being extracted
        doc_state: Document state for checking existing names

    Returns:
        A suggested snake_case pattern name
    """
    name_parts = []

    # Look for struct/enum type name
    struct_match = re.match(r'^(\w+)\s*\{', pattern_text)
    if struct_match:
        name_parts.append(struct_match.group(1).lower())

    # Look for literal values
    string_values = re.findall(r'"([^"]+)"', pattern_text)
    for val in string_values[:2]:  # Max 2 string parts
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

    # Ensure uniqueness
    existing_patterns = get_existing_pattern_names(doc_state)
    base_name = suggested
    counter = 1
    while suggested in existing_patterns:
        suggested = f"{base_name}_{counter}"
        counter += 1

    return suggested


def get_struct_field_names(doc_state: "DocumentState", type_name: str) -> List[str]:
    """Get field names for a struct type from AST or source."""
    field_names = []

    # Try AST first
    if doc_state.ast:
        for type_def in doc_state.ast.type_defs:
            if hasattr(type_def, 'name') and type_def.name == type_name:
                if hasattr(type_def, 'fields'):
                    for field in type_def.fields:
                        if hasattr(field, 'name'):
                            field_names.append(field.name)
                    if field_names:
                        return field_names

    # Fallback: parse source for struct definition
    struct_pattern = re.compile(
        rf'struct\s+{re.escape(type_name)}\s*\{{([^}}]+)\}}',
        re.DOTALL
    )

    match = struct_pattern.search(doc_state.source)
    if match:
        fields_str = match.group(1)
        field_pattern = re.compile(r'(\w+)\s*:')
        for field_match in field_pattern.finditer(fields_str):
            field_names.append(field_match.group(1))

    return field_names


def get_struct_literal_info(
    doc_state: "DocumentState", range_: lsp.Range
) -> Optional[Tuple[lsp.Range, str]]:
    """
    Get info to convert a positional struct literal to explicit form.

    Returns:
        Tuple of (literal_range, explicit_form) or None
    """
    line = range_.start.line
    line_text = get_line_text(doc_state.source, line)

    # Match positional struct: TypeName(arg1, arg2, ...)
    struct_pattern = re.compile(r'([A-Z]\w*)\s*\(([^)]+)\)')

    for match in struct_pattern.finditer(line_text):
        match_start = match.start()
        match_end = match.end()

        if match_start <= range_.start.character <= match_end:
            type_name = match.group(1)
            args_str = match.group(2)
            args = [a.strip() for a in args_str.split(',')]
            field_names = get_struct_field_names(doc_state, type_name)

            if not field_names:
                field_names = [f"field{i+1}" for i in range(len(args))]

            if len(args) <= len(field_names):
                field_assignments = [
                    f"{field_names[i]}: {args[i]}"
                    for i in range(len(args))
                ]
                explicit_form = f"{type_name} {{ {', '.join(field_assignments)} }}"

                literal_range = lsp.Range(
                    start=lsp.Position(line=line, character=match_start),
                    end=lsp.Position(line=line, character=match_end),
                )

                return (literal_range, explicit_form)

    return None


def get_inline_variable_info(
    doc_state: "DocumentState", range_: lsp.Range
) -> Optional[Tuple[str, str, List[lsp.Range]]]:
    """
    Get information needed to inline a variable at cursor.

    Returns:
        Tuple of (var_name, var_value, list of usage ranges) or None
    """
    line = range_.start.line
    char = range_.start.character
    line_text = get_line_text(doc_state.source, line)

    # Find word boundaries
    word_start = char
    while word_start > 0 and (line_text[word_start - 1].isalnum() or line_text[word_start - 1] == '_'):
        word_start -= 1

    word_end = char
    while word_end < len(line_text) and (line_text[word_end].isalnum() or line_text[word_end] == '_'):
        word_end += 1

    if word_start == word_end:
        return None

    var_name = line_text[word_start:word_end]

    # Look for variable definition
    var_value = None
    definition_line = -1

    lines = doc_state.source.splitlines()
    for i, src_line in enumerate(lines):
        let_match = re.match(rf'^\s*let\s+{re.escape(var_name)}\s*=\s*(.+)$', src_line)
        if let_match:
            var_value = let_match.group(1).strip()
            definition_line = i
            break

        assign_match = re.match(rf'^\s*{re.escape(var_name)}\s*:=\s*(.+)$', src_line)
        if assign_match:
            var_value = assign_match.group(1).strip()
            definition_line = i
            break

    if not var_value:
        return None

    # Find all usages
    usage_ranges = []
    var_pattern = re.compile(rf'\b{re.escape(var_name)}\b')

    for line_num, src_line in enumerate(lines):
        if line_num == definition_line:
            continue

        for match in var_pattern.finditer(src_line):
            prefix = src_line[:match.start()]
            if 'let ' in prefix or ':=' in src_line[match.start():]:
                continue

            usage_ranges.append(lsp.Range(
                start=lsp.Position(line=line_num, character=match.start()),
                end=lsp.Position(line=line_num, character=match.end()),
            ))

    return (var_name, var_value, usage_ranges)


def find_similar_variants(doc_state: "DocumentState", typo: str) -> List[str]:
    """Find enum variants similar to a typo using similarity scoring."""
    if not doc_state.ast:
        return []
    
    variants = []
    for type_def in doc_state.ast.type_defs:
        if hasattr(type_def, 'variants'):
            for variant in type_def.variants:
                variants.append(variant.name)
    
    def similarity(a: str, b: str) -> int:
        a_lower, b_lower = a.lower(), b.lower()
        if a_lower == b_lower:
            return 100
        if a_lower.startswith(b_lower) or b_lower.startswith(a_lower):
            return 80
        if a_lower in b_lower or b_lower in a_lower:
            return 60
        common = sum(1 for c in a_lower if c in b_lower)
        return int(common * 100 / max(len(a), len(b)))
    
    scored = [(v, similarity(v, typo)) for v in variants]
    scored.sort(key=lambda x: -x[1])
    
    return [v for v, score in scored if score > 40]


def get_code_actions(
    doc_state: Optional["DocumentState"],
    uri: str,
    range_: lsp.Range,
    context: lsp.CodeActionContext,
) -> List[lsp.CodeAction]:
    """Provide code actions (quick fixes, refactorings)."""
    actions: List[lsp.CodeAction] = []

    if not doc_state:
        return actions

    # Check diagnostics for quick fixes
    for diagnostic in context.diagnostics:
        msg = diagnostic.message.lower()
        
        # Fix for undefined symbol
        if "undefined" in msg:
            word = extract_undefined_symbol(diagnostic.message)
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
        
        # Fix for missing match arms
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
            match = re.search(r"expected\s+(\w+).*got\s+(\w+)", msg)
            if match:
                expected, got = match.groups()
                conversion = get_type_conversion(got, expected)
                if conversion:
                    actions.append(lsp.CodeAction(
                        title=f"Convert to {expected}",
                        kind=lsp.CodeActionKind.QuickFix,
                        diagnostics=[diagnostic],
                    ))
        
        # Fix for missing struct fields
        if "missing field" in msg:
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
        
        # Fix for enum variant typos
        if "unknown variant" in msg or "invalid variant" in msg:
            variant_match = re.search(r"variant[:\s]+['\"]?(\w+)['\"]?", msg)
            if variant_match:
                typo = variant_match.group(1)
                suggestions = find_similar_variants(doc_state, typo)
                for suggestion in suggestions[:3]:
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

    # Context-based refactorings
    if doc_state.ast:
        line_text = get_line_text(doc_state.source, range_.start.line)

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
        pattern_info = extract_match_arm_pattern(doc_state, range_)
        if pattern_info:
            pattern_text, pattern_range = pattern_info
            suggested_name = suggest_pattern_name(pattern_text, doc_state)
            actions.append(lsp.CodeAction(
                title=f"Extract to named pattern '{suggested_name}'",
                kind=lsp.CodeActionKind.RefactorExtract,
                edit=lsp.WorkspaceEdit(
                    changes={
                        uri: [
                            lsp.TextEdit(
                                range=lsp.Range(
                                    start=lsp.Position(line=0, character=0),
                                    end=lsp.Position(line=0, character=0),
                                ),
                                new_text=f"pattern {suggested_name} = {pattern_text}\n\n",
                            ),
                            lsp.TextEdit(
                                range=pattern_range,
                                new_text=suggested_name,
                            ),
                        ],
                    },
                ),
            ))

        # Inline variable at cursor
        inline_info = get_inline_variable_info(doc_state, range_)
        if inline_info:
            var_name, var_value, usage_ranges = inline_info
            if usage_ranges:
                edits = [
                    lsp.TextEdit(range=usage_range, new_text=var_value)
                    for usage_range in usage_ranges
                ]
                actions.append(lsp.CodeAction(
                    title=f"Inline variable '{var_name}'",
                    kind=lsp.CodeActionKind.RefactorInline,
                    edit=lsp.WorkspaceEdit(changes={uri: edits}),
                ))

        # Convert struct literal to explicit form
        struct_info = get_struct_literal_info(doc_state, range_)
        if struct_info:
            struct_range, explicit_form = struct_info
            actions.append(lsp.CodeAction(
                title="Convert to explicit struct literal",
                kind=lsp.CodeActionKind.RefactorRewrite,
                edit=lsp.WorkspaceEdit(
                    changes={
                        uri: [lsp.TextEdit(
                            range=struct_range,
                            new_text=explicit_form,
                        )],
                    },
                ),
            ))

    return actions
