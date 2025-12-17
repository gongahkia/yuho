# Temporal Logic Primitives

## Overview

Yuho supports **temporal logic** for reasoning about time-dependent legal provisions. Temporal types enable tracking of effective dates, sunset dates, and validity windows for statutes and contracts.

## Syntax

```yuho
Temporal<T, valid_from="DD-MM-YYYY", valid_until="DD-MM-YYYY">
```

### Parameters

- **T**: Inner type - The type being constrained temporally
- **valid_from**: Optional - Effective date (when the value becomes valid)
- **valid_until**: Optional - Sunset date (when the value expires)

## Temporal Constraints

### Before/After/Between

Temporal constraints can be applied to date fields:

```yuho
date execution_date where execution_date >= signing_date
date effective_date where effective_date After "01-01-2020"
date contract_date where contract_date Between { start: "01-01-2020", end: "31-12-2025" }
```

### Constraint Types

- **Before(date)**: Value must be before the specified date
- **After(date)**: Value must be after the specified date
- **Between { start, end }**: Value must fall within the date range

## Examples

### Basic Temporal Value

```yuho
struct Statute {
    string title,
    Temporal<string, valid_from="01-01-2020", valid_until="31-12-2025"> content,
}
```

### Contract with Temporal Money

```yuho
struct Contract {
    string contract_id,
    date signing_date,
    Temporal<money, valid_from="01-01-2024"> value,
}
```

### Legal Provision with Effective Dates

```yuho
struct LegalProvision {
    Citation<"415", "1", "Penal Code"> statute,
    date effective_date,
    date sunset_date,
}
```

### License with Expiry

```yuho
struct License {
    string license_number,
    Temporal<bool, valid_from="01-01-2024", valid_until="31-12-2024"> is_valid,
    date issue_date,
    date expiry_date,
}
```

### Statute Version History

```yuho
struct StatuteVersion {
    Citation<"379", "1", "Penal Code"> statute,
    int version_number,
    Temporal<string, valid_from="01-01-2015", valid_until="31-12-2019"> old_text,
    Temporal<string, valid_from="01-01-2020"> current_text,
}
```

## Transpilation

Temporal types are transpiled differently for each target:

### TypeScript

```typescript
export interface Statute {
  title: string;
  content: Temporal<string, ValidFrom<'01-01-2020'>, ValidUntil<'31-12-2025'>>;
}
```

### JSON

```json
{
  "temporal": {
    "inner": "string",
    "valid_from": "01-01-2020",
    "valid_until": "31-12-2025"
  }
}
```

### LaTeX

```latex
string[temporal, from: 01-01-2020, until: 31-12-2025]
```

### English

```
a time-bound text (valid from 01-01-2020 to 31-12-2025)
```

### Alloy

```alloy
sig Temporal_String {}
// With temporal constraints in facts
```

### Mermaid

```
Temporal‹String from:01-01-2020 until:31-12-2025›
```

## Validation

Temporal types are validated during semantic checking:

- ✅ **valid_from** must be before **valid_until**
- ✅ Date formats must be valid (DD-MM-YYYY)
- ✅ Temporal constraints only apply to date types
- ✅ Date ordering is verified at compile time

## Z3 Verification

Temporal logic is verified using Z3:

```rust
verify_temporal_window(Some("01-01-2020"), Some("31-12-2025"))  // true
verify_date_in_temporal_window("15-06-2022", Some("01-01-2020"), Some("31-12-2025"))  // true
verify_date_in_temporal_window("15-06-2026"), Some("01-01-2020"), Some("31-12-2025"))  // false
```

## Use Cases

### 1. Statute Effective Dates

Track when laws come into effect and when they sunset:

```yuho
struct Amendment {
    Citation<"1", "1", "Amendment Act 2020"> citation,
    date effective_date,
    Temporal<string, valid_from="15-03-2020"> changes,
}
```

### 2. Contract Validity Periods

Ensure contracts are only valid within specific timeframes:

```yuho
struct RentalAgreement {
    Temporal<money, valid_from="01-01-2024", valid_until="31-12-2024"> monthly_rent,
    date lease_start,
    date lease_end,
}
```

### 3. License Expiration

Track time-limited licenses and permits:

```yuho
struct BusinessLicense {
    Temporal<bool, valid_from="01-01-2024", valid_until="31-12-2024"> is_active,
    date issue_date,
    date renewal_date,
}
```

### 4. Amendment Tracking

Maintain history of legal changes:

```yuho
struct StatuteHistory {
    Temporal<string, valid_from="01-01-2015", valid_until="31-12-2019"> version_1,
    Temporal<string, valid_from="01-01-2020", valid_until="31-12-2024"> version_2,
    Temporal<string, valid_from="01-01-2025"> current_version,
}
```

### 5. Retroactive Application

Model retroactive legal provisions:

```yuho
struct RetroactiveStatute {
    Citation<"100", "1", "Tax Act"> statute,
    Temporal<percent, valid_from="01-01-2020"> new_rate,
    bool retroactive_to_jan_2019,
}
```

## Benefits

1. **Legal Precision**: Model time-dependent legal provisions accurately
2. **Version Control**: Track statute amendments and changes over time
3. **Expiration Tracking**: Automatically handle sunset clauses
4. **Compile-Time Validation**: Catch temporal logic errors early
5. **Formal Verification**: Use Z3 to verify temporal constraints

## Limitations

- Dates must be in DD-MM-YYYY format
- Time-of-day is not supported (only dates)
- Timezone information is not tracked
- Relative dates (e.g., "30 days after") are not directly supported

## Future Enhancements

Planned improvements for temporal logic:

- Relative date expressions ("30 days after signing")
- Time-of-day support with timezone tracking
- Duration calculations between temporal windows
- Automatic retroactivity checking
- Temporal conflict detection between statutes
- Visualization of temporal timelines

## Related Features

- [Legal Citations](LEGAL_CITATIONS.md) - Reference statutes temporally
- [Amendment Tracking](AMENDMENT_TRACKING.md) - Track changes over time
- [Constraint System](CONSTRAINTS.md) - Date-based constraints
- [Z3 Verification](Z3_VERIFICATION.md) - Formal temporal verification

## See Also

- [Examples](../examples/temporal_logic.yh) - Working temporal examples
- [Date Constraints](../examples/date_constraints.yh) - ValidDate examples
- [API Reference](api.md#temporal) - Technical details
