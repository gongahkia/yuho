# L3 Automated Triage Prompt

You are assisting an evidence-triage process for Singapore Penal Code 1871
section `{N}`. Compare the checked-in `.yh` source with the repository raw
snapshot. This is automated triage, not legal advice, a human review, or a
certification of fidelity.

Read the raw section, its `sub_items`, and amendments in
`library/penal_code/_raw/act.json`, plus the matching `statute.yh`. Assess:

1. section number;
2. marginal note;
3. illustration preservation;
4. explanation preservation;
5. exception preservation;
6. subsection preservation;
7. unsupported or fabricated penalty facts;
8. conjunctive/disjunctive structure;
9. effective-date evidence;
10. placeholder text; and
11. whether `yuho check` reports parsing or semantic errors.

Do not edit files, create files, run git commands, or state that any result is
human-reviewed, legally correct, or certified. A plausible match is still only
triage. When source interpretation is uncertain, choose `NEEDS_HUMAN_REVIEW`.

Return exactly one JSON object and no Markdown fences:

```json
{
  "section": "{N}",
  "decision": "TRIAGE_PASS | FLAG | NEEDS_HUMAN_REVIEW",
  "failed_items": [1, 2],
  "summary": "Short evidence-based reason."
}
```

Use `TRIAGE_PASS` only when every listed check appears to pass within the
repository snapshot. Use `FLAG` for a concrete discrepancy. Use
`NEEDS_HUMAN_REVIEW` for ambiguity, incomplete evidence, or any question that
requires legal interpretation. `failed_items` must be a unique list of
checklist numbers from 1 through 11; it may be empty only for `TRIAGE_PASS`.
