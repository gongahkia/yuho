# Legal Condition Chains (Legal Tests)

## Overview

Legal condition chains, implemented as **legal tests**, provide explicit syntax for defining conjunctive requirements in legal reasoning. A legal test specifies that **ALL** listed conditions must be satisfied for a particular legal outcome.

This feature addresses a core need in legal specification: clearly expressing when multiple elements must simultaneously be true.

## Syntax

### Basic Legal Test

```yuho
legal_test TestName {
    requires requirement_name: bool,
    requires another_requirement: bool,
    ...
}
```

### Key Elements

- **`legal_test`**: Keyword introducing a legal test definition
- **Test Name**: Identifier for the test (PascalCase by convention)
- **`requires`**: Keyword for each conjunctive requirement
- **Requirements**: Boolean-typed conditions that must ALL be true

### Using Legal Tests: The `satisfies` Pattern

```yuho
match case_data {
    case satisfies TestName := outcome_if_all_conditions_met
    case _ := default_outcome
}
```

The `satisfies` pattern checks if all requirements of a legal test are met.

## Examples

### Criminal Law: Cheating (Section 415 Penal Code)

```yuho
legal_test Cheating {
    requires deception: bool,
    requires dishonest_intent: bool,
    requires property_delivery: bool,
    requires victim_induced: bool,
}

struct CheatingCase {
    bool deception,
    bool dishonest_intent,
    bool property_delivery,
    bool victim_induced,
}

enum Verdict {
    Guilty,
    NotGuilty,
}

func determine_verdict(CheatingCase case) -> Verdict {
    match case {
        case satisfies Cheating := Verdict::Guilty
        case _ := Verdict::NotGuilty
    }
}
```

### Contract Law: Valid Contract Formation

```yuho
legal_test ValidContract {
    requires offer_made: bool,
    requires acceptance_given: bool,
    requires consideration_present: bool,
    requires legal_capacity: bool,
    requires lawful_purpose: bool,
}

match contract_data {
    case satisfies ValidContract := "Contract is binding"
    case _ := "Contract is not formed"
}
```

### Multiple Legal Tests

```yuho
legal_test Murder {
    requires killing: bool,
    requires malice_aforethought: bool,
}

legal_test Manslaughter {
    requires killing: bool,
    requires lack_of_malice: bool,
}

match homicide_case {
    case satisfies Murder := "Guilty of Murder"
    case satisfies Manslaughter := "Guilty of Manslaughter"
    case _ := "Not Guilty of Homicide"
}
```

## Formal Semantics

### Conjunctive Logic

A legal test defines a conjunction. For a legal test with requirements r₁, r₂, ..., rₙ:

```
satisfies(Test) ⟺ r₁ ∧ r₂ ∧ ... ∧ rₙ
```

All requirements must be true for the pattern to match.

### Z3 Verification

Legal tests are formally verified using the Z3 SMT solver:

1. **Type Checking**: All requirements must be boolean type
2. **Satisfiability**: The conjunction of requirements must be logically satisfiable
3. **Consistency**: No contradictory requirements are allowed

Example verification:

```bash
yuho verify cheating.yh
```

This checks that:
- All legal test requirements are boolean
- The conjunctive requirements are logically consistent
- References to legal tests in `satisfies` patterns are valid

## Transpilation

Legal tests transpile to different formats based on the target:

### TypeScript

```typescript
export interface CheatingTest {
  deception: boolean;
  dishonest_intent: boolean;
  property_delivery: boolean;
  victim_induced: boolean;
}

export function satisfiesCheatingTest(values: CheatingTest): boolean {
  return values.deception &&
         values.dishonest_intent &&
         values.property_delivery &&
         values.victim_induced;
}
```

### Alloy

```alloy
pred Cheating[deception: Bool, dishonest_intent: Bool,
              property_delivery: Bool, victim_induced: Bool] {
  deception and dishonest_intent and property_delivery and victim_induced
}
```

### Plain English

```
LEGAL TEST "Cheating": ALL of the following conditions must be satisfied:
  1. deception must be true or false
  2. dishonest_intent must be true or false
  3. property_delivery must be true or false
  4. victim_induced must be true or false
```

### LaTeX

```latex
\subsection*{Legal Test: Cheating}
\textbf{All} of the following requirements must be satisfied:
\begin{enumerate}
  \item \texttt{deception} must be a true/false value
  \item \texttt{dishonest_intent} must be a true/false value
  \item \texttt{property_delivery} must be a true/false value
  \item \texttt{victim_induced} must be a true/false value
\end{enumerate}
```

## Use Cases

### 1. Statutory Offense Elements

Define all elements of a statutory offense:

```yuho
legal_test Burglary {
    requires breaking: bool,
    requires entering: bool,
    requires building_or_structure: bool,
    requires intent_to_commit_crime: bool,
}
```

### 2. Contractual Requirements

Specify all necessary elements for contract validity:

```yuho
legal_test EnforceableContract {
    requires mutual_assent: bool,
    requires consideration: bool,
    requires capacity: bool,
    requires legality: bool,
    requires proper_form: bool,
}
```

### 3. Tortious Liability

Define elements of a tort:

```yuho
legal_test Negligence {
    requires duty_of_care: bool,
    requires breach_of_duty: bool,
    requires causation: bool,
    requires damages: bool,
}
```

### 4. Administrative Compliance

Specify regulatory compliance requirements:

```yuho
legal_test DataProtectionCompliance {
    requires consent_obtained: bool,
    requires data_minimization: bool,
    requires security_measures: bool,
    requires breach_notification_procedure: bool,
    requires privacy_policy_published: bool,
}
```

## Best Practices

### 1. Descriptive Names

Use clear, descriptive names for tests and requirements:

```yuho
// Good
legal_test FraudulentMisrepresentation {
    requires false_statement: bool,
    requires knowledge_of_falsity: bool,
    requires intent_to_deceive: bool,
    requires justifiable_reliance: bool,
    requires resulting_damage: bool,
}

// Less clear
legal_test Fraud {
    requires a: bool,
    requires b: bool,
    requires c: bool,
}
```

### 2. Complete Element Lists

Include ALL required elements, not just some:

```yuho
// Complete
legal_test Theft {
    requires taking: bool,
    requires property_of_another: bool,
    requires without_consent: bool,
    requires dishonest_intent: bool,
    requires permanent_deprivation: bool,
}
```

### 3. Boolean Requirements Only

Legal tests currently only support boolean requirements:

```yuho
// Supported
legal_test Valid {
    requires condition: bool,
}

// Not yet supported
legal_test Invalid {
    requires amount: int,  // Error: must be bool
}
```

For non-boolean conditions, use where clauses on struct fields instead.

### 4. Documentation

Document the legal basis for each test:

```yuho
// Singapore Penal Code Section 415: Cheating
// A person cheats when they deceive any person with dishonest intent
legal_test Cheating {
    requires deception: bool,              // Deceives any person
    requires dishonest_intent: bool,       // Dishonestly induces
    requires property_delivery: bool,      // Person delivers property
    requires victim_induced: bool,         // Person is induced to act/omit
}
```

## Limitations

### Current Limitations

1. **Boolean Types Only**: Requirements must be boolean. Complex conditions should use struct field constraints.

2. **No Disjunction**: Legal tests are conjunctive only. For "OR" logic, use multiple legal tests with separate match cases.

3. **No Nesting**: Legal tests cannot be nested or composed.

### Future Enhancements

Planned improvements include:
- Support for typed requirements beyond boolean
- Disjunctive legal tests (OR logic)
- Compositional legal tests
- Temporal requirements
- Weighted requirements (partial satisfaction)

## Related Features

- **Pattern Matching**: See [Pattern Matching Guide](./PATTERN_MATCHING.md)
- **Where Clauses**: See [Constraints Guide](./CONSTRAINTS.md)
- **Formal Verification**: See [Z3 Verification Guide](./Z3_VERIFICATION.md)
- **Semantic Analysis**: See [Type System Guide](./TYPE_SYSTEM.md)

## Command Line Usage

### Check Legal Test Syntax

```bash
yuho check legal_tests.yh
```

### Verify Legal Test Consistency

```bash
yuho verify legal_tests.yh
```

### Generate TypeScript Validators

```bash
yuho typescript legal_tests.yh > validators.ts
```

### Generate Legal Documentation

```bash
yuho latex legal_tests.yh > specification.tex
yuho explain legal_tests.yh > explanation.txt
```

## FAQ

### Q: Can I have optional requirements in a legal test?

A: No. All requirements in a legal test must be satisfied. For optional elements, create multiple legal tests or use pattern guards.

### Q: How do I express "at least N of M conditions"?

A: This is not directly supported. Use multiple legal tests or implement custom logic in match guards.

### Q: Can requirements depend on each other?

A: Requirements are independent boolean conditions. For dependencies, use where clauses on struct fields.

### Q: How does this differ from a struct?

A: Legal tests are for *testing* conditions (all must be true). Structs are for *defining* data structures. Use legal tests for legal reasoning, structs for data modeling.

### Q: Can I reuse legal tests across files?

A: Yes! Define legal tests in one file and reference them from others using the module import system:

```yuho
// criminal_law.yh
legal_test Murder { ... }

// case_analysis.yh
referencing Murder from criminal_law

match case {
    case satisfies Murder := "Guilty"
    case _ := "Not Guilty"
}
```

## Examples Directory

See `examples/legal_tests/` for complete working examples:
- `cheating.yh` - Penal Code Section 415 implementation
- `contracts.yh` - Contract formation elements
- `torts.yh` - Tortious liability tests
- `compliance.yh` - Regulatory compliance checks

---

**Version**: 1.0
**Feature**: Legal Condition Chains
**Status**: Implemented (Yuho v0.1.0)
