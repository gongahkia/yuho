module grammerCore

open util/ordering[Time]
open util/boolean

// ----- ABSTRACT SYNTAX DEFINITION VIA SIGNATURES -----

abstract sig Letter {}
abstract sig Digit {}
abstract sig Identifier {}

abstract sig Type {}
abstract sig Boolean extends Type {}
abstract sig Percent extends Type {}
abstract sig Money extends Type {}
abstract sig Date extends Type {}
abstract sig Duration extends Type {}
abstract sig String extends Type {}
abstract sig IdentifierType extends Type {}

abstract sig ArithmeticOperator {}
abstract sig ComparisonOperator {}
abstract sig LogicalOperator {}

sig True extends Boolean {}
sig False extends Boolean {}
sig Pass {}

sig PercentValue extends Percent {
    value: one Int
}

sig MoneyValue extends Money {
    value: one Int
}

sig DateValue extends Date {
    day: one Int,
    month: one Int,
    year: one Int
}

sig DurationValue extends Duration {
    days: one Int,
    months: one Int,
    years: one Int
}

sig Scope {
    name: one Identifier,
    variables: set VariableDeclaration
}

sig VariableDeclaration {
    varType: one Type,
    varName: one Identifier,
    value: one Expression
}

sig Struct {
    name: one Identifier,
    fields: set Field
}

sig Field {
    fieldType: one Type,
    fieldName: one Identifier
}

sig StructLiteral {
    structName: one Identifier,
    fieldValues: set FieldValue
}

sig FieldValue {
    fieldName: one Identifier,
    value: one Expression
}

sig Addition extends ArithmeticOperator {}
sig Subtraction extends ArithmeticOperator {}
sig Multiplication extends ArithmeticOperator {}
sig Division extends ArithmeticOperator {}
sig IntegerDivision extends ArithmeticOperator {}
sig Modulo extends ArithmeticOperator {}

sig Equal extends ComparisonOperator {}
sig NotEqual extends ComparisonOperator {}
sig GreaterThan extends ComparisonOperator {}
sig LessThan extends ComparisonOperator {}
sig GreaterEqual extends ComparisonOperator {}
sig LessEqual extends ComparisonOperator {}

sig And extends LogicalOperator {}
sig Or extends LogicalOperator {}
sig Not extends LogicalOperator {}

sig MatchCase {
    matchValue: one Identifier,
    cases: set Case
}

sig Case {
    condition: one Expression,
    consequence: one Expression
}

sig Function {
    returnType: one Type,
    funcName: one Identifier,
    parameters: set Parameter,
    body: one Block
}

sig Parameter {
    paramType: one Type,
    paramName: one Identifier
}

sig Block {
    statements: set Statement
}

sig Statement {}

sig Return extends Statement {
    returnValue: one Expression
}

abstract sig Expression {}

sig VariableExpression extends Expression {
    varName: one Identifier
}

sig LiteralExpression extends Expression {
    literal: one Literal
}

sig ArithmeticExpression extends Expression {
    left: one Expression,
    right: one Expression,
    operator: one ArithmeticOperator
}

sig ComparisonExpression extends Expression {
    left: one Expression,
    right: one Expression,
    operator: one ComparisonOperator
}

sig LogicalExpression extends Expression {
    left: one Expression,
    right: one Expression,
    operator: one LogicalOperator
}

abstract sig Literal extends Expression {}

sig IntegerLiteral extends Literal {
    value: one Int
}

sig FloatLiteral extends Literal {
    value: one Float
}

sig StringLiteral extends Literal {
    value: one String
}

sig BooleanLiteral extends Literal {
    value: one Boolean
}
