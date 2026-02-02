; Tree-sitter indent queries for Yuho
; Controls automatic indentation

; Indent after opening blocks
[
  (statute_block)
  (elements_block)
  (struct_definition)
  (enum_definition)
  (function_definition)
  (match_expression)
  (if_expression)
  (block)
] @indent.begin

; Dedent before closing braces
"}" @indent.end

; Align with opening bracket
"(" @indent.align
"[" @indent.align

; Special handling for match arms
(match_arm) @indent.begin

; Branch control - else aligns with if
(else_clause) @indent.branch
