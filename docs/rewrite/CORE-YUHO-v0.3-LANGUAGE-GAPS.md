# Core Yuho v0.3 corpus language-gap audit

This is a generated corpus audit, not a Core Yuho v0.3 language version. Core semantics remain v0.2. The canonical inputs are the 524 rows in [`../../research/singapore/SINGAPORE-CRIMINAL-LAW-COVERAGE-v0.3.json`](../../research/singapore/SINGAPORE-CRIMINAL-LAW-COVERAGE-v0.3.json).

## Method and boundary

Exactly one primary language-gap category is assigned to each structurally saved provision that is not fully covered by an `executable_research` row or a `definition_only` row. The 438 assignments below are coarse triage based on the saved provision category and known executable limits. They do not say that a syntax extension alone would make a legally responsible model: provision-level interpretation and research remain necessary. Null gap values mean only that this audit does not identify a blocking language gap for that row.

| Primary gap | Affected provision rows |
|---|---:|
| `requires_judicial_interpretation` | 335 |
| `missing_procedural_construct` | 69 |
| `missing_participation_form` | 15 |
| `missing_penalty_form` | 11 |
| `missing_normative_or_deontic_construct` | 8 |

The closed taxonomy also reserves `missing_aggregate_or_sequence_construct`, `missing_temporal_or_transitional_construct`, `requires_evidential_assessment`, `source_unavailable_or_ambiguous` and `outside_substantive_penal_code_scope`; none is used as a primary row classification in this saved Penal Code inventory. Those concepts remain real global limitations.

## Ranked implications for the final milestone

1. `requires_judicial_interpretation` has the largest affected set and high legal significance, but it is not chiefly a language defect. The final milestone should improve display and limitation auditing, not automate interpretation.
2. `missing_procedural_construct` affects public-justice provisions and is legally significant with high design cost. Criminal procedure and court disposition remain intentionally out of scope; no broad procedural calculus is recommended for the bounded release.
3. `missing_participation_form` is medium-sized and high significance. Existing s 107, conspiracy and s 511 slices remain usable; broader derivative and group responsibility should stay deferred unless one minimal construct resolves several reviewed provisions.
4. `missing_penalty_form` includes caning, death/life forms and predicate-offence-dependent terms. Candidate penalties are presentation-only and never sentences. A small additive term vocabulary may be considered, but sentencing logic remains out of scope.
5. `missing_normative_or_deontic_construct` affects a smaller General Part set but has high architectural cost. Permission, obligation and legal-power semantics should not be improvised during release integration.

## Global gaps not counted as primary rows

- Legal currency, commencement, retroactivity, savings and continuing conduct are not automatically selected.
- Narrative fact extraction, credibility, evidential sufficiency and open-textured classification remain externally supplied.
- Rule priority is explicit authored technical priority; it does not infer legal hierarchy.
- The saved structural export omits chapter-heading records and does not establish current law.
- Yuho does not produce guilt, conviction, acquittal, liability, sentence or criminal-procedure disposition.

The final milestone may address small correctness or usability issues. Large normative, procedural, interpretive and sentencing extensions remain optional future research rather than blockers to operating the bounded authored corpus.
