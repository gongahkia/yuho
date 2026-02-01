; tree-sitter syntax highlighting queries for Yuho
; Used by editors (Neovim, VSCode, Helix, etc.) for accurate syntax highlighting

; =============================================================================
; Keywords
; =============================================================================

[
  "struct"
  "fn"
  "statute"
  "import"
  "from"
  "match"
  "case"
  "consequence"
  "return"
  "pass"
  "definitions"
  "elements"
  "penalty"
  "illustration"
  "imprisonment"
  "fine"
  "supplementary"
  "actus_reus"
  "mens_rea"
  "circumstance"
  "if"
] @keyword

; =============================================================================
; Types
; =============================================================================

(builtin_type) @type.builtin

[
  "int"
  "float"
  "bool"
  "string"
  "money"
  "percent"
  "date"
  "duration"
  "void"
] @type.builtin

; User-defined types (struct names, type references)
(struct_definition
  name: (identifier) @type.definition)

(generic_type
  (identifier) @type)

; Type annotations
(parameter
  type: (identifier) @type)

(field_definition
  type: (identifier) @type)

(variable_declaration
  type: (identifier) @type)

; =============================================================================
; Literals
; =============================================================================

(integer_literal) @number
(float_literal) @number.float
(boolean_literal) @boolean

(string_literal) @string
(escape_sequence) @string.escape

(money_literal) @number.currency
(currency_symbol) @constant.currency
(money_amount) @number

(percent_literal) @number.percent

(date_literal) @number.date

(duration_literal) @number.duration
(duration_unit) @keyword.duration

; =============================================================================
; Comments
; =============================================================================

(comment) @comment.line
(multiline_comment) @comment.block
(doc_comment) @comment.documentation

; =============================================================================
; Operators
; =============================================================================

[
  ":="
  ".."
] @operator

[
  "+"
  "-"
  "*"
  "/"
  "%"
] @operator.arithmetic

[
  "=="
  "!="
  "<"
  ">"
  "<="
  ">="
] @operator.comparison

[
  "&&"
  "||"
  "!"
] @operator.logical

; =============================================================================
; Punctuation
; =============================================================================

[
  "{"
  "}"
] @punctuation.bracket

[
  "["
  "]"
] @punctuation.bracket

[
  "("
  ")"
] @punctuation.bracket

[
  ","
  ";"
] @punctuation.delimiter

"." @punctuation.delimiter

; =============================================================================
; Functions
; =============================================================================

(function_definition
  name: (identifier) @function.definition)

(function_call
  callee: (identifier) @function.call)

(function_call
  callee: (field_access
    field: (identifier) @function.method))

; Parameters
(parameter
  name: (identifier) @variable.parameter)

; =============================================================================
; Struct definitions
; =============================================================================

(field_definition
  name: (identifier) @property.definition)

(field_assignment
  name: (identifier) @property)

(field_access
  field: (identifier) @property)

(field_pattern
  name: (identifier) @property)

; =============================================================================
; Variables
; =============================================================================

(variable_declaration
  name: (identifier) @variable.definition)

(assignment_statement
  target: (identifier) @variable)

(binding_pattern) @variable

; General identifiers (fallback)
(identifier) @variable

; =============================================================================
; Pattern matching
; =============================================================================

(wildcard_pattern) @constant.wildcard

(match_arm
  pattern: (identifier) @constant.enum)

; =============================================================================
; Statute-specific
; =============================================================================

(statute_block
  section_number: (section_number) @constant.section)

(statute_block
  title: (string_literal) @string.title)

(definition_entry
  term: (identifier) @constant.definition)

(element_entry
  name: (identifier) @variable.element)

(illustration_block
  label: (identifier) @constant.label)

; =============================================================================
; Imports
; =============================================================================

(import_statement
  (import_path) @string.import)

; =============================================================================
; Constants (TRUE, FALSE interpreted as constants)
; =============================================================================

((identifier) @constant.builtin
  (#match? @constant.builtin "^(TRUE|FALSE)$"))

; Enum variants accessed via dot notation
(field_access
  base: (identifier) @type.enum
  field: (identifier) @constant.enum)
