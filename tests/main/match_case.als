module match_case

open util/ordering[Time]
open util/boolean
open grammarCore

assert match_case_has_at_least_one_case {
  all m: MatchCase | some m.cases
}

assert match_case_conditions_are_unique {
  all m: MatchCase | all disj c1, c2: m.cases | c1.condition != c2.condition
}

assert match_case_conditions_have_valid_expressions {
  all m: MatchCase | all c: m.cases | some c.condition and some c.consequence
}

assert match_case_consequences_have_valid_expressions {
  all m: MatchCase | all c: m.cases | some c.consequence
}

assert match_case_exhaustiveness {
  all m: MatchCase | check_match_case_exhaustiveness(m)
}

assert match_case_condition_types {
  all m: MatchCase, c: m.cases | c.condition.type = m.matchValue.type
}

assert match_case_consequence_types {
  all m: MatchCase, c: m.cases | c.consequence.type = m.matchValue.type
}

assert match_case_condition_expressions {
  all m: MatchCase, c: m.cases | check_match_case_condition_expressions(c.condition)
}

assert match_case_consequence_expressions {
  all m: MatchCase, c: m.cases | check_match_case_consequence_expressions(c.consequence)
}

assert match_case_default_case {
  all m: MatchCase | some c: m.cases | c.condition = null
}

check match_case_has_at_least_one_case for 25
check match_case_conditions_are_unique for 25
check match_case_conditions_have_valid_expressions for 25
check match_case_consequences_have_valid_expressions for 25
check match_case_exhaustiveness for 25
check match_case_condition_types for 25
check match_case_consequence_types for 25
check match_case_condition_expressions for 25
check match_case_consequence_expressions for 25
check match_case_default_case for 25

run {} for 100
