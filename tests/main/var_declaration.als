module var_declaration

open util/ordering[Time]
open util/boolean
open grammer_core

assert variable_declarations_have_type_and_value {
  all v: VariableDeclaration | some v.var_type and some v.value
}

assert variable_names_are_unique_within_scope {
  all s: Scope | all disj v1, v2: s.variables | v1.var_name != v2.var_name
}

assert variables_have_valid_types {
  all v: VariableDeclaration | v.var_type in Boolean + Percent + Money + Date + Duration + String + IdentifierType
}

assert variable_values_match_type {
  all v: VariableDeclaration |
    (v.var_type = Boolean => v.value in BooleanLiteral) and
    (v.var_type = Percent => v.value in PercentValue) and
    (v.var_type = Money => v.value in MoneyValue) and
    (v.var_type = Date => v.value in DateValue) and
    (v.var_type = Duration => v.value in DurationValue) and
    (v.var_type = String => v.value in StringLiteral) and
    (v.var_type = IdentifierType => v.value in Identifier)
}

assert variable_initialization_expression_validity {
  all v: VariableDeclaration | check_variable_initialization_expression_validity(v.value)
}

assert variable_shadowing_allowed {
  all s: Scope, v: s.variables | let outer_scope = find_outer_scope_with_variable(v.var_name, s) in outer_scope != null implies v.value != outer_scope.variables[v.var_name].value
}

assert variable_scope_lifetime {
  all v: VariableDeclaration | check_variable_scope_lifetime(v)
}

assert variable_constantness {
  all v: VariableDeclaration | check_variable_constantness(v)
}

assert variable_mutability {
  all v: VariableDeclaration | check_variable_mutability(v)
}

assert variable_type_inference {
  all v: VariableDeclaration | check_variable_type_inference(v)
}

assert variable_default_values {
  all v: VariableDeclaration | check_variable_default_values(v)
}

check variable_declarations_have_type_and_value for 25
check variable_names_are_unique_within_scope for 25
check variables_have_valid_types for 25
check variable_values_match_type for 25
check variable_initialization_expression_validity for 25
check variable_shadowing_allowed for 25
check variable_scope_lifetime for 25
check variable_constantness for 25
check variable_mutability for 25
check variable_type_inference for 25
check variable_default_values for 25

run {} for 200
