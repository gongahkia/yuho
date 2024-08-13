module assertion

open util/ordering[Time]
open util/boolean
open grammarCore

assert all_assertions_hold { 
  all a: Assertion | check a for 5 
}
assert valid_assertions { 
  all a: Assertion | some a 
}
assert all_variables_have_type_and_value { 
  all v: VariableDeclaration | some v.var_type and some v.value 
}
assert structs_have_unique_names { 
  all disj s1, s2: Struct | s1.name != s2.name 
}
assert functions_have_return_type_and_body { 
  all f: Function | some f.return_type and some f.func_name and some f.body 
}
assert match_cases_have_at_least_one_case { 
  all m: MatchCase | some m.cases 
}
assert valid_type_conversions { 
  all tc: TypeConversion | some tc.source_type and some tc.target_type and is_valid_conversion(tc.source_type, tc.target_type) 
}
assert operator_precedence { 
  all e: Expression | check_operator_precedence(e) 
}
assert expression_evaluation { 
  all e: Expression | some e.result 
}
assert if_else_statement_correctness { 
  all if_stmt: IfStatement | (some if_stmt.condition and some if_stmt.then_block) or (some if_stmt.condition and some if_stmt.else_block) 
}
assert function_call_correctness { 
  all fc: FunctionCall | some fc.function and (all p: fc.parameters | some p.value) 
}
assert struct_instance_correctness { 
  all si: StructInstance | some si.struct_type and all f: si.fields | some f.value 
}
assert valid_variable_types { 
  all v: VariableDeclaration | is_valid_type(v.var_type) 
}
assert function_parameter_types { 
  all f: Function, p: f.parameters | is_valid_type(p.type) 
}
assert match_case_exhaustiveness { 
  all m: MatchCase | covers_all_cases(m.expression, m.cases) 
}
assert invalid_function_calls { 
  no fc: FunctionCall | is_invalid_function_call(fc) 
}
assert invalid_struct_definitions { 
  no s: Struct | is_invalid_struct_definition(s) 
}
assert complex_match_cases { 
  all m: MatchCase | check_complex_match_case(m) 
}

check all_assertions_hold for 50
check valid_assertions for 50
check all_variables_have_type_and_value for 50
check structs_have_unique_names for 50
check functions_have_return_type_and_body for 50
check match_cases_have_at_least_one_case for 50
check valid_type_conversions for 50
check operator_precedence for 50
check expression_evaluation for 50
check if_else_statement_correctness for 50
check function_call_correctness for 50
check struct_instance_correctness for 50
check valid_variable_types for 50
check function_parameter_types for 50
check match_case_exhaustiveness for 50
check invalid_function_calls for 50
check invalid_struct_definitions for 50
check complex_match_cases for 50

run {} for 200
