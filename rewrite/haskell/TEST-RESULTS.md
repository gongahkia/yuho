# Haskell foundation targeted verification

**Host:** Fedora workstation, 12 September 2026; GHC 9.8.4, Cabal 3.10.3.0, Python 3.14.7 from `/usr/bin/python`. Commands below ran serially in `rewrite/haskell/` unless stated otherwise. This is a foundation check, not a new Haskell-versus-OCaml benchmark.

| Check | Result |
|---|---|
| `cabal v2-build exe:yuho-kernel --jobs=1` | Pass with `-Wall -Werror -O1`; no warning suppressions. |
| `cabal v2-test foundation-test --jobs=1 --test-show-details=direct` | Pass: 15 frozen exact-byte goldens, 20 in-process hardening cases (H12 belongs to the stream reader), definition-only unit check, seven QuickCheck properties × 100 cases. |
| `python test/protocol.py "$(cabal list-bin exe:yuho-kernel)"` | Pass: all 15 frozen responses match byte for byte; H01–H21 expected status/code/stage; one 1,048,578-byte line rejected and drained; 20 following valid requests and a repeated invalid request match their earlier bytes; stdout has one response per request and stderr is empty. H16 digest independently matches Python's canonical Unicode JSON/SHA-256. |
| Frozen result-v1 JSON Schema validation with installed `jsonschema` | Pass: 36 responses (15 frozen, 21 hardening) conform. The validator emitted only its `RefResolver` deprecation warning. |
| Clean temporary-directory `cabal v2-build exe:yuho-kernel --offline --jobs=1` | Pass using the pinned freeze file and existing user cache; no system-wide install. |
| Source scan for partial semantic operations | Pass: no `head`, `tail`, `fromJust`, `undefined`, `!!`, unchecked map lookup, semantic `error` or unsafe I/O. The bounded UTF-8 byte indexing in `Core.Source` has an explicit range guard. |
| `python scripts/verify_capability_claims.py`, active-document relative links, `git diff --check` | Pass: capability boundaries, 121 relative links in ten active documents, and whitespace. The claim checker initially matched a negated formal-assurance phrase in the ADR; wording was clarified and the rerun passed. |

The hardening manifest lists each production-only case and expected diagnostic. H01/H02/H18 check closed fields, H03–H05 branch shape, H06 real dates, H07 parser acceptance, H08/H21 both definition-state directions, H09/H10/H19 source byte/display spans, H11/H12/H20 resource limits, H13 duplicate IDs, H14 unsupported capability, H15 duplicate escaped JSON key, and H16/H17 valid/invalid Unicode surrogate handling. B01–B07, R01–R04 and P01–P04 were neither edited nor reinterpreted.

Before the single resource sample, `free -h` reported **15 GiB total, 8.3 GiB available and 4.5/8.0 GiB swap used**. The largest visible resident processes were Baloo (~675 MiB) and Helium (~611 MiB). A single serial `/usr/bin/time` launch of B06 reported **8,644 KiB peak RSS** and elapsed `0.00 s` at the tool's hundredth-second resolution. This isolated sample is not a median, latency gate or whole-toolchain forecast. The pinned dependency build was also serial; no concurrent candidate run occurred.

Only targeted checks were run. The full Python suite, full corpus exports, grammar regeneration, Lean/Lake, Docker, new parser/LSP, cross-platform packaging, proof correspondence, and the next semantic fragment were intentionally not run. Host-specific parser/LSP and packaging risk gates in the [ADR](../../docs/rewrite/ADR-0001-HASKELL.md) remain open.
