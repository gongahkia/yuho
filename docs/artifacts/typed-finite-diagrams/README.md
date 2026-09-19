# Core Yuho v0.2 native diagram fixtures

These eight retained artifacts are generated directly by the authoritative Haskell `yuho diagram` command from checked typed-finite Core programs. JSON remains the additive `yuho.semantic-graph/v0.1` format with new stable node and edge kinds; SVG is standalone XML. Neither format contains timestamps or absolute checkout paths.

| Pair | Input/view | Purpose |
|---|---|---|
| `fictional-rule` | fictional typed-rules model, `rule` | entities, predicates, scalars, quantifiers, cardinality, negation, rules and propositions |
| `module-composition` | modular typed-rules model, `modules` | exact imports, typed exports and explicit priority |
| `multi-allegation-case` | typed-rules case, `case` | independent allegations and shared ground classification |
| `conflict-trace` | fictional typed-rules model, `trace` | satisfied, defeated/unresolved and explicit conflict states |

`TypedFiniteChecks` regenerates the semantic graphs in memory and requires byte identity with every retained JSON/SVG file. The release verification also parses all SVG as XML.
