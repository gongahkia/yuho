# Parser Improvements for Complex Nested Quantifiers

## Overview

The Yuho parser now supports arbitrarily nested quantifier expressions using `forall` and `exists` keywords. This enables the expression of complex legal principles that require multiple levels of universal and existential quantification.

## Syntax

### Simple Quantifiers

```yuho
// Universal quantification
forall variable: Type, body_expression

// Existential quantification  
exists variable: Type, body_expression
```

### Nested Quantifiers

Quantifiers can be nested to express complex logical relationships:

```yuho
// Nested forall
forall x: Type1, forall y: Type2, x.relates_to(y)

// Mixed quantifiers
forall person: Person, exists document: Document, 
    document.owner == person

// Triple nesting
forall judge: Judge, forall case: Case, exists ruling: Ruling,
    ruling.judge_id == judge.id && ruling.case_id == case.id
```

## Implementation Details

### Parser Changes

1. **Recursive Quantifier Parsing**: The `parse_quantifier_expr` method now detects nested quantifiers and recursively parses them.

2. **Depth Tracking**: Parser tracks quantifier nesting depth to prevent stack overflow (max 10 levels).

3. **Token Lookahead**: Parser checks for `forall`/`exists` tokens after the comma to determine if a nested quantifier follows.

### Type Checking

The type checker maintains a stack of quantifier variable scopes:

```rust
pub struct Checker {
    quantifier_vars: Vec<HashMap<String, Type>>,
    // ...
}
```

When entering a quantifier:
1. Push a new scope
2. Define the quantified variable in that scope
3. Type check the body expression
4. Pop the scope

This ensures that:
- Variables are only accessible within their quantifier scope
- Nested quantifiers can shadow outer variables
- Variable references are properly resolved

### AST Representation

Quantifiers are represented as recursive expressions:

```rust
pub enum Expr {
    Forall { var: String, ty: Type, body: Box<Expr> },
    Exists { var: String, ty: Type, body: Box<Expr> },
    // ...
}
```

Nested quantifiers create a tree structure:

```
Forall(x, int,
    Forall(y, int,
        Binary(x, Add, y)))
```

## Examples

### Legal Principle: All Defendants Have Rights

```yuho
principle AllDefendantsHaveAllRights {
    forall defendant: Defendant,
    forall right: ConstitutionalRight,
    defendant.rights.contains(right)
}
```

### Legal Principle: Double Jeopardy Protection

```yuho
principle NoDoubleJeopardy {
    forall person: Person,
    forall offense: Offense,
    forall case1: CriminalCase,
    case1.accused == person && case1.offense == offense && case1.final == true
    // Implies no other case with same person and offense
}
```

### Evidence Chain Requirement

```yuho
principle EvidenceChain {
    exists primaryEvidence: Evidence,
    exists corroboration: Evidence,
    primaryEvidence.verified == true &&
    corroboration.supports(primaryEvidence)
}
```

## Limitations

1. **Maximum Depth**: Quantifiers can be nested up to 10 levels deep. Deeper nesting raises a parse error.

2. **No Quantifier Alternation Restrictions**: The parser allows any combination of `forall` and `exists` quantifiers, but some combinations may not make logical sense.

3. **Runtime Evaluation**: The parser and type checker validate syntax and types, but don't evaluate the logical truth of quantified expressions. That's handled by the Z3 verification backend.

## Testing

See `crates/yuho-core/tests/test_nested_quantifiers.rs` for comprehensive test cases covering:
- Simple quantifiers
- Nested quantifiers (2-3 levels)
- Mixed quantifier types
- Depth limit enforcement
- Complex body expressions

## Future Work

- Add hints/warnings for logically equivalent but simpler formulations
- Better error messages for common quantifier mistakes
- Support for bounded quantification (e.g., `forall x in range`)
- Integration with Z3 for quantifier elimination and skolemization
