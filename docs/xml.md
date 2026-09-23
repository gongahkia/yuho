# XML output

`yuho compile` emits canonical KernelInput or case-request JSON by default. Add `--format xml` to emit the same checked, compiled technical value as deterministic XML:

```sh
yuho compile model.yh --scenario scenario.yh --format xml --output request.xml
```

The XML declaration is UTF-8. Its root is `yuho:document` in the `urn:yuho:xml:v1` namespace. JSON values are represented recursively as `yuho:null`, `yuho:boolean`, `yuho:number`, `yuho:string`, `yuho:array`, and `yuho:object`; object fields become named `yuho:member` elements and array entries retain their zero-based index. Object members are ordered by their field name, so equivalent compiled requests produce identical XML bytes.

This output is a generic technical interchange representation of Yuho's canonical compiled request. It is not Akoma Ntoso, an authoritative statute, a source-text preservation format, or a new kernel protocol. `--format json` remains the default and the kernel accepts JSON only. XML generation rejects XML 1.0 control characters rather than silently changing compiled values.

The normal `compile --output` safety rules still apply: the parent directory must exist, an existing target is refused, and successful output publication is atomic.
