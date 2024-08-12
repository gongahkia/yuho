module function

open util/ordering[Time]
open util/boolean
open grammarCore

assert FunctionsHaveReturnTypeAndBody {
    all f: Function | some f.returnType and some f.funcName and some f.body
}

assert FunctionParametersHaveUniqueNames {
    all f: Function | all disj p1, p2: f.parameters | p1.paramName != p2.paramName
}

assert FunctionParametersHaveValidTypes {
    all f: Function | all p: f.parameters | p.paramType in Boolean + Percent + Money + Date + Duration + String + IdentifierType
}

assert FunctionBodiesHaveStatements {
    all f: Function | some f.body.statements
}

fact FunctionsFact {
    some f: Function | some f.parameters and some f.body
}

fact UniqueFunctionParameterNamesFact {
    all f: Function | all disj p1, p2: f.parameters | p1.paramName != p2.paramName
}

fact ValidFunctionParameterTypesFact {
    all f: Function | all p: f.parameters | p.paramType in Boolean + Percent + Money + Date + Duration + String + IdentifierType
}

fact FunctionBodiesStatementsFact {
    all f: Function | some f.body.statements
}

check FunctionsHaveReturnTypeAndBody for 25
check FunctionParametersHaveUniqueNames for 25
check FunctionParametersHaveValidTypes for 25
check FunctionBodiesHaveStatements for 25

run {} for 25
