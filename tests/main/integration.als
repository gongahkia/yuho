module integration

open util/ordering[Time]
open util/boolean
open grammer_core

assert core_components_exist {
  all c: CoreComponent | some c
}

assert modules_exist {
  all m: Module | some m
}

assert scope_variable_usage {
  all s: Scope | s.variables in s.body.statements.expression.var_name
}

assert function_parameters_have_valid_types {
  all f: Function | all p: f.parameters | p.param_type in Boolean + Percent + Money + Date + Duration + String + IdentifierType
}

assert struct_fields_have_valid_types {
  all st: Struct | all f: st.fields | f.field_type in Boolean + Percent + Money + Date + Duration + String + IdentifierType
}

assert type_consistency_between_declarations_and_usages {
  all v: VariableDeclaration | v.var_type = lookup_type(v.var_name)
}

assert function_return_type_consistency {
  all f: Function, r: f.body.return_statement | f.return_type = r.return_value.type
}

assert struct_literal_field_compatibility {
  all sl: StructLiteral | all fv: sl.field_values | let s = lookup_struct(sl.struct_name) in fv.fieldName in s.fields and fv.value.type = s.fields[fv.fieldName].fieldType
}

assert member_access_type_compatibility {
  all ma: MemberAccessExpression | let st = lookup_struct(ma.object.type) in ma.member in st.fields
}

assert function_call_argument_compatibility {
  all fc: FunctionCall | fc.function.parameters.size = fc.arguments.size and all i: Int | i in 0..fc.arguments.size - 1 implies fc.arguments[i].type = fc.function.parameters[i].param_type
}

assert scope_nesting {
  all s1, s2: Scope | s1 in s2.scopes implies s1.name != s2.name
}

assert no_shadowing {
  all s: Scope, v1, v2: s.variables | v1 != v2 implies v1.varName != v2.varName
}

check core_components_exist for 50
check modules_exist for 50
check scope_variable_usage for 50
check function_parameters_have_valid_types for 50
check struct_fields_have_valid_types for 50
check type_consistency_between_declarations_and_usages for 50
check function_return_type_consistency for 50
check struct_literal_field_compatibility for 50
check member_access_type_compatibility for 50
check function_call_argument_compatibility for 50
check scope_nesting for 50
check no_shadowing for 50

run {} for 200
