# ClosedBooleanBranches-v1 spike scorecard

**Status:** Technical spike complete; maintainer accepted [Haskell ADR-0001](../../../docs/rewrite/ADR-0001-HASKELL.md) after the [independent review](INDEPENDENT-REVIEW.md). This is a kernel comparison, not a production rewrite or whole-toolchain decision. [Raw samples](RAW-MEASUREMENTS.json), [clean build evidence](PACKAGING.json), and the [reproduction record](REPRODUCIBILITY.md) accompany this scorecard. The fixed fixture manifest is [MANIFEST.json](../fixtures/MANIFEST.json), frozen against repository HEAD `6f95b1d450b44777c5aa27b16fa61db2c525f824`.

| Gate | Haskell | OCaml | Required threshold |
|---|---:|---:|---|
| B01–B07 and R01–R04 exact schema/structural/byte parity | 11/11 pass | 11/11 pass | 11/11 |
| P01–P04 parser-diagnostic transport | 4/4 pass | 4/4 pass | 4/4 |
| Canonical bytes under shuffled input object keys | 100/100 per case, 10 fresh processes | 100/100 per case, 10 fresh processes | one byte sequence per case |
| Extra malformed JSON and invalid UTF-8 | typed KDEC001 | typed KDEC001 | no crash or stdout contamination |
| Cold-start elapsed, 30 B06 processes, median / p95 / max | 4.71 / 5.39 / 5.68 ms | 2.06 / 2.68 / 2.91 ms | ≤250 / ≤500 / ≤2,000 ms |
| Cold peak RSS, median / max | 8,130 / 8,432 KiB | 3,822 / 3,956 KiB | ≤131,072 KiB |
| 1,000-request steady run, elapsed / peak RSS | 888 ms / 9,704 KiB | 417 ms / 6,736 KiB | peak ≤131,072 KiB |
| Mean RSS growth, first to last 100 requests | 935 KiB | 689 KiB | ≤16,384 KiB |
| Clean offline build and source-free install replay B01/P02 | pass | pass | both pass |
| Lean-neutral B01–B07 proof vectors | 7/7 byte-identical exports | 7/7 byte-identical exports | 7/7, IDs/paths/edges retained |
| Independent clarity mean ≥4/5, no unexplained partial operations | **4.33/5** | **4.15/5** | separate non-implementing runtime review; both ≥4/5 |

The cold-start CPU sample from `/usr/bin/time` has 10 ms reporting resolution and reads 0 ms for these short runs. CPU time is therefore **unavailable at useful precision**; monotonic elapsed times and `/usr/bin/time` max RSS are recorded separately. Values are host-specific, one serial measurement session, not a performance guarantee. The steady elapsed figures include Python harness request/response handling and `/proc` RSS sampling; they are comparable because both candidates used the same path.

OCaml has a measured >25% advantage in cold-start median and peak RSS, plus lower steady elapsed and RSS on this host. Haskell has 512 nonblank, noncomment logical source lines versus OCaml's 780; this difference partly reflects Haskell's installed Parsec dependency versus the OCaml candidate's local JSON parser. LOC alone is not decisive under the spike rule. Both executables pass the mandatory protocol, parity, diagnostic, determinism and packaging gates. The separate review finds Haskell modestly clearer while preserving OCaml's operational advantage as a real measurement.

| Review item | Maintainer | Separate non-implementing runtime |
|---|---|---|
| Haskell clarity (0–5) and rationale | Haskell selected; no numerical code-review score asserted | 4.33/5; [review](INDEPENDENT-REVIEW.md) |
| OCaml clarity (0–5) and rationale | OCaml advantage retained as evidence | 4.15/5; [review](INDEPENDENT-REVIEW.md) |
| Proof-boundary ergonomics and assumptions | Proof tool undecided | Haskell 4.4/5, OCaml 4.3/5; neither has proof glue |
| Reproducibility/failure walkthrough | Accepted as decision evidence | Haskell source/evidence inspected; OCaml replayed 15/15; Haskell not rebuilt on reviewer host |

Final language decision: **Haskell**, accepted by the Yuho maintainer in the instruction accompanying this review. This records maintainer acceptance, not a fabricated second numerical review score. The [accepted ADR](../../../docs/rewrite/ADR-0001-HASKELL.md) records the reasons and reversal gates.

The implementing runtime's original self-assessment is in the [Haskell packet](HASKELL-REVIEW-PACKET.md) and [OCaml packet](OCAML-REVIEW-PACKET.md); it did not count as an independent score. The [toolchain risk assessment](TOOLCHAIN-RISK-ASSESSMENT.md) is non-scored. Before independent review, the implementer provisionally favoured OCaml because of measured resource use; that historical hypothesis and all raw evidence remain visible. The accepted Haskell decision weighs the completed clarity review and maintainer preference against those measurements.
