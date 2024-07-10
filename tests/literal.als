module literal

open util/ordering[Time]
open util/boolean
open grammarCore

assert ValidLiteralTypes {
    all l: Literal | l in IntegerLiteral + FloatLiteral + StringLiteral + BooleanLiteral
}

fact LiteralsFact {
    some LiteralExpression
}

fact ValidLiteralTypesFact {
    all l: Literal | l in IntegerLiteral + FloatLiteral + StringLiteral + BooleanLiteral
}

check ValidLiteralTypes for 25

run {} for 25
