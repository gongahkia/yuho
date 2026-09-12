# Frozen kernel protocol v1

The scored request and result schemas are request.schema.json and result.schema.json. Every request and response is one compact, sorted-key UTF-8 JSON object followed by LF. Haskell and OCaml both decode into explicit algebraic values, validate independently and encode objects with explicit key sorting. Arrays retain source/declaration order.

The input_digest is lowercase SHA-256 of the compact canonical JSON **without LF** of the inner KernelInput fields. Evaluate uses input_schema, fragment, source, program, facts and policy. Validate uses input_schema, fragment, source, parser_result and policy. Outer protocol, operation and request_id are excluded. The original source text and its separate source.sha256 are included. This digest has no relationship to Canonical IR v1.2 hashes.

The program tree keeps ordered requirements and children. Each node has an ID, provision path and UTF-8 byte/display span. A leaf reads a Boolean fact by its ID. Group all/any evaluates every member for a complete trace, then reduces Boolean values. A branch is an executable leaf provision with inherited ancestor requirements. A provision with no executable descendant and no own/inherited requirements produces no branch; the root result is definition_only/false. If any branch is true, overall status is true.

Errors are returned as one typed diagnostic and status=rejected, with empty branches and trace. The specified rejection precedence for the frozen cases is protocol version, unsupported requirement kind, duplicate requirement ID, then missing fact. Duplicate IDs are rejected even if the facts map contains a value for the duplicated name. Parser validate requests preserve the Python adapter's diagnostic records and return true for accepted input, rejected otherwise.

The source.sha256 is SHA-256 of source.text encoded as UTF-8. Spans use half-open byte offsets and one-based displayed line/columns. Byte offsets are not Unicode codepoint indices. The frozen sources and source hashes are in fixtures/MANIFEST.json.
