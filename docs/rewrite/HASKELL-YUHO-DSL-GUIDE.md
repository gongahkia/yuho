# Authoring with the Haskell Yuho research DSL

This guide covers the language implemented by `rewrite/haskell`, not the broader Python 5.1.0 product grammar. The Haskell lexer, source-located AST, resolver, checker, lowering, CLI and in-process kernel are authoritative for these examples. The grammar is a bounded research POC: it exposes criminal-law structure and evaluates synthetic supplied classifications, but it does not assess evidence, determine guilt, select legally applicable law, impose a sentence or make a court disposition.

## Build and four normal commands

From `rewrite/haskell`, use the frozen dependency plan and GHC 9.8.4:

```sh
PATH=/home/gongahkia/.ghcup/bin:/usr/bin:/bin cabal v2-build all --offline --jobs=1
YUHO="$(PATH=/home/gongahkia/.ghcup/bin:/usr/bin:/bin cabal list-bin exe:yuho)"
MODEL=../../research/singapore/offence-corpus-pilot/modular-cheating-mischief.yh
SCENARIO=../../research/singapore/offence-corpus-pilot/scenarios/cheating/01_property_form_satisfied.yh
"$YUHO" check "$MODEL" --scenario "$SCENARIO"
"$YUHO" compile "$MODEL" --scenario "$SCENARIO"
"$YUHO" run "$MODEL" --scenario "$SCENARIO"
"$YUHO" explain "$MODEL" --scenario "$SCENARIO"
```

`compile --output PATH` creates a new output atomically and refuses an existing path. `run` invokes the Haskell kernel in process. None of these commands invokes Python.

## Models, rules and scenarios

A checked model declares `variant SuppliedProofStatus-v1`, jurisdiction and research purpose, a request and policy, exactly one source-text source and one synthetic-status source, source quotes, contextual burden metadata, scope assumptions, typed rules and non-executable limitations. Rules use typed `element` leaves and source-ordered `all`/`any` groups. Supported POCs include statutory definitions, multiple candidate offences, general exceptions, actors and roles, s 107 participation routes, s 511 attempt stages, actor-scoped s 84 instances and three-issue analysis cases.

A separate scenario selects one candidate and supplies every compatible primitive classification as `proved`, `not_proved` or `unresolved(reason)`. It must acknowledge the selected model's scope assumptions. A classification is an external synthetic input, not a finding. Definitions and group results are derived and cannot be supplied.

## Exactly versioned local modules

A module file has the deterministic name `<module-name>@<major.minor.patch>.yh` under the host's explicit local `module-root`. Names contain lowercase letters, digits, dots and hyphens. Versions are exact numeric triples. The current bounded resolver accepts only regular `.yh` files of at most 65,536 bytes, refuses absolute or parent-traversing paths, resolves imports in source order, and rejects cycles, duplicate identities or aliases and more than 32 modules.

```yh
statutory-module singapore.penal-code.section84 version 1.0.0 {
  export general-exception x:section84;
  source-model "section323-section379-definitions.yh";
}
```

Exports are explicit and typed. A non-export is private. A host imports an exact version with an alias, selects one exported model graph, names every declaration it composes, and attaches an exception explicitly:

```yh
modular-model SingaporeModularTheftWithSection84-v1 {
  module-root ".";
  import singapore.penal-code.theft version 1.0.0 as theft;
  import singapore.penal-code.section84 version 1.0.0 as s84;
  use model theft::SingaporePenalCodeStatutoryDefinitionsResearchPrototype-v1;
  use offence theft::o:theft;
  use general-exception s84::x:section84;
  attach s84::x:section84 to offence theft::o:theft;
}
```

An import does not execute a model, expose private declarations or attach an exception. All `use` declarations must refer to one checked authored graph. Existing unqualified single-file models remain valid. Module identity describes authored content; it does not select law for a conduct date. Module names, versions and aliases are diagnostic and explanatory metadata and do not enter KernelInput.

The actor-scoped attachment form is:

```yh
attach warehouse::x:section84 to participation warehouse::p:abet-theft
  for role:alleged-abettor context aid-conduct as xi:abettor-section84;
```

## Authored temporal expressions

A temporal wrapper names at least two complete source models. Intervals must be valid, ordered, non-overlapping and gap-free between adjacent expressions. The final expression may use `open-end`.

```yh
temporal-model FictionalRestrictedAreaTemporal-v1 {
  expression expr:old effective-from 2020-01-01 effective-to 2024-01-01 source-model "old.yh";
  expression expr:new effective-from 2024-01-01 open-end source-model "new.yh" supersedes expr:old;
}
```

The separately supplied wrapper scenario contains the conduct date and points to the ordinary classification scenario:

```yh
temporal-scenario TS01 {
  conduct-date 2024-01-01;
  input "scenario_input.yh";
}
```

Selection is only `effective_from <= conduct_date < effective_to`. Missing or invalid dates, gaps, overlaps, invalid intervals and zero or multiple matches are refusals. `supersedes` is displayed metadata and never selects an expression. The selected expression and interval appear in `explain`; no temporal metadata enters KernelInput. This mechanism chooses among authored assumptions. It does not resolve commencement, savings, retroactivity, continuing conduct or legal currency.

## Candidate penalties and terms

Candidate penalties attach to a declared offence and cite a numeric provision plus a declared source. The Haskell surface currently supports positive integer imprisonment endpoints in days, weeks, months or years; SGD fine endpoints; `not-stated` and maximum `unbounded` endpoints; and `all-of`, `exactly-one-of` and `one-or-more-of` term trees with at least two children.

```yh
candidate-penalties {
  candidate pen:section417 for offence o:cheating source src:pc-offence-corpus provision 417 {
    one-or-more-of term:section417-alternatives {
      imprisonment term:section417-imprisonment minimum not-stated maximum 3 years;
      fine term:section417-fine currency SGD minimum not-stated maximum unbounded;
    }
  }
}
```

The existing `SuppliedProofStatus-v1` kernel validates the term and reports the candidate in `selected_penalties` only when its technical offence branch is finally satisfied. The offence/exception result and the penalty selection remain separate response fields. A selected candidate is not an imposed sentence, and the grammar has no syntax for labelling one as such. Conditions, offender eligibility, enhanced provisions, caning, ancillary orders, concurrent or consecutive terms and sentencing discretion are not authored by this surface.

## Multi-issue cases

[`case-modular-warehouse-shared.yh`](../../research/singapore/abetment-routes-pilot/case-modular-warehouse-shared.yh) loads a modular sibling model and checks principal theft, bounded s 107/s 109 participation and s 511 attempt as three allegations. It binds shared primitive case facts explicitly and keeps each actor's s 84 instance isolated. Run it without `--scenario`:

```sh
"$YUHO" check ../../research/singapore/abetment-routes-pilot/case-modular-warehouse-shared.yh
"$YUHO" compile ../../research/singapore/abetment-routes-pilot/case-modular-warehouse-shared.yh
"$YUHO" run ../../research/singapore/abetment-routes-pilot/case-modular-warehouse-shared.yh
"$YUHO" explain ../../research/singapore/abetment-routes-pilot/case-modular-warehouse-shared.yh
```

The case result has allegation-specific statuses and no aggregate status, guilt conclusion or sentencing outcome.

## Runnable corpus

The discoverable inventory and limits are in the [Singapore corpus index](../../research/singapore/CORPUS-INDEX.md). The new [cheating and mischief model](../../research/singapore/offence-corpus-pilot/modular-cheating-mischief.yh) has 20 synthetic decision paths and representative explanation snapshots. Existing hurt, theft, definitions, participation, attempt and actor-scoped exception models remain compatibility fixtures.
