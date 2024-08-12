module assertion

open util/ordering[Time]
open util/boolean
open grammarCore

assert AllAssertionsHold {
    all a: Assertion | check a for 5
}

assert ValidAssertions {
    all a: Assertion | some a
}

assert AllVariablesHaveTypeAndValue {
    all v: VariableDeclaration | some v.varType and some v.value
}

assert StructsHaveUniqueNames {
    all disj s1, s2: Struct | s1.name != s2.name
}

assert FunctionsHaveReturnTypeAndBody {
    all f: Function | some f.returnType and some f.funcName and some f.body
}

assert MatchCasesHaveAtLeastOneCase {
    all m: MatchCase | some m.cases
}

check AllAssertionsHold for 50
check ValidAssertions for 50
check AllVariablesHaveTypeAndValue for 50
check StructsHaveUniqueNames for 50
check FunctionsHaveReturnTypeAndBody for 50
check MatchCasesHaveAtLeastOneCase for 50

run {} for 200
