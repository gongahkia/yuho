# Porting Statutes to a New Jurisdiction

This guide explains how to model statutes from jurisdictions beyond Singapore's Penal Code.

## Quick Start

1. Create a directory under `library/<jurisdiction>/<section_id>/`
2. Add `statute.yh` with doc-comment annotations
3. Add `test_statute.yh` with assertion-based tests

## Jurisdiction Annotations

Use doc-comments before the `statute` block:

```yh
/// @jurisdiction united_kingdom
/// @meta act=Theft Act 1968
/// @meta source=https://www.legislation.gov.uk/ukpga/1968/60
statute 1 "Theft" {
    ...
}
```

## Mapping Legal Concepts

| Common Law concept | Yuho element type | Notes |
|:-------------------|:-----------------|:------|
| Physical act | `actus_reus` | The prohibited conduct |
| Mental state | `mens_rea` | Required intention/knowledge |
| Surrounding facts | `circumstance` | Conditions that must exist |
| Conjunctive elements | `all_of { ... }` | ALL must be satisfied |
| Disjunctive elements | `any_of { ... }` | ANY one suffices |

For civil law jurisdictions that don't use actus reus / mens rea terminology, use `circumstance` for all elements and add a `@meta tradition=civil_law` annotation.

## Element Granularity

Follow the statute's own structure:
- If the statute lists elements disjunctively ("A or B or C"), use `any_of`
- If conjunctively ("A and B and C"), use `all_of`
- If the statute has numbered sub-sections, consider separate elements per sub-section

## Cross-Statute References

Use `referencing` to link related statutes:

```yh
referencing "uk_theft_act/s1_theft/statute"

statute 8 "Robbery" {
    ...
}
```

## Penalties

Different jurisdictions express penalties differently:

```yh
// Singapore: specific ranges
penalty {
    imprisonment := 1 year .. 7 years;
    fine := $0.00 .. $50,000.00;
}

// UK: maximum only
penalty {
    imprisonment := 0 days .. 7 years;
}

// Federal: guidelines ranges
penalty {
    imprisonment := 5 years .. 20 years;
    supplementary := "Federal Sentencing Guidelines Level 24-30";
}
```

## Exceptions and Defences

Model statutory defences as `exception` blocks with `when` guards:

```yh
exception selfDefence {
    "Reasonable force used in self-defence"
    "Complete defence - acquittal"
    when facts.defence == "selfDefence"
}
```

## Testing

Write test files that assert specific fact patterns:

```yh
referencing "my_jurisdiction/my_statute/statute"

assert is_offence("intent", TRUE) == TRUE;
assert is_offence("none", FALSE) == FALSE;
```

Run with: `yuho test test_statute.yh`

## Validation Checklist

- [ ] Statute parses without errors (`yuho check statute.yh`)
- [ ] Elements cover all constituent parts of the offence
- [ ] Penalty matches the statute's prescribed range
- [ ] At least one illustration demonstrates typical application
- [ ] Test file covers both positive and negative cases
- [ ] Jurisdiction annotation present
- [ ] Cross-references to related statutes added
