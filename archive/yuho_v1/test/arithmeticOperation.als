module arithmeticOperation

open util/ordering[Time]
open util/boolean
open grammarCore

assert ValidArithmeticOperators {
    all op: ArithmeticOperator | op in Addition + Subtraction + Multiplication + Division + IntegerDivision + Modulo
}

assert ArithmeticOperationsHaveValidOperands {
    all ae: ArithmeticExpression | some ae.left and some ae.right
}

assert ArithmeticExpressionsHaveMatchingTypes {
    all ae: ArithmeticExpression | ae.left.type = ae.right.type
}

fact ArithmeticOperationsFact {
    some ArithmeticExpression
}

fact ValidArithmeticOperatorsFact {
    all op: ArithmeticOperator | op in Addition + Subtraction + Multiplication + Division + IntegerDivision + Modulo
}

fact ArithmeticOperandsFact {
    all ae: ArithmeticExpression | some ae.left and some ae.right
}

fact MatchingArithmeticTypesFact {
    all ae: ArithmeticExpression | ae.left.type = ae.right.type
}

check ValidArithmeticOperators for 25
check ArithmeticOperationsHaveValidOperands for 25
check ArithmeticExpressionsHaveMatchingTypes for 25

run {} for 25
