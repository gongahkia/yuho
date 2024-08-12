module integration

open util/ordering[Time]
open util/boolean
open grammarCore

assert CoreIntegration {
    all c: CoreComponent | some c
}

assert ModulesIntegration {
    all m: Module | some m
}

assert ScopeVariableUsage {
    all s: Scope | s.variables in s.body.statements.Expression.varName
}

assert FunctionParametersAreValid {
    all f: Function | all p: f.parameters | p.paramType in Boolean + Percent + Money + Date + Duration + String + IdentifierType
}

assert StructFieldsHaveValidTypes {
    all st: Struct | all f: st.fields | f.fieldType in Boolean + Percent + Money + Date + Duration + String + IdentifierType
}

check CoreIntegration for 50
check ModulesIntegration for 50
check ScopeVariableUsage for 50
check FunctionParametersAreValid for 50
check StructFieldsHaveValidTypes for 50

run {} for 200
