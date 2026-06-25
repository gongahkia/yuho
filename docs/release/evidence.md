# Release Evidence Ledger

This ledger maps public claims to local evidence. Treat unlisted claims as
unsupported.

| Claim | Evidence | Gate |
| --- | --- | --- |
| Yuho parses the checked-in Singapore Penal Code corpus. | `make verify-coverage` reports `524/524 sections pass yuho check`. | `make verify-core` |
| Yuho emits AKN that validates against the vendored OASIS XSD for the checked corpus. | `scripts/akn_roundtrip.py --xsd` reports `524/524 validate clean`. | `make verify-akn-xsd` |
| Runtime evaluation and Z3 agree on retained rich fixtures. | `scripts/verify_runtime_tests.py` reports `DISAGREE=0 ERR=0`. | `make verify-runtime-tests` |
| Penalty-bearing runtime verdicts match Z3 model verdicts for retained fixtures. | `scripts/verify_penalty_verdicts.py` reports `MISMATCH=0 ERR=0`. | `make verify-penalty-verdicts` |
| Legal export source maps cover element/exception nodes for retained targets. | `scripts/verify_source_maps.py` reports full coverage for JSON, AKN, LegalRuleML, and Alloy. | `make verify-source-maps` |
| Backend parity boundaries are explicit. | `tests/fixtures/backend_parity/claims.json` plus `scripts/verify_backend_parity.py`. | `make verify-backend-parity` |
| DSL v1 conformance is executable. | `tests/fixtures/conformance/dsl_spec_v1.json` plus `scripts/verify_dsl_spec.py`. | `make verify-dsl-spec` |
| Lean structural smoke fixtures match Python Z3 generator shape. | `scripts/verify_structural_diff.py --strict` reports `PASS`. | `make verify-structural-diff` |
| Lean expected verdict fixtures match Python runtime. | `scripts/verify_lean_expected_verdicts.py` reports `MISMATCH=0`. | `make verify-lean-verdicts` |
| Lean penalty footprints match Python Z3 constraints. | `scripts/verify_lean_penalty_footprints.py` reports `MISMATCH=0`. | `make verify-lean-penalty-footprints` |
| Release workflows use immutable action SHAs. | `scripts/verify_action_pins.py`. | `make verify-action-pins` |
| Corpus provenance is complete for the SG Penal Code ledger. | `scripts/verify_corpus_provenance.py`. | `make verify-corpus-provenance` |
| Python release artifacts are reproducible under fixed build inputs. | `scripts/verify_reproducible_build.py`. | `make verify-reproducible-build` |

Non-claims:

- no end-to-end legal correctness;
- no complete proof coverage for the full language;
- no Alloy parity beyond documented explicit unsupported boundaries;
- no hosted decision service implementation.
