; Tree-sitter fold queries for Yuho
; Controls code folding in editors

; Foldable blocks
[
  (statute_block)
  (elements_block)
  (struct_definition)
  (enum_definition)
  (function_definition)
  (match_expression)
  (if_expression)
  (block)
  (penalty_block)
  (exception_block)
  (illustration)
] @fold

; Comments are foldable
(comment)+ @fold
