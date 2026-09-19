# Native semantic diagrams

`yuho diagram` derives a checked semantic graph from normalized Core Yuho and writes deterministic standalone SVG or canonical JSON directly from Haskell.

```sh
yuho diagram model.yh --scenario scenario.yh --view rule --format svg --output rule.svg
yuho diagram case.yh --view case --format json --output case.json
yuho diagram case.yh --view trace --format svg --output trace.svg
yuho diagram model.yh --scenario scenario.yh --view modules --format svg --output modules.svg
```

Stable node identifiers describe inputs, groups, definitions, offences, exceptions, participation, attempts, penalties, presumptions, typed finite rules, actors, allegations and shared facts. Shapes, borders and labels—not colour alone—distinguish node and trace kinds. Output contains no timestamp or absolute checkout path. Publication is atomic and an existing destination is refused.

Retained deterministic fixtures live under [`docs/artifacts/`](artifacts/). Diagram labels report technical states and always preserve the no-judicial-outcome boundary.
