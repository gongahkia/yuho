module expression

open util/ordering[Time]
open util/boolean
open grammarCore

assert AllExpressionsHaveType {
    all e: Expression | some e.type
}

assert ExpressionsHaveValidTypes {
    all e: Expression | e.type in Boolean + Percent + Money + Date + Duration + String + IdentifierType
}

assert IntegerAdditionIsCorrect {
    all il1, il2: IntegerLiteral | (il1.value + il2.value) = (il2.value + il1.value)
}

assert FloatMultiplicationIsCorrect {
    all fl1, fl2: FloatLiteral | (fl1.value * fl2.value) = (fl2.value * fl1.value)
}

assert AndOperationIsCommutative {
    all le: LogicalExpression | (le.left and le.right) = (le.right and le.left)
}

assert OrOperationIsAssociative {
    all le1, le2, le3: LogicalExpression | ((le1.left or le2.left) or le3.left) = (le1.left or (le2.left or le3.left))
}

assert BooleanLiteralNegation {
    all bl: BooleanLiteral | not bl.value != bl.value
}

assert StringConcatenationIsAssociative {
    all sl1, sl2, sl3: StringLiteral | ((sl1.value + sl2.value) + sl3.value) = (sl1.value + (sl2.value + sl3.value))
}

check AllExpressionsHaveType for 50
check ExpressionsHaveValidTypes for 50
check IntegerAdditionIsCorrect for 50
check FloatMultiplicationIsCorrect for 50
check AndOperationIsCommutative for 20
check OrOperationIsAssociative for 20
check BooleanLiteralNegation for 20
check StringConcatenationIsAssociative for 40

run {} for 200
