# Legal Citation Types

## Overview

Yuho supports first-class **Citation** types for representing statutory references in legal code. Citations provide a structured way to reference specific sections, subsections, and acts.

## Syntax

```yuho
Citation<section, subsection, act>
```

### Parameters

- **section**: String - The section number (e.g., "415", "12")
- **subsection**: String - The subsection number (e.g., "1", "2a")
- **act**: String - The name of the act or statute (e.g., "Penal Code", "Constitution of Singapore")

## Examples

### Basic Usage

```yuho
struct OffenseDefinition {
    Citation<"415", "1", "Penal Code"> statutory_basis,
    string description,
}
```

### Type Aliases

```yuho
type CheatingStat := Citation<"415", "1", "Penal Code">
type TheftStat := Citation<"379", "1", "Penal Code">

struct CriminalCase {
    CheatingStat primary_charge,
    TheftStat secondary_charge,
}
```

### Multiple Citations

```yuho
struct Cheating {
    Citation<"415", "1", "Penal Code"> statute,
    bool deception,
    bool dishonest_inducement,
}

struct Theft {
    Citation<"379", "1", "Penal Code"> statute,
    bool dishonest_intent,
    bool movable_property,
}
```

### Constitutional References

```yuho
struct ConstitutionalRight {
    Citation<"12", "1", "Constitution of Singapore"> article,
    string description,
}
```

## Transpilation

Citations are transpiled differently for each target:

### TypeScript

```typescript
export interface OffenseDefinition {
  statutory_basis: Citation<'415', '1', 'Penal Code'>;
  description: string;
}
```

### JSON

```json
{
  "citation": {
    "section": "415",
    "subsection": "1",
    "act": "Penal Code"
  }
}
```

### LaTeX

```latex
§415.1 of Penal Code
```

### English

```
a legal citation to section 415, subsection 1 of the Penal Code
```

### Alloy

```alloy
sig Citation_415_1_Penal_Code {}
```

### Mermaid

```
Citation‹§415.1 Penal Code›
```

## Validation

Citations are validated during semantic checking:

- ✅ Section must be non-empty
- ✅ Subsection must be non-empty
- ✅ Act must be non-empty

## Use Cases

### 1. Offense Definitions

Link criminal offenses to their statutory basis:

```yuho
struct Cheating {
    Citation<"415", "1", "Penal Code"> statute,
    bool deception,
    bool dishonest_inducement,
    bool property_delivered,
}
```

### 2. Legal Documentation

Track which statutes apply to different scenarios:

```yuho
struct LegalDocument {
    Citation<"415", "1", "Penal Code"> primary_statute,
    string title,
    date effective_date,
}
```

### 3. Cross-References

Build relationships between different legal provisions:

```yuho
struct RelatedStatutes {
    Citation<"415", "1", "Penal Code"> cheating,
    Citation<"417", "1", "Penal Code"> cheating_by_personation,
    Citation<"420", "1", "Penal Code"> cheating_and_dishonest_inducement,
}
```

## Benefits

1. **Type Safety**: Citations are strongly typed and validated at compile time
2. **Documentation**: Self-documenting code with explicit statutory references
3. **Traceability**: Easy to track which laws apply to which code sections
4. **Transpilation**: Automatic generation of hyperlinks in LaTeX/HTML outputs
5. **Consistency**: Standardized format across the entire codebase

## Future Enhancements

Planned improvements for citation types:

- Citation resolution (verify cited statute exists)
- Hyperlink generation to legal databases
- Citation index generator
- Amendment tracking for citations
- Cross-reference graph visualization

## Related Features

- [Type Aliases](TYPE_ALIASES.md) - Create semantic names for citations
- [Legal Tests](LEGAL_CONDITION_CHAINS.md) - Use citations in legal tests
- [Conflict Detection](CONFLICT_DETECTION.md) - Detect conflicts between cited statutes

## See Also

- [Examples](../examples/citations.yh) - Working examples
- [API Reference](api.md#citation) - Technical details
- [Type System](type-system.md) - General type system documentation
