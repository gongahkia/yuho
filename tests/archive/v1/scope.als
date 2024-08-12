module scope

open util/ordering[Time]
open util/boolean
open grammarCore

assert ScopeHasNameAndVariables {
    all s: Scope | some s.name and some s.variables
}

assert ScopeVariablesHaveValidTypes {
    all s: Scope | all v: s.variables | v.varType in Boolean + Percent + Money + Date + Duration + String + IdentifierType
}

assert UniqueVariableNamesInScope {
    all s: Scope | all disj v1, v2: s.variables | v1.varName != v2.varName
}

assert VariablesHaveValuesInScope {
    all s: Scope | all v: s.variables | some v.value
}

fact ScopesFact {
    some Scope | some variables
}

fact ValidScopeVariableTypesFact {
    all s: Scope | all v: s.variables | v.varType in Boolean + Percent + Money + Date + Duration + String + IdentifierType
}

fact UniqueVariableNamesFact {
    all s: Scope | all disj v1, v2: s.variables | v1.varName != v2.varName
}

fact VariablesHaveValuesFact {
    all s: Scope | all v: s.variables | some v.value
}

check ScopeHasNameAndVariables for 25
check ScopeVariablesHaveValidTypes for 25
check UniqueVariableNamesInScope for 25
check VariablesHaveValuesInScope for 25

run {} for 25
