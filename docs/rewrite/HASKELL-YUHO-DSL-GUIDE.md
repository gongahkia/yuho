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

A checked model declares `variant SuppliedProofStatus-v1`, jurisdiction and research purpose, a request and policy, exactly one source-text source and one synthetic-status source, source quotes, contextual burden metadata, scope assumptions, typed rules and non-executable limitations. Rules use typed `element` leaves and source-ordered `all`/`any` groups. Supported POCs include statutory definitions, multiple candidate offences, general exceptions, actors and roles, s 107 participation routes, s 511 attempt stages, actor-scoped s 84 instances and ordered bounded analysis cases.

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

An import does not execute a model, expose private declarations or attach an exception. A host may compose explicitly exported definitions, offences, general exceptions and candidate penalties from independent source graphs. Participation and attempt modules remain specialised whole graphs. Existing compatibility-view modules and unqualified single-file models remain valid. Module identity describes authored content; it does not select law for a conduct date. Module names, versions and aliases are diagnostic and explanatory metadata and do not enter KernelInput.

The release host is the concrete independent-composition example: it imports seven separate source graphs, selects seven offences, four exceptions and seven penalties, then attaches exceptions across module boundaries. For example:

```yh
import singapore.penal-code.misappropriation version 1.0.0 as misappropriation;
import singapore.penal-code.receiving-property version 1.0.0 as receiving;
use offence misappropriation::o:misappropriation;
use offence receiving::o:receiving-property;
use general-exception misappropriation::x:section79;
use candidate-penalty receiving::pen:section411;
attach misappropriation::x:section79 to offence receiving::o:receiving-property;
```

See [`modular-singapore-criminal-law-release.yh`](../../research/singapore/research-release/modular-singapore-criminal-law-release.yh) for the complete host. The earlier theft/hurt and cheating/mischief module files remain compatibility views over pre-existing source graphs and are identified as such.

Candidate penalties are exported and selected with the same typed mechanism:

```yh
export candidate-penalty pen:section403;
use candidate-penalty misappropriation::pen:section403;
```

The resolver rejects colliding final legal identities rather than silently prefixing them. See the [composition and lowering note](HASKELL-MODULE-COMPOSITION-AND-LOWERING.md).

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

## Multi-allegation cases

Cases contain 1–32 allegations in authored order. The target is a closed typed sum: `offence`, `participation` or `attempt`. A broad offence host permits repeated and different offence targets; the specialised participation/attempt host permits its typed targets. Case-level roles may name different actors, and primitive facts are shared only by explicit compatible bindings.

```yh
analysis-case case:property-deception-showcase
  model "modular-singapore-criminal-law-release.yh" {
  bind role:property-actor to actor:person-1;
  supplied-fact fact:movable kind circumstance
    subject actor:person-1 target o:misappropriation
    status proved reason "synthetic classification";

  allegation a:first analyse offence o:misappropriation
    for role:property-actor {
      assume a:bounded-section403-expression;
      bind-fact fact:movable to input f:403-movable-property;
      // remaining primitive classifications
    }
}
```

Derived definition outputs, rule results, penalty selection and final statuses cannot be bound as case facts. There is no allegation-order inference and no aggregate case result.

[`case-modular-warehouse-shared.yh`](../../research/singapore/abetment-routes-pilot/case-modular-warehouse-shared.yh) loads a modular sibling model and checks principal theft, bounded s 107/s 109 participation and s 511 attempt as three allegations. It binds shared primitive case facts explicitly and keeps each actor's s 84 instance isolated. Run it without `--scenario`:

```sh
"$YUHO" check ../../research/singapore/abetment-routes-pilot/case-modular-warehouse-shared.yh
"$YUHO" compile ../../research/singapore/abetment-routes-pilot/case-modular-warehouse-shared.yh
"$YUHO" run ../../research/singapore/abetment-routes-pilot/case-modular-warehouse-shared.yh
"$YUHO" explain ../../research/singapore/abetment-routes-pilot/case-modular-warehouse-shared.yh
```

The case result has allegation-specific statuses and no aggregate status, guilt conclusion or sentencing outcome.

## Registered-presumption technical subprograms

`presumption-program` makes the existing registered-derivation kernel boundary authorable without pretending that it is an evidence assessment or folding it into an offence request:

```yh
presumption-program FictionalAuthorizationPresumptionActive-v1 {
  base-model "restricted_entry.yh";
  base-scenario "scenario_presumption_active.yh";
  burden bearer fictional-proponent standard supplied-classification
    note "Fictional context only; no evidence assessment";
  presumption pres:fictional-authorization
    target f:no-authorization
    source src:fictional-rule
    trigger f:knowledge
    rebuttal f:rescue-purpose;
}
```

The target, trigger and rebuttal must already be primitive proof facts in the compiled base. Explanations distinguish `active`, `inactive`, `rebutted` and `unresolved`, as well as direct and effective satisfaction. Burden bearer and standard are authored contextual annotations. Evidence Act s 107 remains the bounded burden context already used by the Singapore exception models; it is not misdescribed as a registered presumption.

## Top-level syntax map

| Construct | Starts with | Separate input |
|---|---|---|
| Ordinary research model | `model` | `scenario ... for ...` |
| Exact statutory module | `statutory-module` | none |
| Composed host | `modular-model` | ordinary scenario |
| Temporal expression set | `temporal-model` | `temporal-scenario` |
| Multi-allegation case | `analysis-case` | allegation bodies are embedded |
| Presumption subprogram | `presumption-program` | names a base model and scenario |

The [research-release quick start](../../research/singapore/research-release/README.md) is the recommended entry point. The [capability matrix](HASKELL-RESEARCH-RELEASE-v0.1.md) classifies every major feature as supported, bounded, deferred or out of scope.

## Runnable corpus

The discoverable inventory and limits are in the [Singapore corpus index](../../research/singapore/CORPUS-INDEX.md). The new [cheating and mischief model](../../research/singapore/offence-corpus-pilot/modular-cheating-mischief.yh) has 20 synthetic decision paths and representative explanation snapshots. Existing hurt, theft, definitions, participation, attempt and actor-scoped exception models remain compatibility fixtures.
