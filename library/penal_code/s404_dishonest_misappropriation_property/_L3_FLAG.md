# s404 — L3 flag

- failed: 8
- reason: The encoding introduces an `any_of` split between an invented `ordinary_case` and `clerk_or_servant_case`, but the canonical text states one offence with a higher imprisonment ceiling if the offender was the deceased's clerk or servant.
- suggested fix: Remove the fabricated offence-level disjunction and model the clerk-or-servant status only as the predicate for the enhanced penalty branch.
