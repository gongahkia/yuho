module varDeclaration

open util/ordering[Time]
open util/boolean
open grammarCore

assert VariableDeclarationsHaveTypeAndValue {
    all v: VariableDeclaration | some v.varType and some v.value
}

assert VariableNamesAreUniqueWithinScope {
    all s: Scope | all disj v1, v2: s.variables | v1.varName != v2.varName
}

assert VariablesHaveValidTypes {
    all v: VariableDeclaration | v.varType in Boolean + Percent + Money + Date + Duration + String + IdentifierType
}

assert VariableValuesMatchType {
    all v: VariableDeclaration |
        (v.varType = Boolean => v.value in BooleanLiteral) and
        (v.varType = Percent => v.value in PercentValue) and
        (v.varType = Money => v.value in MoneyValue) and
        (v.varType = Date => v.value in DateValue) and
        (v.varType = Duration => v.value in DurationValue) and
        (v.varType = String => v.value in StringLiteral) and
        (v.varType = IdentifierType => v.value in Identifier)
}

fact VariableDeclarationsFact {
    some VariableDeclaration
}

fact VariableDeclarationsMultipleScopes {
    some s: Scope | #s.variables > 1
}

fact ValidVariableTypesFact {
    all v: VariableDeclaration | v.varType in Boolean + Percent + Money + Date + Duration + String + IdentifierType
}

fact MatchingVariableValuesFact {
    all v: VariableDeclaration |
        (v.varType = Boolean => v.value in BooleanLiteral) and
        (v.varType = Percent => v.value in PercentValue) and
        (v.varType = Money => v.value in MoneyValue) and
        (v.varType = Date => v.value in DateValue) and
        (v.varType = Duration => v.value in DurationValue) and
        (v.varType = String => v.value in StringLiteral) and
        (v.varType = IdentifierType => v.value in Identifier)
}

check VariableDeclarationsHaveTypeAndValue for 25
check VariableNamesAreUniqueWithinScope for 25
check VariablesHaveValidTypes for 25
check VariableValuesMatchType for 25

run {} for 25
