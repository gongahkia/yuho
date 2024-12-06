module cheating_detailed

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

sig facts {
    accused: one party,
    action: one String,
    victim: one party
}

sig mental_element {
    deception: one deception_type
}

sig physical_element {
    attribution: one attribution_type,
    inducement: one inducement_type,
    causes_damage_harm: one Bool,
    damage_harm_result: some damage_harm_type
}

sig cheating {
    material_facts: one facts,
    mens_rea: one mental_element,
    actus_reus: one physical_element,
    definition: one consequence_definition
}

fact {
    all c: cheating | {
        c.definition = 
            (c.actus_reus.attribution = sole_inducment or c.actus_reus.attribution = not_sole_inducement) implies (c.definition = c.mens_rea.deception) and
            (c.mens_rea.deception = fraudulently or c.mens_rea.deception = dishonestly) implies (c.definition = c.actus_reus.inducement) and
            (c.actus_reus.inducement = deliver_property or c.actus_reus.inducement = consent_retain_property or c.actus_reus.inducement = do_or_omit) implies (c.definition = c.actus_reus.causes_damage_harm) and
            (c.actus_reus.causes_damage_harm = true) implies (c.definition = c.actus_reus.damage_harm_result) and
            (na_damage_harm in c.actus_reus.damage_harm_result) implies (c.definition = not_said_to_cheat) and
            (c.actus_reus.damage_harm_result = body or c.actus_reus.damage_harm_result = mind or c.actus_reus.damage_harm_result = reputation or c.actus_reus.damage_harm_result = property) implies (c.definition = said_to_cheat)
    }
}

assert test {
    some c: cheating | {
        c.material_facts.accused = accused and
        c.material_facts.victim = victim and
        c.material_facts.action = "deceiving" and
        c.mens_rea.deception in fraudulently + dishonestly + na_deception and
        c.actus_reus.attribution in sole_inducment + not_sole_inducement + na_attribution and
        c.actus_reus.inducement in deliver_property + consent_retain_property + do_or_omit + na_inducement and
        c.actus_reus.causes_damage_harm in true + false and
        c.actus_reus.damage_harm_result in body + mind + reputation + property + na_damage_harm
    }
}
