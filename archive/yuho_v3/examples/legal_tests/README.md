# Legal Tests Examples

This directory contains comprehensive examples demonstrating the **legal condition chains** feature (legal tests) in Yuho.

## Overview

Legal tests provide explicit syntax for defining conjunctive requirements where **ALL** conditions must be satisfied. They are essential for modeling legal rules, statutory requirements, and compliance checks.

## Examples

### 1. Criminal Law: Cheating (`cheating.yh`)

Implements Singapore Penal Code Section 415 (Cheating) using legal tests.

**Key Features:**
- Defines all four elements of cheating as conjunctive requirements
- Shows how to model case data with boolean elements
- Demonstrates verdict determination using `satisfies` pattern matching
- Includes examples of both guilty and not guilty cases

**Run:**
```bash
yuho check examples/legal_tests/cheating.yh
yuho typescript examples/legal_tests/cheating.yh
yuho explain examples/legal_tests/cheating.yh
```

### 2. Contract Law: Formation (`contracts.yh`)

Models essential elements for valid contract formation.

**Key Features:**
- Multiple legal tests (ValidContract, WrittenContract)
- Nested pattern matching for different contract types
- Examples of valid and invalid contracts
- Demonstrates both written and oral contracts

**Run:**
```bash
yuho check examples/legal_tests/contracts.yh
yuho latex examples/legal_tests/contracts.yh
yuho alloy examples/legal_tests/contracts.yh
```

### 3. Tort Law: Negligence (`torts.yh`)

Establishes elements of tortious liability for negligence.

**Key Features:**
- Four-element negligence test
- Separate professional duty test
- Multiple case scenarios (medical malpractice, car accident, no breach)
- Boolean functions for duty determination

**Run:**
```bash
yuho check examples/legal_tests/torts.yh
yuho draw examples/legal_tests/torts.yh
yuho typescript examples/legal_tests/torts.yh
```

### 4. Regulatory Compliance: Data Protection (`compliance.yh`)

Verifies compliance with data protection regulations (GDPR-style).

**Key Features:**
- Three legal tests (GDPR, SensitiveData, BreachNotification)
- Complex nested matching for different scenarios
- Integration with where clauses
- Multiple compliance statuses

**Run:**
```bash
yuho check examples/legal_tests/compliance.yh
yuho verify examples/legal_tests/compliance.yh
yuho json examples/legal_tests/compliance.yh
```

## Common Patterns

### Basic Legal Test

```yuho
legal_test TestName {
    requires element1: bool,
    requires element2: bool,
    requires element3: bool,
}
```

### Using Satisfies Pattern

```yuho
match case_data {
    case satisfies TestName := "all requirements met"
    case _ := "requirements not met"
}
```

### Multiple Legal Tests

```yuho
match data {
    case satisfies Test1 := "outcome 1"
    case satisfies Test2 := "outcome 2"
    case _ := "default outcome"
}
```

### Nested Matching

```yuho
match data {
    case satisfies OuterTest := match data {
        case satisfies InnerTest := "both satisfied"
        case _ := "only outer satisfied"
    }
    case _ := "neither satisfied"
}
```

## Testing the Examples

### Parse and Check

```bash
# Check syntax
yuho check examples/legal_tests/*.yh

# Check each file individually
yuho check examples/legal_tests/cheating.yh
yuho check examples/legal_tests/contracts.yh
yuho check examples/legal_tests/torts.yh
yuho check examples/legal_tests/compliance.yh
```

### Formal Verification

```bash
# Verify with Z3 (requires z3 feature)
yuho verify examples/legal_tests/cheating.yh
yuho verify examples/legal_tests/contracts.yh --timeout 5000
```

### Transpilation

```bash
# Generate TypeScript validators
yuho typescript examples/legal_tests/cheating.yh > cheating.ts

# Generate legal documentation
yuho latex examples/legal_tests/contracts.yh > contracts.tex
yuho explain examples/legal_tests/torts.yh > torts.txt

# Generate formal specifications
yuho alloy examples/legal_tests/compliance.yh > compliance.als

# Generate visualizations
yuho draw examples/legal_tests/cheating.yh > cheating_flow.mmd
```

## Learning Path

1. **Start with `cheating.yh`** - Simple example with clear elements
2. **Move to `contracts.yh`** - Multiple tests and nesting
3. **Study `torts.yh`** - Boolean functions and professional duties
4. **Master `compliance.yh`** - Complex scenarios and integration

## Key Concepts Demonstrated

- ✅ Conjunctive requirements (ALL must be true)
- ✅ Boolean-typed requirements
- ✅ Pattern matching with `satisfies`
- ✅ Nested legal tests
- ✅ Integration with enums and structs
- ✅ Multiple satisfies patterns in one match
- ✅ Where clauses with legal tests
- ✅ Real-world legal modeling

## Additional Resources

- [Legal Condition Chains Documentation](../../docs/LEGAL_CONDITION_CHAINS.md)
- [Pattern Matching Guide](../../docs/PATTERN_MATCHING.md)
- [Yuho Language Reference](../../docs/LANGUAGE_REFERENCE.md)

## Contributing Examples

To add new examples:
1. Create a `.yh` file in this directory
2. Include clear comments explaining the legal concept
3. Demonstrate multiple scenarios (valid/invalid cases)
4. Add appropriate test cases
5. Update this README

---

**Note**: These examples use fictional case data and simplified legal rules for demonstration purposes. Actual legal implementation requires consultation with legal professionals and jurisdiction-specific requirements.
