# Module Import Examples

This directory demonstrates Yuho's module import system with practical examples.

## Files

- `person.yh` - Base module defining reusable Person and Address types
- `employee.yh` - Employment contract using Person/Address from person module
- `customer.yh` - Service agreement using Person/Address from person module

## Usage

Check individual files with imports:
```bash
yuho check employee.yh
yuho check customer.yh
```

The module resolver automatically:
- Finds imported modules (searches current directory)
- Validates imported symbols exist in the module
- Detects circular import cycles
- Merges symbol tables for type checking

## Import Syntax

```yuho
referencing Person, Address from person
```

This imports `Person` and `Address` from `person.yh` (in the same directory).

## Example Output

```
╭─ Yuho Check
│  File: employee.yh
│
├─ Lexer
│  ✓ 108 tokens found
│
├─ Parser
│  ✓ 2 items parsed
│
├─ Module Resolver
│  ✓ 2 modules resolved
│
╰─ Semantic Analysis
   ✓ No errors found

   All checks passed! Your Yuho code is valid.
```
