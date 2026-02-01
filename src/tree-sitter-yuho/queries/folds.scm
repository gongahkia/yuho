; tree-sitter code folding queries for Yuho
; Defines foldable regions for editors

; =============================================================================
; Struct bodies are foldable
; =============================================================================

(struct_definition
  "{" @fold.start
  "}" @fold.end) @fold

; =============================================================================
; Match expressions (case arms) are foldable
; =============================================================================

(match_expression
  "{" @fold.start
  "}" @fold.end) @fold

; =============================================================================
; Function bodies are foldable
; =============================================================================

(function_definition
  (block
    "{" @fold.start
    "}" @fold.end)) @fold

; =============================================================================
; Statute blocks are foldable
; =============================================================================

(statute_block
  "{" @fold.start
  "}" @fold.end) @fold

; Nested statute members are foldable
(definitions_block
  "{" @fold.start
  "}" @fold.end) @fold

(elements_block
  "{" @fold.start
  "}" @fold.end) @fold

(penalty_block
  "{" @fold.start
  "}" @fold.end) @fold

(illustration_block
  "{" @fold.start
  "}" @fold.end) @fold

; =============================================================================
; Struct literals are foldable
; =============================================================================

(struct_literal
  "{" @fold.start
  "}" @fold.end) @fold

; =============================================================================
; Multiline comments are foldable
; =============================================================================

(multiline_comment) @fold
