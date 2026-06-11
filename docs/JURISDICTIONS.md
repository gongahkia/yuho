# Jurisdiction Notes For Legal Timelines

Euclid should stay a DSL for legal timelines, not a generic rules engine. Jurisdiction support is now an auditable authority layer: timelines can carry jurisdiction metadata, rulesets define sourced procedural coverage, deadline rules describe event-triggered obligations, and concrete `deadline` entities record the actual case date selected by the author.

## Research Notes

Different civil procedure systems encode timeline duties differently:

| Jurisdiction/ruleset | Timeline implication | Official source |
| --- | --- | --- |
| U.S. federal civil procedure (`US-FRCP`) | Service and response deadlines are keyed to procedural events. FRCP Rule 6 supplies default counting mechanics; Rule 12(a)(1)(A)(i) keys the answer deadline to service of summons and complaint. | [U.S. Courts FRCP PDF](https://www.uscourts.gov/sites/default/files/2025-02/federal-rules-of-civil-procedure-dec-1-2024_0.pdf) |
| England and Wales civil procedure (`UK-CPR`) | CPR separates claim-form service, particulars of claim, acknowledgment of service, defence, and agreed extension timing. Part 10 covers acknowledgment; Part 15 covers defence timing. | [CPR Part 10](https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part10), [CPR Part 15](https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part15) |
| Singapore Rules of Court 2021 (`SG-ROC-2021`) | Originating claim timelines distinguish notice of intention to contest and defence periods, with different timing for service inside and outside Singapore. | [Singapore Judiciary response guide](https://www.judiciary.gov.sg/civil/civil-claims-%28from-1-april-2022%29/respond-to-a-civil-claim-%28from-1-april-2022%29/respond-to-a-civil-claim-made-by-an-originating-claim-%28from-1-april-2022%29/how-to-respond-to-an-originating-claim-%28from-1-april-2022%29), [Singapore Courts ROC 2021 digest](https://www.judiciary.gov.sg/civil/new-rules-of-court-2021/digest-1) |
| EU cross-border service (`EU-2020-1784`) | Service itself can have a cross-border procedural timeline; Article 12 supports an addressee language-refusal window. | [EUR-Lex Regulation (EU) 2020/1784](https://eur-lex.europa.eu/eli/reg/2020/1784/oj/eng) |
| California civil motion practice (`CA-CIVIL`) | California motion papers combine statute, statewide rules, court days, and local practice. The committed starter rule records Rule 3.1300(c)'s proof-of-service timing. | [California Rule 3.1300](https://courts.ca.gov/cms/rules/index/three/rule3_1300) |
| New York civil practice (`NY-CPLR`) | CPLR appearance and answer windows depend on service method and whether a pleading is served with the summons. Starter rules record CPLR 320(a) and 3012(a). | [N.Y. CPLR 320](https://www.nysenate.gov/legislation/laws/CVP/320), [N.Y. CPLR 3012](https://www.nysenate.gov/legislation/laws/CVP/3012) |

## Euclid Encoding

Use timeline metadata to label the procedural frame:

```euclid
timeline case_file {
    jurisdiction: "US-FRCP",
    court: "Example U.S. District Court",
    procedure: "civil-procedure",
    start: 2024-01-01,
    end: 2024-12-31,
}
```

Use `deadline` entities for auditable procedural obligations:

```euclid
entity answer_deadline : deadline {
    rule: "FRCP 12(a)(1)(A)(i)",
    jurisdiction: "US-FRCP",
    trigger: "service of summons and complaint",
    due: 2024-01-31,
    source_ref: docket_record,
    appears_on: case_file @ 2024-01-31..2024-01-31,
}
```

Use `ruleset` and `deadline_rule` for reusable authority packs:

```euclid
ruleset us_frcp {
    jurisdiction: "US-FRCP",
    court: "U.S. district courts",
    procedure: "civil-procedure",
    effective: 2024-12-01..2026-12-31,
    source_ref: frcp_2024,
}

deadline_rule us_frcp_answer_21 {
    ruleset: us_frcp,
    rule: "FRCP 12(a)(1)(A)(i)",
    trigger: "service of summons and complaint",
    actor: "defendant",
    action: "serve an answer",
    offset: days(21),
    direction: after,
    counting: calendar_days_with_last_day_rollover,
    source_ref: frcp_2024,
}
```

Use `rule_ref` on concrete deadlines when the case date is selected from a declared authority:

```euclid
entity answer_deadline : deadline {
    rule: "FRCP 12(a)(1)(A)(i)",
    jurisdiction: "US-FRCP",
    trigger: "service of summons and complaint",
    due: 2024-01-31,
    source_ref: docket_record,
    rule_ref: us_frcp_answer_21,
    appears_on: case_file @ 2024-01-31..2024-01-31,
}
```

Use `source_bundle` for packets of pleadings, authorities, docket entries, transcripts, and exhibits:

```euclid
source_bundle pleadings {
    sources: [docket_record],
    jurisdiction: "US-FRCP",
    court: "Example U.S. District Court",
}
```

The current implementation validates that:

- timelines with a jurisdiction should also name a procedure/ruleset
- rulesets must point at declared source records
- deadline rules must point at declared rulesets and source records
- deadline-rule offsets must be positive durations
- `deadline.jurisdiction` should match the appeared-on timeline jurisdiction
- `source_ref`, `locator_ref`, and `rule_ref` fields point at declared records
- source bundles only include declared source records
- duplicate citations and canonical IDs are detected after normalization

It intentionally does not calculate due dates from jurisdiction rules. The ruleset layer is declarative. Docketing-grade computation would still require versioned holiday calendars, service methods, local rules, extensions, waiver rules, court orders, emergency closures, and human review.

See [`examples/legal/jurisdiction_rulesets.euclid`](../examples/legal/jurisdiction_rulesets.euclid) for the starter jurisdiction pack.
