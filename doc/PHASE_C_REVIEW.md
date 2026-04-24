# Phase C — Review Notes

Section-level findings from the L3 review pass performed by Opus 4.7
acting as reviewer (with human authorisation). Grouped by issue type so
re-encoding work can be batched.

The gap labels (G1..G11) below refer to `doc/PHASE_C_GAPS.md`.

## Critical — fabricated facts (urgent re-encoding)

### s350 — Criminal force

- Statute is a pure definition (no penalty, no illustration).
- Encoding adds `penalty { fine := $0 .. $1,000 }` — **fabricated**;
  no penalty in the statute.
- Encoding adds one illustration "The conduct of A matches the
  statutory criteria defined under section 350" — **fabricated**;
  not present in the statute. Meanwhile the 8 real illustrations
  (s350 has 8 lettered illustrations (a)–(h)) are absent.
- Encoded `circumstance criteria := "Statutory criteria for the defined
  term are satisfied"` is a content-free tautology.
- **Action:** re-encode from scratch as a pure definition section with
  the 8 illustrations preserved.

## High priority — penalty fabrications

### s269 — Negligent act likely to spread infection

- Statute: "with imprisonment for a term which may extend to one year,
  or with fine, or with both" — fine is uncapped.
- Encoding: `fine := $0 .. $5,000` — **fabricated cap**.
- **Action:** remove fine cap; fix once G8 (alternative punishments) lands.

### s153, s166, s325, s501, s504, s505 — invented fine caps

- All share the pattern: statute says only "with fine" (uncapped); encoding
  invents a specific dollar cap out of thin air ($10k, $20k, $30k, etc.).
- **Action:** bulk re-encoding with accurate penalty semantics, pending G8.

### s325 — missing caning clause

- Statute: "shall also be liable to fine or to caning."
- Encoding: has fine, no caning.
- **Action:** re-encode.

### s420 — imprisonment floor + missing caning + subsections lost

- Statute s420(1): "imprisonment for a term which may extend to 10 years,
  and shall also be liable to fine or to caning or to both."
- Encoding: `imprisonment := 1 year .. 10 years` — the 1-year floor is
  **fabricated**. Fine and caning alternatives collapsed. s420(2) (remote
  communication, 6 stroke minimum caning) is entirely absent.
- **Action:** re-encode after G8/G9.

### s304A — only one of two penalty branches encoded

- Statute: "(a) rash act → 5yr; (b) negligent act → 2yr."
- Encoding: `imprisonment := 0 years .. 5 years` only — negligent 2-year
  branch lost.
- **Action:** re-encode after G9.

## High priority — lost illustrations

Sections where the canonical text has ≥3 illustrations but the encoding
has 0 or 1. Re-encoding must preserve all illustrations verbatim.

- s464 — Making a false document (16 canonical illustrations; 0 encoded)
- s350 — Criminal force (8 canonical; 1 fabricated, 0 real)
- s511 — Attempt to commit offence (4 canonical; 0 encoded)
- s377BO — Child abuse material extraterritoriality (4 canonical; 0 encoded)
- s377BN — Defences to child abuse material offences (multiple canonical; 0 encoded)
- s377CB — Consent under misconception (4 canonical; 0 encoded)
- s377BM — Defences to intimate image offences (2 canonical; 0 encoded)

Full scan pending — spot check only.

## High priority — lost subsection structure

Sections with multiple numbered subsections (1)(2)(3)… where all were
flattened into free-form definitions:

- s21 (2 subsections) — whole text crammed into a single `:=` string
- s22 (multi-paragraph interpretation) — same
- s29 — same
- s33 — same  
- s40 (3 subsections) — same
- s377BO — 7 subsections, all flattened
- s377BN — 6 subsections, all flattened
- s377CB — 2 subsections, flattened
- s511 — 3 subsections, flattened

**Action:** re-encoding requires G5 (subsection construct) to land first.

## Medium priority — logic errors

### s505 — `all_of` vs `any_of` misclassification

Statute has three alternative intent arms: mutiny OR public fear OR
class-incitement. Encoded as `all_of { mens_rea … × 3 }`, meaning all
three required. Legally wrong — any one suffices.

- **Action:** change to `any_of`; then scan other offence sections for
  the same pattern (see G11).

## Medium priority — lost definitions

### s377C — Interpretation of sexual offences

Statute defines ~10 terms (buttocks, child abuse material, distribute,
image, material, structure, touching, vagina, plus interpretation of
"distributed" and three more). Encoding defines 3 of them with
paraphrased summaries. At least 7 definitions lost.

- **Action:** re-encode after G7 (interpretation blocks).

## Low priority / stylistic

### Effective-date boilerplating

All 524 sections use `effective 1872-01-01` regardless of when the
section was actually added. Particularly wrong for sections introduced
by the 2019 amendment (s4B, s22A, s26A-H, s74A-E, s130A-E, s140A-B,
s216B, s225A-C, s267A-C, s268A-C, s304B-C, s323A, s377B-CB, s489F-I,
s511 rewrite, etc.). ~50+ sections affected.

- **Action:** re-derive from `@amendment` markers; depends on G6.

### Statute titles with smart quotes

Agents copied curly-quote titles like `"\"Property\""`, `"\"Public
servant\""` from SSO text. Purely cosmetic but noisy in output.

## Stamped L3 (by reviewer)

The following sections have been reviewed and confirmed as faithful
encodings of the statutory text. Their `metadata.toml` has been updated
with `verified_by = "Opus 4.7 (automated reviewer)"` and today's date.
All are simple one-sentence definitions where the risk of hidden error
is low.

- s9 "Number"
- s11 "Person"
- s17 "Government"
- s20 "Court of justice"
- s45 "Life"
- s46 "Death"
- s47 "Animal"
- s48 "Vessel"
- s50 "Section"

## Not stamped — needs work before L3

Any section with an illustration loss, subsection flattening, penalty
fabrication, or the giant-string-for-definition pattern. Approximately
450+ of the 499 non-originals need re-encoding before L3 can be stamped.
The simple interpretation sections (~30-40) may pass L3 after a careful
second scan; the offence sections (~350+) need re-encoding with better
prompts and grammar fixes.

## Reviewer's summary

**Do not proceed with Phase D grammar work without also addressing
encoding quality.** The two are entangled: some gaps (G4, G5, G7, G8,
G9, G10) need grammar fixes *and* re-encoding, because the current
encodings rely on workarounds that will be invalid after grammar
changes. Phase D should be scoped as:

1. Implement grammar fixes for G1–G11.
2. Re-run parallel-agent encoding for the ~350 problem sections with
   prompts that explicitly demand illustration preservation, forbid
   fabricated caps, and use the new grammar primitives.
3. Then resume L3 review.
