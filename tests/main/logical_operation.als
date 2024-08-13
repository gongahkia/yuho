module logical_operation

open util/ordering[Time]
open util/boolean
open grammarCore

assert valid_logical_operators {
  all op: LogicalOperator | op in And + Or + Not
}

assert logical_operations_have_valid_operands {
  all le: LogicalExpression | some le.left and some le.right
}

assert logical_expressions_have_boolean_operands {
  all le: LogicalExpression | le.left.type = Boolean and le.right.type = Boolean
}

assert and_operation_is_commutative {
  all le: LogicalExpression | le.operator = And implies (le.left and le.right) = (le.right and le.left)
}

assert or_operation_is_associative {
  all le1, le2, le3: LogicalExpression | le1.operator = Or and le2.operator = Or and le3.operator = Or implies (((le1.left or le2.left) or le3.left) = (le1.left or (le2.left or le3.left)))
}

assert boolean_literal_negation {
  all bl: BooleanLiteral | not bl.value != bl.value
}

assert short_circuit_evaluation {
  all le: LogicalExpression | check_short_circuit_evaluation(le)
}

assert logical_operator_precedence {
  all le: LogicalExpression | check_logical_operator_precedence(le)
}

assert logical_expression_truth_tables {
  all le: LogicalExpression | check_logical_expression_truth_table(le)
}

assert logical_expression_simplification {
  all le: LogicalExpression | check_logical_expression_simplification(le)
}

assert logical_expression_equivalence {
  all le1, le2: LogicalExpression | le1.equivalentTo(le2) implies (le1.value = le2.value)
}

check valid_logical_operators for 25
check logical_operations_have_valid_operands for 25
check logical_expressions_have_boolean_operands for 25
check and_operation_is_commutative for 20
check or_operation_is_associative for 20
check boolean_literal_negation for 20
check short_circuit_evaluation for 30
check logical_operator_precedence for 30
check logical_expression_truth_tables for 30
check logical_expression_simplification for 30
check logical_expression_equivalence for 30

run {} for 200
