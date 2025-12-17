# Verification Command Examples

## Basic Principle Verification

```bash
# Verify all principles in a file
yuho verify-principle examples/z3_principles.yh

# Show SMT-LIB2 formula
yuho verify-principle examples/z3_principles.yh --show-smt

# Show counterexamples if verification fails
yuho verify-principle examples/z3_principles.yh --show-counterexample

# Save results to file
yuho verify-principle examples/z3_principles.yh -o verification-results.txt
```

## Example Output

```
╭─ Principle Verification
│  File: examples/z3_principles.yh
│  Principles: 10
│
├─ Verifying: AllPositive
│  ✓ Valid
│
│  Explanation:
│    Principle 'AllPositive' states that:
│
│      For all x of type integer,
│        x > 0
│
├─ Verifying: EvidenceExists
│  ✓ Valid
│
│  Explanation:
│    Principle 'EvidenceExists' states that:
│
│      For all case of type CriminalCase,
│        There exists a evidence of type Evidence such that
│          evidence.case_id == case.id and evidence.admissible == true
│
╰─
```

## Verification with Counterexamples

When a principle fails verification, counterexamples show which variable assignments violate the principle:

```
╭─ Principle Verification
│  File: examples/invalid_principle.yh
│  Principles: 1
│
├─ Verifying: InvalidPrinciple
│  ✗ Invalid
│
│  Counterexample:
│    x = -5
│    y = 10
│
│  This assignment violates the principle because:
│    The constraint x > y is false when x = -5 and y = 10
│
╰─
```

## SMT-LIB2 Formula Output

With `--show-smt`, see the underlying SMT formula sent to Z3:

```
╭─ Principle Verification
│  File: examples/z3_principles.yh
│  Principles: 1
│
├─ Verifying: AllPositive
│  ✓ Valid
│
│  SMT-LIB2 Formula:
│    (forall ((x Int)) (> x 0))
│
│  Explanation:
│    Principle 'AllPositive' states that:
│
│      For all x of type integer,
│        x > 0
│
╰─
```

## Integration with CI/CD

```bash
# Verify and exit with error code if invalid
yuho verify-principle src/*.yh || exit 1

# Run verification in CI pipeline
yuho verify-principle src/**/*.yh --show-counterexample -o verification-report.txt
```

## Complex Principles

```yuho
// Double jeopardy protection
principle NoDoubleJeopardy {
    forall person: Person,
    forall offense: Offense,
    forall case1: CriminalCase,
    forall case2: CriminalCase,
    (case1.accused == person && 
     case2.accused == person &&
     case1.offense == offense && 
     case2.offense == offense &&
     case1.verdict != Verdict::Pending &&
     case1.id != case2.id) == false
}
```

Verification result:
```
├─ Verifying: NoDoubleJeopardy
│  ✓ Valid
│
│  SMT-LIB2 Formula:
│    (forall ((person Person))
│      (forall ((offense Offense))
│        (forall ((case1 CriminalCase))
│          (forall ((case2 CriminalCase))
│            (= (and
│                 (= (select case1 accused) person)
│                 (= (select case2 accused) person)
│                 (= (select case1 offense) offense)
│                 (= (select case2 offense) offense)
│                 (distinct (select case1 verdict) Pending)
│                 (distinct (select case1 id) (select case2 id)))
│               false)))))
```
