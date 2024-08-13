module arithmetic_operation

assert valid_arithmetic_operators {
    all op: ArithmeticOperator | op in addition + subtraction + multiplication + division + integer_division + modulo
}
assert arithmetic_operations_have_valid_operands {
    all ae: ArithmeticExpression | some ae.left and some ae.right
}
assert arithmetic_expressions_have_matching_types {
    all ae: ArithmeticExpression | ae.left.type == ae.right.type
}
assert arithmetic_operations_are_commutative {
    all op: ArithmeticOperator, a, b | (op in addition + multiplication) implies (op.apply(a, b) == op.apply(b, a))
}
assert division_by_zero {
    no ae: ArithmeticExpression | (ae.operator == division || ae.operator == integer_division) && ae.right.value == 0
}
assert modulo_with_zero {
    no ae: ArithmeticExpression | ae.operator == modulo && ae.right.value == 0
}
assert integer_division_produces_integer {
    all ae: ArithmeticExpression | ae.operator == integer_division implies (ae.left.type == "Integer" && ae.right.type == "Integer")
}
fact arithmetic_operations_fact {
    some ArithmeticExpression
}
fact valid_arithmetic_operators_fact {
    all op: ArithmeticOperator | op in addition + subtraction + multiplication + division + integer_division + modulo
}
fact arithmetic_operands_fact {
    all ae: ArithmeticExpression | some ae.left and some ae.right
}
fact matching_arithmetic_types_fact {
    all ae: ArithmeticExpression | ae.left.type == ae.right.type
}
fact arithmetic_operations_commutative_fact {
    all op: ArithmeticOperator, a, b | (op in addition + multiplication) implies (op.apply(a, b) == op.apply(b, a))
}
fact no_division_by_zero_fact {
    no ae: ArithmeticExpression | (ae.operator == division || ae.operator == integer_division) && ae.right.value == 0
}
fact no_modulo_by_zero_fact {
    no ae: ArithmeticExpression | ae.operator == modulo && ae.right.value == 0
}
fact integer_division_result_fact {
    all ae: ArithmeticExpression | ae.operator == integer_division implies (ae.left.type == "Integer" && ae.right.type == "Integer")
}

check valid_arithmetic_operators for 25
check arithmetic_operations_have_valid_operands for 25
check arithmetic_expressions_have_matching_types for 25
check arithmetic_operations_are_commutative for 25
check division_by_zero for 25
check modulo_with_zero for 25
check integer_division_produces_integer for 25

run {} for 25
