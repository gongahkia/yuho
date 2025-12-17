# Z3 SMT Translation for Principle Verification

## Overview

This module provides translation from Yuho legal principles (with quantifiers) to Z3 SMT-LIB2 format for automated theorem proving and verification.

## Architecture

### Translation Pipeline

```
Yuho Principle (AST)
        ↓
  Quantifier Translator
        ↓
   SMT-LIB2 Formula
        ↓
    Z3 Solver
        ↓
  Verification Result
```

### Key Components

1. **`quantifier.rs`**: Core translation logic
   - Converts `forall`/`exists` expressions to SMT quantifiers
   - Handles nested quantifiers with proper variable scoping
   - Translates binary/unary operations to SMT operators

2. **`lib.rs`**: Public API
   - `verify_principle()`: Main entry point for verification
   - `PrincipleVerificationResult`: Structured results with counterexamples

3. **SMT-LIB2 Output**: Standard Z3 format
   ```smt2
   (forall ((x Int)) (> x 0))
   (exists ((y Bool)) (and y true))
   ```

## Translation Rules

### Quantifiers

| Yuho | SMT-LIB2 |
|------|----------|
| `forall x: int, P(x)` | `(forall ((x Int)) P(x))` |
| `exists x: bool, P(x)` | `(exists ((x Bool)) P(x))` |

### Types

| Yuho Type | Z3 Sort |
|-----------|---------|
| `int` | `Int` |
| `bool` | `Bool` |
| `float` | `Real` |
| `string` | `String` |
| `BoundedInt<a,b>` | `Int` (with constraints) |

### Operators

| Yuho | SMT-LIB2 |
|------|----------|
| `+`, `-`, `*` | `+`, `-`, `*` |
| `/` | `div` |
| `%` | `mod` |
| `==` | `=` |
| `!=` | `distinct` |
| `<`, `>`, `<=`, `>=` | `<`, `>`, `<=`, `>=` |
| `&&`, `||`, `!` | `and`, `or`, `not` |

## Example Translations

### Simple Principle

**Yuho:**
```yuho
principle Positive {
    forall x: int, x > 0
}
```

**SMT-LIB2:**
```smt2
(forall ((x Int)) (> x 0))
```

### Nested Quantifiers

**Yuho:**
```yuho
principle DoubleJeopardy {
    forall person: Person,
    forall case: Case,
    case.accused == person
}
```

**SMT-LIB2:**
```smt2
(forall ((person Person))
  (forall ((case Case))
    (= (select case accused) person)))
```

### Mixed Quantifiers

**Yuho:**
```yuho
principle Evidence {
    forall case: CriminalCase,
    exists evidence: Evidence,
    evidence.case_id == case.id
}
```

**SMT-LIB2:**
```smt2
(forall ((case CriminalCase))
  (exists ((evidence Evidence))
    (= (select evidence case_id) (select case id))))
```

## Usage

```rust
use yuho_z3::verify_principle;
use yuho_core::ast::PrincipleDefinition;

// Parse a Yuho principle
let principle: PrincipleDefinition = /* ... */;

// Verify using Z3
let result = verify_principle(&principle)?;

if result.is_valid {
    println!("Principle verified: {}", principle.name);
    println!("SMT formula: {}", result.smt_formula);
} else {
    println!("Principle invalid!");
    if let Some(counterexample) = result.counterexample {
        println!("Counterexample: {}", counterexample);
    }
}
```

## Limitations

1. **Custom Types**: User-defined structs are translated as uninterpreted sorts. Z3 treats them symbolically.

2. **Function Symbols**: Custom functions in principles are translated as uninterpreted functions.

3. **Recursive Definitions**: Not supported in current version.

4. **Quantifier Alternation**: No automatic simplification of quantifier alternations.

## Future Enhancements

- [ ] Quantifier elimination for decidable fragments
- [ ] Skolemization for efficient proofs
- [ ] Counter example generation with concrete values
- [ ] Support for arrays and records
- [ ] Bit-vector support for bounded arithmetic
- [ ] Timeout and resource limits
- [ ] Incremental verification
- [ ] Theory combination (e.g., arrays + arithmetic)

## References

- [Z3 Guide](https://microsoft.github.io/z3guide/)
- [SMT-LIB2 Standard](https://smtlib.cs.uiowa.edu/)
- [z3.rs Documentation](https://github.com/prove-rs/z3.rs)
