# XML output

`yuho diagram` emits a deterministic native semantic graph from checked Core Yuho. Add `--format xml` to emit the same graph as XML:

```sh
yuho diagram model.yh --scenario scenario.yh --view rule --format xml --output rule.xml
```

The XML declaration is UTF-8. Its root is `yuho:semantic-graph` in the `urn:yuho:semantic-graph:v0.1` namespace. The root records the graph ID, view and `yuho.semantic-graph/v0.1` format; `yuho:nodes` contains `yuho:node` elements and `yuho:edges` contains `yuho:edge` elements. Node IDs, kinds, labels, citations, statuses and module boundaries, as well as edge endpoints, kinds and labels, use the same values as the JSON semantic graph.

This output is an XML representation of Yuho's native semantic graph, not an XML encoding of KernelInput. It is not Akoma Ntoso, an authoritative statute, a source-text preservation format, or a new kernel protocol. JSON remains the canonical graph output. XML generation rejects XML 1.0 control characters rather than silently changing graph values.

The normal `diagram --output` safety rules apply: the parent directory must exist, an existing target is refused, and successful output publication is atomic.
