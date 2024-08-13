module scope

open util/ordering[Time]
open util/boolean
open grammarCore

assert scope_has_name_and_variables {
  all s: Scope | some s.name and some s.variables
}

assert scope_variables_have_valid_types {
  all s: Scope | all v: s.variables | v.var_type in Boolean + Percent + Money + Date + Duration + String + IdentifierType
}

assert unique_variable_names_in_scope {
  all s: Scope | all disj v1, v2: s.variables | v1.var_name != v2.var_name
}

assert variables_have_values_in_scope {
  all s: Scope | all v: s.variables | some v.value
}

assert nested_scopes_have_unique_names {
  all s1, s2: Scope | s1.name != s2.name and (s1 in s2.scopes or s2 in s1.scopes) implies s1.name != s2.name
}

assert scope_variable_usage_within_scope {
  all s: Scope | all st: s.statements | all e: st.expression | let v = lookup_variable(e.var_name) in v != null and v.var_name = e.var_name and v in s.variables
}

assert scope_variable_shadowing_allowed {
  all s: Scope, v: s.variables | let outer_scope = find_outer_scope_with_variable(v.var_name, s) in outer_scope != null implies v.value != outer_scope.variables[v.var_name].value
}

assert scope_variable_initialization {
  all s: Scope, v: s.variables | v.value != null
}

assert scope_nesting_depth {
  all s: Scope | check_scope_nesting_depth(s)
}

check scope_has_name_and_variables for 25
check scope_variables_have_valid_types for 25
check unique_variable_names_in_scope for 25
check variables_have_values_in_scope for 25
check nested_scopes_have_unique_names for 25
check scope_variable_usage_within_scope for 50
check scope_variable_shadowing_allowed for 25
check scope_variable_initialization for 25
check scope_nesting_depth for 25

run {} for 200
