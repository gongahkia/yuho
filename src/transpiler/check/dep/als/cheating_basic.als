module cheating_basic

abstract sig party {}
one sig accused extends party {}
one sig victim extends party {}

abstract sig attribution_type {}
one sig sole_inducment extends attribution_type {}
one sig not_sole_inducement extends attribution_type {}
one sig na_attribution extends attribution_type {}

abstract sig deception_type {}
one sig fraudulently extends deception_type {}
one sig dishonestly extends deception_type {}
one sig na_deception extends deception_type {}

abstract sig inducement_type {}
one sig deliver_property extends inducement_type {}
one sig consent_retain_property extends inducement_type {}
one sig do_or_omit extends inducement_type {}
one sig na_inducement extends inducement_type {}

abstract sig damage_harm_type {}
one sig body extends damage_harm_type {}
one sig mind extends damage_harm_type {}
one sig reputation extends damage_harm_type {}
one sig property extends damage_harm_type {}
one sig na_damage_harm extends damage_harm_type {}

abstract sig consequence_definition {}
one sig said_to_cheat extends consequence_definition {}
one sig not_said_to_cheat extends consequence_definition {}

sig cheating {
    accused: one party,
    action: one String,
    victim: one party,
    attribution: one attribution_type,
    deception: one deception_type,
    inducement: one inducement_type,
    causes_damage_harm: one Bool,
    damage_harm_result: some damage_harm_type,
    definition: one consequence_definition
}

fact {
    all c: cheating | {
        c.definition = 
            (c.attribution = sole_inducment or c.attribution = not_sole_inducement) implies (c.definition = c.deception) and
            (c.deception = fraudulently or c.deception = dishonestly) implies (c.definition = c.inducement) and
            (c.inducement = deliver_property or c.inducement = consent_retain_property or c.inducement = do_or_omit) implies (c.definition = c.causes_damage_harm) and
            (c.causes_damage_harm = true) implies (c.definition = c.damage_harm_result) and
            (na_damage_harm in c.damage_harm_result) implies (c.definition = not_said_to_cheat) and
            (c.damage_harm_result = body or c.damage_harm_result = mind or c.damage_harm_result = reputation or c.damage_harm_result = property) implies (c.definition = said_to_cheat)
    }
}

assert test {
    some c: cheating | {
        c.accused = accused and
        c.victim = victim and
        c.action = "deceiving" and
        c.attribution in sole_inducment + not_sole_inducement + na_attribution and
        c.deception in fraudulently + dishonestly + na_deception and
        c.inducement in deliver_property + consent_retain_property + do_or_omit + na_inducement and
        c.causes_damage_harm in true + false and
        c.damage_harm_result in body + mind + reputation + property + na_damage_harm
    }
}
