module logicalOperation

open util/ordering[Time]
open util/boolean
open grammarCore

assert ValidLogicalOperators {
    all op: LogicalOperator | op in And + Or + Not
}

assert LogicalOperationsHaveValidOperands {
    all le: LogicalExpression | some le.left and some le.right
}

assert LogicalExpressionsHaveBooleanOperands {
    all le: LogicalExpression | le.left.type = Boolean and le.right.type = Boolean
}

fact LogicalOperationsFact {
    some LogicalExpression
}

fact ValidLogicalOperatorsFact {
    all op: LogicalOperator | op in And + Or + Not
}

fact LogicalOperandsFact {
    all le: LogicalExpression | some le.left and some le.right
}

fact BooleanLogicalOperandsFact {
    all le: LogicalExpression | le.left.type = Boolean and le.right.type = Boolean
}

check ValidLogicalOperators for 25
check LogicalOperationsHaveValidOperands for 25
check LogicalExpressionsHaveBooleanOperands for 25

run {} for 25
