module expression

open util/ordering[Time]
open util/boolean
open grammarCore

assert all_expressions_have_type {
  all e: Expression | some e.type
}

assert expressions_have_valid_types {
  all e: Expression | e.type in Boolean + Percent + Money + Date + Duration + String + IdentifierType
}

assert integer_addition_is_commutative {
  all il1, il2: IntegerLiteral | (il1.value + il2.value) = (il2.value + il1.value)
}

assert float_multiplication_is_commutative {
  all fl1, fl2: FloatLiteral | (fl1.value * fl2.value) = (fl2.value * fl1.value)
}

assert and_operation_is_commutative {
  all le: LogicalExpression | (le.left and le.right) = (le.right and le.left)
}

assert or_operation_is_associative {
  all le1, le2, le3: LogicalExpression | ((le1.left or le2.left) or le3.left) = (le1.left or (le2.left or le3.left))
}

assert boolean_literal_negation {
  all bl: BooleanLiteral | not bl.value != bl.value
}

assert string_concatenation_is_associative {
  all sl1, sl2, sl3: StringLiteral | ((sl1.value + sl2.value) + sl3.value) = (sl1.value + (sl2.value + sl3.value))
}

assert type_compatibility_for_binary_operators {
  all be: BinaryExpression | is_compatible(be.left.type, be.operator, be.right.type)
}

assert correct_operator_precedence {
  all e: Expression | check_operator_precedence(e)
}

assert short_circuit_evaluation {
  all le: LogicalExpression | check_short_circuit_evaluation(le)
}

assert constant_folding {
  all ce: ConstantExpression | check_constant_folding(ce)
}

assert arithmetic_overflow {
  no ae: ArithmeticExpression | is_arithmetic_overflow(ae)
}

assert division_by_zero {
  no de: DivisionExpression | de.divisor = 0
}

assert integer_literal_range {
  all il: IntegerLiteral | il.value >= INT_MIN and il.value <= INT_MAX
}

assert float_literal_precision {
  all fl: FloatLiteral | check_float_precision(fl)
}

assert unary_operator_correctness {
  all ue: UnaryExpression | check_unary_operator_correctness(ue)
}

assert binary_operator_compatibility {
  all be: BinaryExpression | check_binary_operator_compatibility(be)
}

assert ternary_operator_correctness {
  all te: TernaryExpression | check_ternary_operator_correctness(te)
}

assert parenthesis_precedence {
  all e: Expression | check_parenthesis_precedence(e)
}

assert function_call_argument_count {
  all fc: FunctionCall | fc.arguments.size = fc.function.parameters.size
}

assert array_index_in_bounds {
  all ae: ArrayAccess | ae.index >= 0 and ae.index < ae.array.size
}

assert struct_member_access {
  all sa: StructAccess | sa.member in sa.struct_type.members
}

assert type_conversion_validity {
  all tc: TypeConversion | is_valid_type_conversion(tc.source_type, tc.target_type)
}

check all_expressions_have_type for 50
check expressions_have_valid_types for 50
check integer_addition_is_commutative for 50
check float_multiplication_is_commutative for 50
check and_operation_is_commutative for 20
check or_operation_is_associative for 20
check boolean_literal_negation for 20
check string_concatenation_is_associative for 40
check type_compatibility_for_binary_operators for 50
check correct_operator_precedence for 50
check short_circuit_evaluation for 30
check constant_folding for 30
check arithmetic_overflow for 30
check division_by_zero for 30
check integer_literal_range for 50
check float_literal_precision for 50
check unary_operator_correctness for 50
check binary_operator_compatibility for 50
check ternary_operator_correctness for 30
check parenthesis_precedence for 50
check function_call_argument_count for 50
check array_index_in_bounds for 50
check struct_member_access for 50
check type_conversion_validity for 50

run {} for 200
