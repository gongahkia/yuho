# Alloy Transpiler

The Alloy transpiler converts Yuho code into formal specifications for automated verification.

## Overview

The Alloy transpiler generates:

- **Formal Specifications** - Alloy language specifications
- **Verification Commands** - Ready-to-run Alloy code
- **Type Mappings** - Convert Yuho types to Alloy types
- **Logical Verification** - Prove correctness using Alloy Analyzer

## Supported Features

### Struct to Signature Conversion

**Yuho Code:**
```yh
struct Cheating {
    string accused,
    bool deception,
    bool dishonest,
    bool harm
}
```

**Generated Alloy:**
```alloy
sig Cheating {
  accused: String,
  deception: Bool,
  dishonest: Bool,
  harm: Bool
}
```

### Match-Case to Predicate Conversion

**Yuho Code:**
```yh
match {
    case deception && dishonest && harm :=
        consequence "guilty of cheating";
    case _ :=
        consequence "not guilty of cheating";
}
```

**Generated Alloy:**
```alloy
pred MatchCase0[x: univ] {
  (deception = True and dishonest = True and harm = True) => {
    // Consequence: guilty of cheating
  }
}
```

### Complete Specification Generation

**Yuho Code:**
```yh
// Section 415 - Cheating
struct Cheating {
    string accused,
    bool deception,
    bool dishonest,
    bool harm
}

match {
    case deception && dishonest && harm :=
        consequence "guilty of cheating";
    case _ :=
        consequence "not guilty of cheating";
}
```

**Generated Alloy:**
```alloy
// Generated Alloy specification from Yuho
module YuhoGenerated

abstract sig Bool {}
one sig True, False extends Bool {}

sig Cheating {
  accused: String,
  deception: Bool,
  dishonest: Bool,
  harm: Bool
}

pred MatchCase0[x: univ] {
  (deception = True and dishonest = True and harm = True) => {
    // Consequence: guilty of cheating
  }
}

run {} for 5
```

## Usage

### Basic Usage

```bash
# Generate Alloy specification
yuho alloy example.yh -o specification.als

# Generate to stdout
yuho alloy example.yh
```

### CLI Integration

```bash
# Generate from legal example
yuho alloy examples/cheating/cheating_illustration_A.yh -o cheating.als

# Generate multiple specifications
yuho alloy examples/cheating/*.yh -o cheating_specs.als
```

## Type Mapping

### Yuho to Alloy Types

| Yuho Type | Alloy Type | Notes |
|-----------|------------|-------|
| `int` | `Int` | Integer numbers |
| `float` | `Int` | Alloy has no floats |
| `bool` | `Bool` | Custom signature |
| `string` | `String` | Text strings |
| `percent` | `Int` | Percentage values |
| `money` | `Int` | Currency amounts |
| `date` | `String` | Date strings |
| `duration` | `String` | Duration strings |
| Custom struct | Custom signature | User-defined types |

### Example Type Mappings

**Yuho Code:**
```yh
struct Person {
    string name,
    int age,
    bool isMinor,
    money salary
}
```

**Generated Alloy:**
```alloy
sig Person {
  name: String,
  age: Int,
  isMinor: Bool,
  salary: Int
}
```

## Legal Examples

### Example 1: Cheating Offense

**Yuho Code:**
```yh
// Section 415 - Cheating
struct Cheating {
    string accused,
    bool deception,
    bool dishonest,
    bool harm
}

Cheating case1 := {
    accused := "Alice",
    deception := TRUE,
    dishonest := TRUE,
    harm := TRUE
};

match {
    case case1.deception && case1.dishonest && case1.harm :=
        consequence "guilty of cheating";
    case _ :=
        consequence "not guilty of cheating";
}
```

**Generated Alloy:**
```alloy
// Generated Alloy specification from Yuho
module YuhoGenerated

abstract sig Bool {}
one sig True, False extends Bool {}

sig Cheating {
  accused: String,
  deception: Bool,
  dishonest: Bool,
  harm: Bool
}

pred MatchCase0[x: univ] {
  (deception = True and dishonest = True and harm = True) => {
    // Consequence: guilty of cheating
  }
}

run {} for 5
```

### Example 2: Theft Offense

**Yuho Code:**
```yh
// Section 378 - Theft
struct Theft {
    bool dishonestIntention,
    bool movableProperty,
    bool withoutConsent,
    bool movedProperty
}

match {
    case dishonestIntention && movableProperty && 
         withoutConsent && movedProperty :=
        consequence "guilty of theft";
    case _ :=
        consequence "not guilty of theft";
}
```

**Generated Alloy:**
```alloy
// Generated Alloy specification from Yuho
module YuhoGenerated

abstract sig Bool {}
one sig True, False extends Bool {}

sig Theft {
  dishonestIntention: Bool,
  movableProperty: Bool,
  withoutConsent: Bool,
  movedProperty: Bool
}

pred MatchCase0[x: univ] {
  (dishonestIntention = True and movableProperty = True and 
   withoutConsent = True and movedProperty = True) => {
    // Consequence: guilty of theft
  }
}

run {} for 5
```

### Example 3: Complex Legal Logic

**Yuho Code:**
```yh
struct LegalCase {
    string caseNumber,
    bool isGuilty,
    money penalty
}

match {
    case isGuilty && penalty > $1000.00 :=
        consequence "severe punishment";
    case isGuilty && penalty <= $1000.00 :=
        consequence "moderate punishment";
    case _ :=
        consequence "not guilty";
}
```

**Generated Alloy:**
```alloy
// Generated Alloy specification from Yuho
module YuhoGenerated

abstract sig Bool {}
one sig True, False extends Bool {}

sig LegalCase {
  caseNumber: String,
  isGuilty: Bool,
  penalty: Int
}

pred MatchCase0[x: univ] {
  (isGuilty = True and penalty > 1000) => {
    // Consequence: severe punishment
  }
}

pred MatchCase1[x: univ] {
  (isGuilty = True and penalty <= 1000) => {
    // Consequence: moderate punishment
  }
}

pred MatchCase2[x: univ] {
  else => {
    // Consequence: not guilty
  }
}

run {} for 5
```

## Advanced Features

### Nested Structs

**Yuho Code:**
```yh
struct Address {
    string street,
    string city,
    string postalCode
}

struct Person {
    string name,
    int age,
    Address address
}
```

**Generated Alloy:**
```alloy
sig Address {
  street: String,
  city: String,
  postalCode: String
}

sig Person {
  name: String,
  age: Int,
  address: Address
}
```

### Multiple Match-Case Statements

**Yuho Code:**
```yh
struct Offense {
    string name,
    bool isViolent,
    bool isRepeat
}

match {
    case isViolent && isRepeat :=
        consequence "life imprisonment";
    case isViolent :=
        consequence "10 years imprisonment";
    case _ :=
        consequence "2 years imprisonment";
}
```

**Generated Alloy:**
```alloy
sig Offense {
  name: String,
  isViolent: Bool,
  isRepeat: Bool
}

pred MatchCase0[x: univ] {
  (isViolent = True and isRepeat = True) => {
    // Consequence: life imprisonment
  }
}

pred MatchCase1[x: univ] {
  (isViolent = True) => {
    // Consequence: 10 years imprisonment
  }
}

pred MatchCase2[x: univ] {
  else => {
    // Consequence: 2 years imprisonment
  }
}
```

### Function Definitions

**Yuho Code:**
```yh
bool func isEligible(int age) {
    match age {
        case 18 := consequence TRUE;
        case _ := consequence FALSE;
    }
}
```

**Generated Alloy:**
```alloy
fun isEligible[age: Int]: Bool {
  // Function body would be implemented here
}
```

## Verification Workflow

### Step 1: Generate Alloy Specification

```bash
yuho alloy legal_concept.yh -o legal_concept.als
```

### Step 2: Install Alloy Analyzer

1. Download from [alloytools.org](https://alloytools.org/)
2. Install Java (required for Alloy)
3. Run Alloy Analyzer

### Step 3: Verify Specification

```bash
# Open in Alloy Analyzer
java -jar alloy.jar legal_concept.als
```

### Step 4: Analyze Results

- **Satisfiable** - Model has valid instances
- **Unsatisfiable** - Model has no valid instances
- **Counterexamples** - Invalid instances found

## Use Cases

### Use Case 1: Legal Logic Verification

**Problem**: Need to verify legal logic is consistent

**Solution**: Generate Alloy specification and verify

```bash
# Generate Alloy spec
yuho alloy statute.yh -o statute.als

# Verify with Alloy Analyzer
java -jar alloy.jar statute.als
```

**Result**: Formal verification of legal logic consistency

### Use Case 2: Legal Completeness Check

**Problem**: Need to ensure all legal cases are covered

**Solution**: Generate Alloy and check for completeness

```bash
# Generate Alloy spec
yuho alloy legal_concept.yh -o legal_concept.als

# Check completeness
java -jar alloy.jar legal_concept.als
```

**Result**: Verification that all legal cases are covered

### Use Case 3: Legal Consistency Analysis

**Problem**: Need to find contradictions in legal logic

**Solution**: Generate Alloy and analyze for contradictions

```bash
# Generate Alloy spec
yuho alloy analysis.yh -o analysis.als

# Analyze for contradictions
java -jar alloy.jar analysis.als
```

**Result**: Identification of legal logic contradictions

## Best Practices

### 1. Validate Yuho First

```bash
# Check Yuho file is valid
yuho check legal_concept.yh

# Generate Alloy only if valid
yuho alloy legal_concept.yh -o legal_concept.als
```

### 2. Use Descriptive Output Names

```bash
# Good: Descriptive names
yuho alloy cheating.yh -o cheating_verification.als
yuho alloy theft.yh -o theft_analysis.als

# Avoid: Generic names
yuho alloy example.yh -o output.als
```

### 3. Generate for Multiple Concepts

```bash
# Generate Alloy for multiple legal concepts
yuho alloy examples/cheating/cheating_illustration_A.yh -o cheating_A.als
yuho alloy examples/cheating/cheating_illustration_B.yh -o cheating_B.als
yuho alloy examples/theft/theft_definition.yh -o theft.als
```

### 4. Integrate with Verification Workflow

```bash
# Generate and verify in one workflow
yuho alloy legal_concept.yh -o legal_concept.als
java -jar alloy.jar legal_concept.als
```

## Troubleshooting

### Common Issues

#### Issue 1: Invalid Yuho File

```bash
$ yuho alloy invalid.yh
✗ Error: Invalid Yuho file
```

**Solution**: Check file with `yuho check` first:

```bash
yuho check invalid.yh
# Fix errors, then try again
yuho alloy invalid.yh
```

#### Issue 2: Empty Output

```bash
$ yuho alloy empty.yh
# No output generated
```

**Solution**: Ensure file has content:

```yh
// Add some content
struct Test {
    bool field
}

match {
    case field := consequence "result";
    case _ := consequence "default";
}
```

#### Issue 3: Permission Denied

```bash
$ yuho alloy example.yh -o protected.als
✗ Error: Permission denied: protected.als
```

**Solution**: Check file permissions:

```bash
ls -la protected.als
chmod 644 protected.als
yuho alloy example.yh -o protected.als
```

## Performance

### Generation Speed

Typical generation times:

| File Size | Statements | Time |
|-----------|------------|------|
| Small | 1-10 | <10ms |
| Medium | 11-100 | <50ms |
| Large | 101-1000 | <500ms |
| Very Large | 1000+ | <2s |

### Optimization Tips

1. **Generate to files** for repeated use
2. **Batch generate** multiple specifications
3. **Cache results** for large files
4. **Use appropriate scope** for verification

## Integration with Alloy Analyzer

### Installation

1. Download Alloy Analyzer from [alloytools.org](https://alloytools.org/)
2. Install Java (required for Alloy)
3. Run Alloy Analyzer

### Basic Verification

```bash
# Generate Alloy specification
yuho alloy legal_concept.yh -o legal_concept.als

# Open in Alloy Analyzer
java -jar alloy.jar legal_concept.als
```

### Advanced Verification

```bash
# Generate with custom scope
yuho alloy legal_concept.yh -o legal_concept.als

# Run with specific scope
java -jar alloy.jar legal_concept.als
```

## Advanced Usage

### Batch Processing

```bash
# Generate Alloy for all files
for file in examples/cheating/*.yh; do
    yuho alloy "$file" -o "${file%.yh}.als"
done
```

### Custom Output

```bash
# Generate with custom naming
yuho alloy example.yh -o "legal_concept_$(date +%Y%m%d).als"
```

### Integration with CI/CD

```bash
# Generate Alloy specs in CI pipeline
yuho alloy examples/cheating/cheating_illustration_A.yh -o docs/cheating.als
yuho alloy examples/theft/theft_definition.yh -o docs/theft.als
```

## Next Steps

- [Mermaid Transpiler](mermaid.md) - Generate visual diagrams
- [CLI Commands](../cli/commands.md) - Command-line interface
- [Examples](../examples/criminal-law.md) - Legal examples
- [Language Guide](../language/overview.md) - Yuho language reference
