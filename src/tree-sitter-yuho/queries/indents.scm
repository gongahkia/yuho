; tree-sitter indentation queries for Yuho
; Controls automatic indentation in editors

; =============================================================================
; Indent after opening braces
; =============================================================================

; General brace-based indentation
[
  (struct_definition)
  (function_definition)
  (block)
  (statute_block)
  (definitions_block)
  (elements_block)
  (penalty_block)
  (illustration_block)
  (match_expression)
  (struct_literal)
] @indent

; =============================================================================
; Indent match arms
; =============================================================================

; Match arms increase indent
(match_arm) @indent

; =============================================================================
; Opening braces trigger indent
; =============================================================================

"{" @indent.begin
"}" @indent.end
"}" @indent.branch

; =============================================================================
; Struct field definitions maintain indent
; =============================================================================

(field_definition) @indent.align

; =============================================================================
; Parameters maintain alignment
; =============================================================================

"(" @indent.begin.parameter
")" @indent.end.parameter

; =============================================================================
; Dedent on closing braces
; =============================================================================

; Closing braces dedent
(("}") @indent.dedent)

; =============================================================================
; Case statement indentation
; =============================================================================

; Case keyword should be at match level, body indented
(match_arm
  "case" @indent.branch
  ":=" @indent.dedent)

; =============================================================================
; Comments preserve surrounding indentation
; =============================================================================

(comment) @indent.auto
(multiline_comment) @indent.auto
