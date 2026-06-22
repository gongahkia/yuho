# Transpile Snapshot Matrix

`tests/snapshots/transpile_matrix.json` is the regression contract for
the Singapore Penal Code transpilers.

Current verified shape:

- `statute_count`: `524`
- targets: `json`, `english`, `latex`, `mermaid`, `mindmap`, `alloy`,
  `akomantoso`, `legalruleml`
- entries: `524 x 8 = 4192`
- payload size: about 686 KiB

DOCX is a registered transpiler, but it is not part of this snapshot
test. The matrix stores deterministic text outputs only.

## Contract

The snapshot file has:

| Field | Meaning |
|---|---|
| `version` | Snapshot schema version. Currently `1`. |
| `statute_count` | Count of `library/penal_code/*/statute.yh` files. |
| `targets` | Ordered target list from `TARGETS` in `tests/test_transpile_snapshot_matrix.py`. |
| `snapshots` | Map from statute path to target fingerprints. |

Each target fingerprint stores:

- `sha256`: hash of the UTF-8 output bytes.
- `bytes`: output byte length.
- `lines`: output line count.

## Running

```bash
python3 -m pytest tests/test_transpile_snapshot_matrix.py -q
```

On failure, the test means at least one emitted output changed for at
least one Penal Code section/target pair.

## Updating

Only accept a snapshot change after reviewing the implementation diff and
confirming the changed output is intended.

```bash
YUHO_ACCEPT_SNAPSHOTS=1 python3 -m pytest tests/test_transpile_snapshot_matrix.py -q
git diff -- tests/snapshots/transpile_matrix.json
```

There is currently no pytest flag for accepting this snapshot; the test
uses only the `YUHO_ACCEPT_SNAPSHOTS=1` environment variable.

## Reading a mismatch

A hash mismatch does not say whether the new output is better. It only
says the output changed. Use the changed target and statute path to
regenerate that one output, inspect the text, then either fix the
transpiler or accept the snapshot.
