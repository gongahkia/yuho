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

## AcyclicGuardedExceptions-v1 completion

The separately [specified exception fragment](../../docs/rewrite/ACYCLIC-GUARDED-EXCEPTIONS-V1.md) was checked on the same Fedora host with the pinned GHC 9.8.4/Cabal workspace, serially and offline. It adds no direct or transitive Haskell dependency, warning suppression or compiler extension. The public release capability registry remains unchanged because this subprocess is not yet a product CLI/LSP capability; the [foundation capability table](README.md) describes its actual scope.

| Check | Result |
|---|---|
| `cabal v2-build exe:yuho-kernel --offline --jobs=1` | Pass under `-Wall -Werror -O1`. |
| `cabal v2-test foundation-test --offline --jobs=1 --test-show-details=direct` | Pass: all 15 frozen exact-byte responses, H01–H21, 39 in-process E fixtures (E35 is a stream-limit case), the existing seven properties and eleven exception properties ×100 generated cases, plus pure unresolved truth-table checks. |
| `python test/protocol.py "$(cabal list-bin exe:yuho-kernel)"` | Pass: 15 frozen goldens and 21 H hardening cases with persistent recovery. |
| `python test/exception_protocol.py "$(cabal list-bin exe:yuho-kernel)"` | Pass: 40 E fixtures, 82 persistent requests, recovery after every rejected case, all result schemas, 13 valid request schemas, canonical repeated bytes, digest, branch/dependency vectors and no stdout/stderr contamination. E32/E33/E34 exercise duplicate escaped keys and malformed/valid non-BMP Unicode; E35 exercises overlong-line draining. |
| Production union schema replay | Pass: nine accepted Boolean requests and all 36 Boolean responses validate. An initial overly broad one-off command tried to validate R03 as a valid request; R03 deliberately has an unsupported constructor. Restricting request validation to accepted inputs corrected that test assertion; all result variants were still validated. |
| Exception generator and manifest | Pass: 44 files are byte-identical after regeneration; the subprocess harness checks every SHA-256 manifest entry. E39 adds capability-class rejection of an unsupported guard that also carries extra fields; E40 checks duplicate executable-branch IDs. |
| Clean temporary-directory offline build and local copy install | Pass: serial `cabal v2-build` and `cabal v2-install` with the pinned freeze and existing user cache; launching the installed executable on E02 produced the expected defeated-branch result. No system-wide install or network fetch was used. |
| `python scripts/verify_capability_claims.py` and active rewrite relative links | Pass: the public capability/evidence boundary remains valid and 106 active relative links resolve. |

Before the clean offline replay, `free -h` reported **15 GiB total, about 6.4 GiB available and 5.0/8.0 GiB swap used**. The largest visible resident process was Baloo (~855 MiB), followed by several Helium processes (~270–467 MiB each). The build/install replay was run serially and completed; no precise latency or peak-RSS benchmark was attempted. The full Python suite, corpus exports, parser regeneration, Lean/Lake, Docker, native parser/LSP work, proof-tool selection and later semantic fragments remain intentionally unrun or unimplemented. These tests do not establish doctrine-level fidelity, formal refinement or cross-platform packaging parity.
