; Tree-sitter highlight queries for Yuho
; Provides syntax highlighting for statute definitions

; Keywords
[
  "statute"
  "section"
  "title"
  "elements"
  "fn"
  "struct"
  "enum"
  "import"
  "from"
  "match"
  "case"
  "if"
  "then"
  "else"
  "return"
  "let"
  "const"
  "type"
  "penalty"
  "punishment"
  "illustration"
  "exception"
] @keyword

; Types
[
  "int"
  "bool"
  "string"
  "money"
  "percent"
  "date"
  "duration"
  "void"
] @type.builtin

(type_identifier) @type

; Literals
(number_literal) @number
(string_literal) @string
(boolean_literal) @boolean

; Statute-specific
(section_number) @constant
(statute_title) @title
(element_name) @field
(penalty_type) @keyword.operator

; Functions and methods
(function_definition
  name: (identifier) @function)

(function_call
  function: (identifier) @function.call)

; Variables and parameters
(parameter
  name: (identifier) @parameter)

(variable_declaration
  name: (identifier) @variable)

(assignment
  left: (identifier) @variable)

; Struct definitions
(struct_definition
  name: (identifier) @type)

(struct_field
  name: (identifier) @field)

; Enum definitions
(enum_definition
  name: (identifier) @type)

(enum_variant
  name: (identifier) @constant)

; Operators
[
  "+"
  "-"
  "*"
  "/"
  "%"
  "="
  "=="
  "!="
  "<"
  ">"
  "<="
  ">="
  "&&"
  "||"
  "!"
  ":="
  "->"
] @operator

; Punctuation
[
  "("
  ")"
  "["
  "]"
  "{"
  "}"
] @punctuation.bracket

[
  ":"
  ";"
  ","
  "."
] @punctuation.delimiter

; Comments
(comment) @comment

; Match expressions
(match_expression
  value: (_) @variable)

(match_arm
  pattern: (_) @pattern)

; Special contexts
(illustration
  content: (string_literal) @string.documentation)

(exception_block
  condition: (_) @conditional)
