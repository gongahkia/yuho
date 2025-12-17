# Singapore Law Gazette Format in Yuho

This document explains the **Singapore Law Gazette Format** transpiler for generating official legal document formatting.

## Overview

Singapore's legal system follows specific formatting conventions for statutes published in the Law Gazette. Yuho can automatically transpile code into this official format with proper section numbering, subsections, and legal terminology.

## Usage

### Command Line

```bash
yuho gazette contract.yh
yuho gazette contract.yh -o statute.txt
```

This generates properly formatted legal text following Singapore Law Gazette conventions.

## Formatting Rules

### Section Numbering

Sections are numbered sequentially starting from 1:

```
1. CONTRACT

2. EMPLOYMENT_CONTRACT

3. CONTRACT_VALIDITY — INTERPRETATION
```

### Subsection Numbering

Subsections use parenthesized numbers:

```
(1) In this Act, "Contract", in relation to ...
(2) The following conditions apply:
```

### Lettered Clauses

Individual requirements use lowercase letters in parentheses:

```
    (a) the parties must be of type a textual description;
    (b) the consideration must be of type a textual description;
    (c) the mutual_consent must be of type a boolean value;
```

## Struct Transpilation

### Input

```yuho
struct Contract {
    string parties,
    string consideration,
    bool mutual_consent where mutual_consent == true,
}
```

### Output

```
1. CONTRACT

(1) In this Act, "Contract", in relation to means a matter that satisfies the following conditions:

    (a) the parties must be of type a textual description;
    (b) the consideration must be of type a textual description;
    (c) the mutual_consent must be of type a boolean value, and must satisfy be equal to true;
```

## Enum Transpilation

### Input

```yuho
enum ContractValidity {
    Valid,
    Voidable,
    Void,
}
```

### Output

```
2. CONTRACTVALIDITY — INTERPRETATION

(1) For the purposes of this Act, "ContractValidity" includes —

    (a) Valid;
    (b) Voidable;
    (c) Void;
```

### Mutual Exclusivity

If an enum is marked as mutually exclusive:

```yuho
enum Status {
    Active,
    Inactive,
} mutually_exclusive
```

Output includes:

```
(2) The categories in subsection (1) are mutually exclusive.
```

## Function Transpilation

### Input

```yuho
fn assess_liability(fault: FaultType, damages: bool) -> LiabilityStatus {
    // implementation
}
```

### Output

```
3. ASSESS_LIABILITY — PROCEDURE

(1) Where a matter concerning assess_liability arises —

    (a) the fault shall be of type a FaultType;
    (b) the damages shall be of type a boolean value;

(2) The result shall be of type a LiabilityStatus.
```

## Type Descriptions

Yuho types are translated to legal terminology:

| Yuho Type | Gazette Description |
|-----------|---------------------|
| `int`, `float` | "a numerical value" |
| `bool` | "a boolean value" |
| `string` | "a textual description" |
| `money<SGD>` | "a monetary sum" |
| `Date` | "a calendar date" |
| `BoundedInt<0, 100>` | "an integer between 0 and 100 (inclusive)" |
| `Citation<"415", "1", "Penal Code">` | "section 415(1) of the Penal Code" |

## Constraint Descriptions

Constraints are expressed in legal language:

| Constraint | Gazette Description |
|------------|---------------------|
| `where x > 10` | "must satisfy be greater than 10" |
| `where x >= 18` | "must satisfy be at least 18" |
| `where x < 100` | "must satisfy be less than 100" |
| `where x == value` | "must satisfy be equal to value" |

## Inheritance Formatting

Structs with inheritance include the parent reference:

```yuho
struct EmploymentContract extends Contract {
    string employer,
    string employee,
}
```

Output:

```
4. EMPLOYMENTCONTRACT

(1) In this Act, "EmploymentContract", in relation to extending Contract, means a matter that satisfies the following conditions:

    (a) the employer must be of type a textual description;
    (b) the employee must be of type a textual description;
```

## Proviso Clauses

Functions with `requires` clauses include provisos:

```yuho
fn convict(defendant: Defendant, evidence: Array<Evidence>) -> Verdict
    requires("prosecution must prove guilt beyond reasonable doubt")
{
    // implementation
}
```

Output:

```
(3) Provided that prosecution must prove guilt beyond reasonable doubt.
```

## Cross-References

Citations are automatically formatted:

```yuho
Citation<"415", "1", "Penal Code">
```

Becomes:

```
section 415(1) of the Penal Code
```

## Best Practices

1. **Clear Naming**: Use descriptive struct/enum names that translate well to legal text
2. **Explicit Constraints**: Add where clauses for all requirements
3. **Hierarchical Structure**: Use inheritance to model legal relationships
4. **Mutual Exclusivity**: Mark enums as mutually exclusive when applicable
5. **Provisos**: Use `requires` clauses for burden of proof and conditions

## Comparison with Other Formats

| Feature | Mermaid | LaTeX | Gazette |
|---------|---------|-------|---------|
| Section Numbering | ✗ | ✓ | ✓✓ |
| Legal Terminology | ✗ | ✓ | ✓✓ |
| Subsection Letters | ✗ | ✗ | ✓ |
| Proviso Formatting | ✗ | ~ | ✓ |
| Official Format | ✗ | ✗ | ✓ |

## Related Features

- **LaTeX Transpilation** - Academic legal formatting
- **English Transpilation** - Plain language explanations
- **Citation Types** - Legal citation support
- **Constraint Inheritance** - Hierarchical legal concepts

## Examples

See `examples/gazette_format.yh` for comprehensive examples:
- Contract definitions with constraints
- Enum interpretations with mutual exclusivity
- Function procedures with parameters
- Inheritance with parent references
- Citation formatting
