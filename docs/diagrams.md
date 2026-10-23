# Native semantic diagrams

`yuho diagram` derives a checked semantic graph from normalized Core Yuho and writes deterministic standalone SVG, canonical JSON, or equivalent XML directly from Haskell.

```sh
yuho diagram model.yh --scenario scenario.yh --view rule --format svg --output rule.svg
yuho diagram case.yh --view case --format json --output case.json
yuho diagram case.yh --view case --format xml --output case.xml
yuho diagram case.yh --view trace --format svg --output trace.svg
yuho diagram model.yh --scenario scenario.yh --view modules --format svg --output modules.svg
```

Stable node identifiers describe inputs, groups, definitions, offences, exceptions, participation, attempts, penalties, presumptions, typed finite rules, actors, allegations and shared facts. Shapes, borders and labels—not colour alone—distinguish node and trace kinds. Output contains no timestamp or absolute checkout path. Publication is atomic and an existing destination is refused.

Retained deterministic fixtures live under [`docs/artifacts/`](artifacts/). Diagram labels report technical states and always preserve the no-judicial-outcome boundary.

Current native output is `yuho.semantic-graph/v0.2`. Its optional node
`observation` contains `evaluation` (`evaluated`, `not_evaluated`, or `supplied`),
`technical_value`, `branch_reason` and `skip_reason` where reported. An absent
technical value on a skipped guard is not an evaluated `unresolved` value. Rule
values and guard occurrences come from the actual kernel report; diagram building
does not evaluate missing observations. Authored primitive classifications remain
labelled `supplied`. A guard occurrence has its own stable identity qualified by
caller, branch and exception; a shared target computation is a separate node.
Presumption routes and global direct/effective target values are also separate
from downstream guard execution.

Typed-case proposition occurrences use `case-proposition:` followed by two
length-prefixed components: `<allegation-length>:<allegation><proposition-length>:<proposition>`.
Lengths count Unicode scalar values, not UTF-8 bytes. Each component can therefore
contain colons or hyphens without merging independently scoped observations.
Nodes and their result edges share this key; labels retain the authored proposition
and the boundary retains its allegation. This corrects the ambiguous `--` pair
concatenation in the unreleased experimental v0.2 format, without a version bump.
Consumers should treat IDs as opaque and qualify observations by their actual
scope. Only typed-case proposition IDs and edges referring to them change; frozen
SDK/reference encoders and backend identities retain their existing contracts.

Scalar cards retain exact supplied values, and comparison cards retain the
operator/result, with operand links. Known integers are dimensionless unless the
source specifies an independently supported nominal scalar type; the view performs
no new arithmetic or unit inference. These remain simplified graphs, not complete
SDK projections. Complete composition projections and bindings keep their existing
formats and identities.

The native SVG uses content-sized cards, conservative UTF-8-aware wrapping without
truncation, occupied-column bounds and separate numbered routing lanes. Long labels,
citations, states and scope metadata have their own lines. Grey dashed cards state
`not_evaluated` and include available skip reasons. Routing lanes can make dense
graphs large, so use SVG zoom or inspect the canonical structured graph. SVG bytes
are deterministic and use no runtime timestamps, random layout or network fonts.
Retained v0.1 files under `docs/artifacts/` are historical examples and were not
regenerated as part of this correction.

The pre-existing library `encodeSemanticGraph`, `encodeSemanticGraphXml` and
`encodeSvg` entrypoints stay frozen at v0.1 for SDK reference-view and retained
corpus compatibility. Current native exports use `encodeNativeSemanticGraph`,
`encodeNativeSemanticGraphXml` and `encodeNativeSvg` explicitly. The historical
renderer is not the corrected trace contract; new execution explanations should
use the native v0.2 entrypoints or the complete SDK projections.
