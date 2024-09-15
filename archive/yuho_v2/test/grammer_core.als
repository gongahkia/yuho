module grammer_core

open util/ordering[Time]
open util/boolean

abstract sig letter {}
abstract sig digit {}
abstract sig identifier {}

abstract sig type {}
abstract sig boolean_type extends type {}
abstract sig percent_type extends type {}
abstract sig money_type extends type {}
abstract sig date_type extends type {}
abstract sig duration_type extends type {}
abstract sig string_type extends type {}
abstract sig identifier_type extends type {}

abstract sig arithmetic_operator {}
abstract sig comparison_operator {}
abstract sig logical_operator {}

sig true_literal extends boolean_type {}
sig false_literal extends boolean_type {}
sig pass_statement {}

sig percent_value extends percent_type {
  value: one int
}

sig money_value extends money_type {
  value: one int
}

sig date_value extends date_type {
  day: one int,
  month: one int,
  year: one int
}

sig duration_value extends duration_type {
  days: one int,
  months: one int,
  years: one int
}

sig scope {
  name: one identifier,
  variables: set variable_declaration
}

sig variable_declaration {
  var_type: one type,
  var_name: one identifier,
  value: one expression
}

sig struct {
  name: one identifier,
  fields: set field
}

sig field {
  field_type: one type,
  field_name: one identifier
}

sig struct_literal {
  struct_name: one identifier,
  field_values: set field_value
}

sig field_value {
  field_name: one identifier,
  value: one expression
}

sig addition extends arithmetic_operator {}
sig subtraction extends arithmetic_operator {}
sig multiplication extends arithmetic_operator {}
sig division extends arithmetic_operator {}
sig integer_division extends arithmetic_operator {}
sig modulo extends arithmetic_operator {}

sig equal extends comparison_operator {}
sig not_equal extends comparison_operator {}
sig greater_than extends comparison_operator {}
sig less_than extends comparison_operator {}
greater_equal extends comparison_operator {}
sig less_equal extends comparison_operator {}

sig and_operator extends logical_operator {}
sig or_operator extends logical_operator {}
sig not_operator extends logical_operator {}

sig match_case {
  match_value: one identifier,
  cases: set case
}

sig case {
  condition: one expression,
  consequence: one expression
}

sig function {
  return_type: one type,
  func_name: one identifier,
  parameters: set parameter,
  body: one block
}

sig parameter {
  param_type: one type,
  param_name: one identifier
}

sig block {
  statements: set statement
}

abstract sig statement {}

sig return_statement extends statement {
  return_value: one expression
}

sig assignment_statement extends statement {
  left: one identifier,
  right: one expression
}

sig if_statement extends statement {
  condition: one expression,
  then_block: one block,
  else_block: one block
}

sig while_statement extends statement {
  condition: one expression,
  body: one block
}

sig for_statement extends statement {
  initializer: one statement,
  condition: one expression,
  update: one statement,
  body: one block
}

abstract sig expression {}

sig variable_expression extends expression {
  var_name: one identifier
}

sig literal_expression extends expression {
  literal: one literal
}

sig arithmetic_expression extends expression {
  left: one expression,
  right: one expression,
  operator: one arithmetic_operator
}

sig comparison_expression extends expression {
  left: one expression,
  right: one expression,
  operator: one comparison_operator
}

sig logical_expression extends expression {
  left: one expression,
  right: one expression,
  operator: one logical_operator
}

abstract sig literal extends expression {}

sig integer_literal extends literal {
  value: one int
}

sig float_literal extends literal {
  value: one float
}

sig string_literal extends literal {
  value: one string
}

sig boolean_literal extends literal {
  value: one boolean
}

sig array_literal extends literal {
  elements: set expression
}

sig array_access_expression extends expression {
  array: one expression,
  index: one expression
}

sig function_call_expression extends expression {
  function: one function,
  arguments: set expression
}

sig struct_literal_expression extends expression {
  literal: one struct_literal
}

sig member_access_expression extends expression {
  object: one expression,
  member: one identifier
}

sig unary_expression extends expression {
  operator: one unary_operator,
  operand: one expression
}

abstract sig unary_operator {}
sig plus_operator extends unary_operator {}
sig minus_operator extends unary_operator {}
sig not_operator extends unary_operator {}
