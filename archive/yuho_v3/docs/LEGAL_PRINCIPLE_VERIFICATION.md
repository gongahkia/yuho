# Legal Principle Verification in Yuho

This document explains the **Legal Principle Verification** system for formally verifying fundamental legal principles using quantifiers and SMT solving.

## Overview

Legal reasoning often involves verifying that a set of rules and cases comply with fundamental legal principles. Yuho allows you to declare principles using first-order logic quantifiers (`forall`, `exists`) and verify them against your legal code.

## Status

**Current Implementation (Commits 1-7/10)**:
- ✅ Keywords added: `principle`, `forall`, `exists`
- ✅ AST nodes: `PrincipleDefinition`, `Expr::Forall`, `Expr::Exists`
- ✅ Type checking for principles and quantified expressions
- ✅ Transpilation to all targets (Mermaid, Alloy, JSON, LaTeX, English, TypeScript, Gazette)
- ✅ Parser support for simple principles with single quantifiers
- ⏳ Parser support for complex nested quantifiers (in progress)
- ⏳ Z3 SMT translation for verification (planned)
- ⏳ Counterexample generation (planned)

## Syntax

### Basic Principle

```yuho
principle ConsiderationRequired {
    forall contract: Contract,
    exists consideration: money<SGD>,
    consideration > 0 && contract.consideration == consideration
}
```

This principle states: "For all contracts, there exists some positive consideration amount that equals the contract's consideration."

### Quantifiers

#### Universal Quantification (forall)

```yuho
forall variable: Type, expression
```

States that the expression must hold for **all** values of the given type.

Example:
```yuho
forall person: Person, person.age >= 0
```
"Every person must have a non-negative age."

#### Existential Quantification (exists)

```yuho
exists variable: Type, expression
```

States that the expression must hold for **at least one** value of the given type.

Example:
```yuho
exists witness: Person, witness.saw_defendant == true
```
"There exists at least one witness who saw the defendant."

### Simple Principles

```yuho
principle PresumptionOfInnocence {
    forall accused: Person,
    accused.presumed_status == Status::Innocent
}
```

### Principles with Conditions

```yuho
principle TimelyJustice {
    forall case: CourtCase,
    exists hearing_date: date,
    hearing_date <= case.filed_date + duration_days(180)
}
```

### Nested Quantifiers

```yuho
principle NoDoubleJeopardy {
    forall case1: CriminalCase,
    forall case2: CriminalCase,
    (case1.verdict == Verdict::Guilty 
        && case2.accused == case1.accused
        && case2.offense == case1.offense)
    => case1.case_id == case2.case_id
}
```

**Note**: Complex nested quantifiers currently require additional parser work. Simple single-quantifier principles work fully.

## Verification (Planned)

### Command

```bash
# Verify principles against a Yuho program
yuho verify principles.yh

# With timeout (milliseconds)
yuho verify --timeout 10000 principles.yh

# With Z3 trace output
yuho verify --trace principles.yh
```

### How It Works

1. **Parse**: Principles are parsed into AST nodes
2. **Type Check**: Variable types and expressions are validated
3. **Translate**: Principles are translated to Z3 SMT formulas
4. **Solve**: Z3 attempts to find counterexamples
5. **Report**: Valid principles are confirmed, violations are reported with counterexamples

## Legal Principles Library

### Criminal Law

```yuho
principle NoDoubleJeopardy {
    forall case1: CriminalCase,
    forall case2: CriminalCase,
    (case1.verdict == Verdict::Guilty && case2.accused == case1.accused)
    => case1.case_id == case2.case_id
}

principle PresumptionOfInnocence {
    forall accused: Person,
    forall trial: CriminalTrial,
    !trial.concluded => accused.presumed_status == Status::Innocent
}
```

### Contract Law

```yuho
principle ConsiderationRequired {
    forall contract: Contract,
    contract.enforceable == true =>
    exists consideration: money<SGD>,
    consideration > 0
}

principle MutualConsent {
    forall contract: Contract,
    contract.valid == true =>
    contract.offer_accepted == true && contract.parties_competent == true
}
```

### Property Law

```yuho
principle BundleOfRights {
    forall property: RealProperty,
    forall owner: Person,
    property.owner == owner =>
    (owner.has_right_to_possess && owner.has_right_to_use)
}
```

### Tort Law

```yuho
principle CausationRequired {
    forall tort: TortClaim,
    tort.liability_established == true =>
    tort.factual_causation && tort.legal_causation
}
```

### Evidence Law

```yuho
principle BeyondReasonableDoubt {
    forall case: CriminalCase,
    case.verdict == Verdict::Guilty =>
    case.evidence_strength >= 95
}

principle BalanceOfProbabilities {
    forall case: CivilCase,
    case.judgment == Judgment::Plaintiff =>
    case.evidence_strength > 50
}
```

## Transpilation

### LaTeX Output

```latex
\textbf{Principle: ConsiderationRequired}

$\forall$ \textit{contract}: Contract,
$\exists$ \textit{consideration}: money$\langle$SGD$\rangle$,
consideration $>$ 0
```

### Alloy Output

```alloy
pred ConsiderationRequired {
  all contract: Contract |
    some consideration: Money |
      gt[consideration, 0]
}
```

### English Output

```
Principle: ConsiderationRequired

For all values of contract of type Contract,
there exists a value consideration of type money<SGD> such that
consideration is greater than 0.
```

## Type Checking

The type checker validates:

1. **Variable Types**: All quantified variables have valid types
2. **Expression Types**: Body expressions are well-typed
3. **Scope**: Variables are properly scoped within quantifiers
4. **Principle Signature**: Principle names are unique

Example error:
```
Type Error: Variable 'contract' in principle body has type Contract,
but is compared with incompatible type Person
```

## Z3 Integration (Planned)

### SMT Translation

Principles will be translated to Z3 SMT-LIB format:

```smt2
(declare-fun contract () Contract)
(declare-fun consideration () Money)

(assert (forall ((c Contract))
  (exists ((m Money))
    (> m 0))))

(check-sat)
(get-model)
```

### Verification Results

```bash
✓ Principle NoDoubleJeopardy: VERIFIED
✓ Principle PresumptionOfInnocence: VERIFIED
✗ Principle InvalidPrinciple: VIOLATED

Counterexample:
  case1.accused = Person { name: "Alice", ... }
  case2.accused = Person { name: "Alice", ... }
  case1.verdict = Guilty
  case2.verdict = Guilty
  case1.offense = "Theft"
  case2.offense = "Theft"
  case1.case_id = "2023-001"
  case2.case_id = "2023-002"  <- Different IDs violate NoDoubleJeopardy
```

## Best Practices

1. **Clear Naming**: Use descriptive principle names (e.g., `NoDoubleJeopardy`, not `Principle1`)
2. **Type Safety**: Ensure quantified variables have appropriate types
3. **Simplicity**: Start with simple principles before nesting quantifiers
4. **Testing**: Verify principles against example cases
5. **Documentation**: Comment complex principles with legal reasoning

## Limitations (Current)

- Complex nested quantifiers need parser improvements
- Z3 verification not yet implemented
- Counterexample generation not yet implemented
- Performance limits on large principle sets (Z3 timeout may be needed)

## Future Enhancements

- **Temporal Principles**: Principles that change over time
- **Probabilistic Principles**: Principles with probabilistic guarantees
- **Principle Hierarchies**: Constitutional > Statutory > Regulatory principles
- **Automated Principle Discovery**: Extract principles from case law
- **Interactive Verification**: Step-through debugging for failed principles

## Related Features

- **Constraint Verification** (`yuho verify`) - Verify dependent type constraints
- **Z3 Integration** - SMT solving for constraint checking
- **Legal Tests** (`legal_test`) - Conjunctive boolean requirements
- **Conflict Detection** (`verify no_conflict`) - Multi-file consistency checking

## Examples

See:
- `examples/simple_principle.yh` - Basic single-quantifier principles (working)
- `examples/principles.yh` - Comprehensive principle library (parser work in progress)

## Implementation Status

| Component | Status | Commits |
|-----------|--------|---------|
| Keywords (principle, forall, exists) | ✅ Complete | 1 |
| AST Nodes | ✅ Complete | 2 |
| Type Checking | ✅ Complete | 3 |
| Transpilers (all 7 targets) | ✅ Complete | 4 |
| Parser (simple principles) | ✅ Complete | 5-7 |
| Parser (complex nested) | ⏳ In Progress | 7 |
| Z3 Translation | 🔮 Planned | 8 |
| Verification Engine | 🔮 Planned | 9 |
| Documentation | ✅ Complete | 10 |

**Overall: 7/10 commits complete (70%)**
