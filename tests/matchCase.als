module matchCase

open util/ordering[Time]
open util/boolean
open grammarCore

assert MatchCaseHasAtLeastOneCase {
    all m: MatchCase | some m.cases
}

assert MatchCaseConditionsAreUnique {
    all m: MatchCase | all disj c1, c2: m.cases | c1.condition != c2.condition
}

assert MatchCaseConditionsHaveValidExpressions {
    all m: MatchCase | all c: m.cases | some c.condition and some c.consequence
}

assert MatchCaseConsequencesAreValidExpressions {
    all m: MatchCase | all c: m.cases | some c.consequence
}

fact MatchCaseFact {
    some MatchCase | some cases
}

fact UniqueMatchCaseConditionsFact {
    all m: MatchCase | all disj c1, c2: m.cases | c1.condition != c2.condition
}

fact ValidMatchCaseExpressionsFact {
    all m: MatchCase | all c: m.cases | some c.condition and some c.consequence
}

fact MatchCaseConsequencesFact {
    all m: MatchCase | all c: m.cases | some c.consequence
}

check MatchCaseHasAtLeastOneCase for 25
check MatchCaseConditionsAreUnique for 25
check MatchCaseConditionsHaveValidExpressions for 25
check MatchCaseConsequencesAreValidExpressions for 25

run {} for 25
