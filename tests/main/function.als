module function

open util/ordering[Time]
open util/boolean
open grammarCore

assert functions_have_return_type_and_body {
  all f: Function | some f.returnType and some f.funcName and some f.body
}

assert function_parameters_have_unique_names {
  all f: Function | all disj p1, p2: f.parameters | p1.paramName != p2.paramName
}

assert function_parameters_have_valid_types {
  all f: Function | all p: f.parameters | p.paramType in Boolean + Percent + Money + Date + Duration + String + IdentifierType
}

assert function_bodies_have_statements {
  all f: Function | some f.body.statements
}

assert return_type_compatibility {
  all f: Function | is_compatible(f.body.return_expression.type, f.returnType)
}

assert function_call_argument_count {
  all fc: FunctionCall | fc.arguments.size = fc.function.parameters.size
}

assert function_call_argument_types {
  all fc: FunctionCall, i: Int | is_compatible(fc.arguments[i].type, fc.function.parameters[i].paramType)
}

assert recursive_function_termination {
  all f: Function | check_recursive_function_termination(f)
}

assert function_side_effects {
  all f: Function | check_function_side_effects(f)
}

assert function_preconditions {
  all f: Function | check_function_preconditions(f)
}

assert function_postconditions {
  all f: Function | check_function_postconditions(f)
}

check functions_have_return_type_and_body for 25
check function_parameters_have_unique_names for 25
check function_parameters_have_valid_types for 25
check function_bodies_have_statements for 25
check return_type_compatibility for 25
check function_call_argument_count for 25
check function_call_argument_types for 25
check recursive_function_termination for 25
check function_side_effects for 25
check function_preconditions for 25
check function_postconditions for 25

run {} for 200
