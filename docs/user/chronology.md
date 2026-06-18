# Chronology and Provenance

Yuho chronology declarations model source-backed facts, timelines,
relationships, issues, deadlines, exhibits, and alternate scenarios in
the same `.yh` file as statute logic. They are Yuho-native declarations;
Yuho does not parse `.euclid` files or run a separate Euclid runtime.

## Minimal example

```yh
source transcript: transcript {
    citation := "Lee Dep. 24:3-25:9";
}

locator lee_24 {
    source_ref := transcript;
    page := 24;
    line_start := 3;
    line_end := 9;
}

timeline record_window {
    start := 2024-01-01;
    end := 2024-03-31;
}

entity attendance_register: evidence {
    source_ref := transcript;
    locator_ref := lee_24;
    citation := "Lee Dep. 24:3-25:9";
    appears_on := record_window @ 2024-01-15..2024-02-20;
}

entity attendance_claim: claim {
    source_ref := transcript;
    citation := "Lee Dep. 24:3-25:9";
    appears_on := record_window @ 2024-02-01..2024-02-01;
}

rel attendance_register -["cites"]-> attendance_claim;
```

`yuho check FILE` runs chronology validation automatically when a module
contains chronology declarations. Use `yuho chronology check FILE` for a
chronology-focused report.

## Declarations

Supported top-level declarations:

- `source`, `source_bundle`, `locator`
- `timeline`
- `entity`, `reltype`, `rel`
- `ruleset`, `deadline_rule`
- `issue`, `issue_element`
- `scenario`, `view`, `constraint`

Chronology fields use the same `:=` field-assignment style as struct
literals. Dates and durations use Yuho literals, and timeline appearances
use `timeline_name @ start..end`.

## Validation

Chronology validation treats structural impossibility as an error and
legal-audit concerns as warnings.

Errors include missing references, impossible time bounds, malformed
deadline rules, invalid source locators, bad state/recurrence values, and
unknown statute/section/element/caselaw references.

Warnings include weak source metadata, duplicate citations, contradiction
edges, uncited claims or facts, witness records without matching
depositions, relationship cardinality concerns, and continuous-coverage
gaps.

## Custom entity schemas

Chronology entity schemas reuse Yuho `struct` definitions. Optional
fields use normal Yuho optional types.

```yh
struct LegalFact {
    string citation,
}

struct ProvenFact : LegalFact {
    source source_ref,
    string status,
}

entity filing: ProvenFact {
    citation := "Dkt. 12";
    source_ref := docket_entry;
    status := "filed";
}
```

The `struct Child : Parent` form is only schema inheritance. It does not
change normal struct literal evaluation.

## Constraints, recurrence, and state

`constraint` blocks evaluate Yuho assertions and boolean expression
statements against a chronology-aware interpreter seeded with entities,
sources, timelines, relationships, module functions, and statutes.

```yh
constraint "material claims are sourced" {
    assert has_inbound(attendance_claim, "cites"), "claim must cite evidence";
    type_of(attendance_claim) == "claim";
}
```

Available chronology predicates include `type_of`, `entities_where`,
`inbound`, `outbound`, `has_inbound`, `has_outbound`, `before`, `after`,
`overlaps`, `state_at`, and `field_at`.

Recurrence and state changes are field-based:

```yh
entity monthly_report: exhibit {
    number := "X1";
    description := "monthly reports";
    recurrence := 30 days;
    skip := [2024-02-01];
    state := [{ at := 2024-01-01, status := "draft" },
              { at := 2024-01-15, status := "served" }];
}
```

Recurrence is bounded for rendering. Deadline rules remain declarative
authority records; Yuho does not calculate docketing deadlines.

## CLI

```sh
yuho chronology check FILE
yuho chronology export FILE -t json|markdown|mermaid|svg|html -o OUT
yuho chronology diff LEFT RIGHT -t text|svg|html
yuho chronology scenario-report FILE [SCENARIO]
yuho chronology scenario-diff FILE SCENARIO -t text|svg|html -o OUT
yuho chronology sources FILE
yuho chronology deadlines FILE
yuho chronology issues FILE
yuho chronology contradictions FILE
yuho chronology exhibits FILE --format text|csv|json
yuho chronology review FILE
yuho chronology import FILE --from csv|jsonld -o OUT
```

See `examples/chronology/` for legal-provenance examples.
