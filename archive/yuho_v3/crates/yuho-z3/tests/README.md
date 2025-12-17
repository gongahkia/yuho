# Z3 SMT Translation Integration Tests

This directory contains integration tests for Z3 principle verification.

## Test Files

- `test_quantifier_translation.rs` - Tests SMT-LIB2 generation from Yuho quantifiers
- More tests to be added as verification functionality expands

## Running Tests

```bash
# Run all Z3 tests
cargo test --features z3

# Run specific test
cargo test --features z3 test_quantifier_translation
```

## Test Coverage

- [x] Simple forall translation
- [x] Simple exists translation
- [x] Nested forall/forall
- [x] Mixed forall/exists
- [x] Boolean operators
- [x] Arithmetic operators
- [ ] Full Z3 solver integration (coming in verification command)
- [ ] Counterexample extraction
- [ ] Model enumeration

## Example Test

```rust
#[test]
fn test_principle_verification() {
    let principle = PrincipleDefinition {
        name: "AllPositive".to_string(),
        body: Expr::Forall {
            var: "x".to_string(),
            ty: Type::Int,
            body: Box::new(Expr::Binary(
                Box::new(Expr::Identifier("x".to_string())),
                BinaryOp::Gt,
                Box::new(Expr::Literal(Literal::Int(0)))
            ))
        },
        span: Span { start: 0, end: 0 },
    };
    
    let result = verify_principle(&principle);
    assert!(result.is_ok());
}
```
