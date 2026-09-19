# Deferred research and tooling

This is the current corpus gap audit for Yuho v1. The canonical inputs are the 524 rows in [`../research/singapore/SINGAPORE-CRIMINAL-LAW-COVERAGE-v0.3.json`](../research/singapore/SINGAPORE-CRIMINAL-LAW-COVERAGE-v0.3.json). Normative positions, richer candidate sanctions and explicit responsibility routes close representation gaps only where saved material supports a responsible authored model.

## Method and boundary

Exactly one primary language-gap category is assigned to each structurally saved provision that is not fully covered by an `executable_research` row or a `definition_only` row. The 438 assignments below are coarse triage based on the saved provision category and known executable limits. They do not say that a syntax extension alone would make a legally responsible model: provision-level interpretation and research remain necessary. Null gap values mean only that this audit does not identify a blocking language gap for that row.

| Primary gap | Affected provision rows |
|---|---:|
| `requires_judicial_interpretation` | 336 |
| `missing_procedural_construct` | 69 |
| `missing_participation_form` | 15 |
| `missing_penalty_form` | 10 |
| `missing_normative_or_deontic_construct` | 8 |

The closed taxonomy also reserves `missing_aggregate_or_sequence_construct`, `missing_temporal_or_transitional_construct`, `requires_evidential_assessment`, `source_unavailable_or_ambiguous` and `outside_substantive_penal_code_scope`; none is used as a primary row classification in this saved Penal Code inventory. Those concepts remain real global limitations.

## Optional future work

1. `requires_judicial_interpretation` has the largest affected set and high legal significance, but it is not chiefly a language defect. New models require external legal research and review; the language must not automate interpretation.
2. `missing_procedural_construct` affects public-justice provisions and is legally significant with high design cost. Criminal procedure and court disposition remain intentionally out of scope; no broad procedural calculus is recommended for the bounded release.
3. `missing_participation_form` is medium-sized and high significance. Existing s 107, conspiracy and s 511 slices remain usable; broader derivative and group responsibility should stay deferred unless one minimal construct resolves several reviewed provisions.
4. `missing_penalty_form` includes caning, death/life forms and predicate-offence-dependent terms. Candidate penalties are presentation-only and never sentences. A small additive term vocabulary may be considered, but sentencing logic remains out of scope.
5. `missing_normative_or_deontic_construct` affects a smaller General Part set. Core v0.3 can represent finite required, prohibited and permitted positions, but these eight rows remain unmodelled because the saved corpus does not support replacing their jurisdictional and interpretive questions with syntax alone.

## Global gaps not counted as primary rows

- Legal currency, commencement, retroactivity, savings and continuing conduct are not automatically selected.
- Narrative fact extraction, credibility, evidential sufficiency and open-textured classification remain externally supplied.
- Rule priority is explicit authored technical priority; it does not infer legal hierarchy.
- The saved structural export omits chapter-heading records and does not establish current law.
- Yuho does not produce guilt, conviction, acquittal, liability, sentence or criminal-procedure disposition.

Further judicial interpretation, procedure and sentencing extensions are optional future research rather than blockers to operating the bounded authored corpus.
