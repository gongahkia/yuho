# Presumption Tracking in Yuho

This document explains the **Presumption Tracking** system in Yuho for handling burden of proof and legal presumptions.

## Overview

Legal reasoning frequently involves presumptions that shift the burden of proof. Yuho tracks these using annotation attributes and requires clauses.

## Annotation Syntax

### `@presumed`

Marks a field or value that has a legal presumption:

```yuho
struct Defendant {
    string name,
    @presumed(innocence) Verdict status,
}
```

This indicates the defendant's status is presumed "innocence" until proven otherwise.

### Burden Clauses

Functions can specify which party bears the burden of proof:

```yuho
fn convict_defendant(defendant: Defendant, evidence: Array<Evidence>) -> Verdict
    requires("prosecution must prove guilt beyond reasonable doubt")
{
    // implementation
}
```

## Annotation Types

The `Annotation` enum supports four variants:

1. **Presumed** - Legal presumptions (e.g., innocence, capacity, legitimacy)
2. **Precedent** - Bound by case law precedent
3. **Hierarchy** - Subject to statutory hierarchies
4. **Amended** - Tracks amendments to statutes

## Semantic Interpretation

### Default Presumptions

- **Criminal Law**: Presumption of innocence (prosecution bears burden)
- **Civil Law**: Preponderance of evidence (plaintiff bears burden)
- **Family Law**: Best interests of the child (rebuttable presumptions)

### Burden Shifting

When a presumption is rebutted, the burden shifts:

```yuho
struct Property {
    string title,
    @presumed(ownership) Person owner,
}

fn challenge_ownership(property: Property, challenger: Person) -> bool
    requires("challenger must provide clear and convincing evidence")
{
    // implementation
}
```

## Transpilation

### TypeScript

```typescript
interface Defendant {
  name: string;
  /** @presumed(innocence) */
  status: Verdict;
}
```

### JSON

```json
{
  "Defendant": {
    "name": "string",
    "status": {
      "type": "Verdict",
      "presumed": "innocence"
    }
  }
}
```

### LaTeX

```latex
\\textbf{Defendant} \\{ 
  name: string, 
  status: Verdict \\textit{(presumed: innocence)} 
\\}
```

### English

```
Defendant structure with:
- name (string)
- status (Verdict, presumed innocent)
```

## Z3 Verification

The Z3 integration verifies:
- Presumptions are properly annotated
- Burden requirements are satisfied
- Proof standards are met

## Best Practices

1. **Annotate Defaults**: Mark all presumed values explicitly
2. **Document Burdens**: Use `requires` clauses for burden allocation
3. **Track Rebuttals**: Model evidence that overcomes presumptions
4. **Specify Standards**: Include proof standards (preponderance, clear and convincing, beyond reasonable doubt)

## Related Features

- **Legal Citations** (`Citation<>`) - Reference statutes establishing presumptions
- **Temporal Logic** (`Temporal<>`) - Track when presumptions apply
- **Legal Precedents** - Case law establishing rebuttable presumptions

## Examples

See `examples/presumptions.yh` for comprehensive examples of:
- Criminal law presumptions
- Civil law burden shifting
- Family law best interests
- Evidence authentication requirements
