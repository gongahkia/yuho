# Citation Validation

The citation validation system ensures that legal citations in Yuho programs are properly formed and reference existing statutes.

## Features

### Section Validation
- Checks section numbers are numeric (with optional alpha suffix like "415A")
- Enforces reasonable range (1-10000)
- Rejects empty or purely alphabetic sections

### Subsection Validation
- Supports numeric: "1", "2", "3"
- Supports alphabetic: "a", "b", "c"
- Supports combined: "1a", "2b"
- Allows empty (refers to entire section)

### Cross-Reference Checking
- Tracks all defined acts/statutes in the program
- Validates citations reference existing acts
- Reports unresolved references

## Usage

Citations are automatically validated when you run `yuho check`:

```bash
yuho check your_file.yh
```

## Example

```yuho
struct PenalCodeSection {
    Citation<"415", "1", "Penal Code"> offense,
}

struct PenalCode {
    string jurisdiction,
}
```

## Error Messages

- `InvalidSection`: Section number is malformed or out of range
- `InvalidSubsection`: Subsection identifier has invalid format
- `UnresolvedReference`: Citation references non-existent act

## Implementation

See `crates/yuho-check/src/citation_validator.rs` for the full implementation.
