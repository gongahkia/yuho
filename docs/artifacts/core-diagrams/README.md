# Native Haskell semantic-diagram fixtures

These retained artifacts are emitted by the authoritative Haskell `yuho diagram` command from checked Core Yuho. JSON uses `yuho.semantic-graph/v0.1`; SVG is standalone and directly emitted by Haskell. Neither format embeds a generation time or checkout path.

| Stem | Input and view | Semantic purpose |
|---|---|---|
| `modular-release-rule` | modular Singapore release, `rule` | Full normalized rule graph. |
| `offence-exception-penalty` | rash-endangerment exception-defeat scenario, `rule` | Offence, attached exception and candidate penalty. |
| `module-composition` | modular Singapore release, `modules` | Exact imports, explicit exports/uses and host composition. |
| `temporal-selection` | fictional boundary scenario, `rule` | Frontend-owned interval selection. |
| `multi-allegation-case` | property/deception showcase, `case` | Ordered allegations and typed shared-fact bindings. |
| `satisfied-defeated-unresolved-trace` | person/harm showcase, `trace` | Satisfied exception guard, defeated allegation and unresolved allegation. |
| `registered-presumption-trace` | fictional active presumption, `trace` | Trigger, rebuttal, target and derivation state. |

Each stem has byte-deterministic `.json` and `.svg` forms. Regenerate into an empty directory with the commands documented in the [Haskell DSL guide](../HASKELL-YUHO-DSL-GUIDE.md), compare twice, parse every SVG as XML, then replace these reviewed fixtures only when the semantic graph intentionally changes.

These are technical research views. They do not state guilt, conviction, acquittal, liability or sentence.
