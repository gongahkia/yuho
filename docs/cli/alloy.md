# Alloy Command

The `yuho alloy` command generates Alloy specifications from Yuho source files for formal verification.

## Overview

The `alloy` command creates formal specifications that can be verified using the Alloy Analyzer:

- **Formal Verification** - Prove logical consistency
- **Model Checking** - Find counterexamples
- **Specification Generation** - Convert Yuho to Alloy
- **Verification Commands** - Ready-to-run Alloy code

## Basic Usage

```bash
yuho alloy <file_path> [OPTIONS]
```

### Examples

```bash
# Generate Alloy spec to stdout
yuho alloy example.yh

# Save to file
yuho alloy example.yh -o specification.als

# Generate from legal example
yuho alloy examples/cheating/cheating_illustration_A.yh -o cheating.als
```

## Command Options

### `--output`, `-o`

Specify output file path:

```bash
yuho alloy example.yh -o output.als
```

**Default**: Output to stdout

## Output Format

### Generated Alloy Specification

The command generates a complete Alloy specification including:

- **Signatures** - From Yuho struct definitions
- **Predicates** - From match-case logic
- **Facts** - From constraints and relationships
- **Run Commands** - For automated verification

### Example Output

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
  // Match expression conditions
  (deception = True and harm = True) => {
    // Consequence: guilty
  }
}

run {} for 5
```

## Working with Examples

### Basic Cheating Example

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

**Generate Alloy:**
```bash
yuho alloy cheating.yh -o cheating.als
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
  // Match expression conditions
  (deception = True and dishonest = True and harm = True) => {
    // Consequence: guilty of cheating
  }
}

run {} for 5
```

### Complex Legal Example

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

**Generate Alloy:**
```bash
yuho alloy theft.yh -o theft.als
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
  // Match expression conditions
  (dishonestIntention = True and movableProperty = True and 
   withoutConsent = True and movedProperty = True) => {
    // Consequence: guilty of theft
  }
}

run {} for 5
```

## Alloy Specification Components

### Signatures

Generated from Yuho struct definitions:

```alloy
sig Cheating {
  accused: String,
  deception: Bool,
  dishonest: Bool,
  harm: Bool
}
```

### Predicates

Generated from match-case logic:

```alloy
pred MatchCase0[x: univ] {
  // Match expression conditions
  (deception = True and dishonest = True and harm = True) => {
    // Consequence: guilty of cheating
  }
}
```

### Facts

Generated from constraints:

```alloy
fact {
  // All Cheating instances must have valid boolean values
  all c: Cheating | c.deception in Bool and c.dishonest in Bool and c.harm in Bool
}
```

### Run Commands

Generated for verification:

```alloy
// Run command to check satisfiability
run {} for 5
```

## Type Mapping

### Yuho to Alloy Types

| Yuho Type | Alloy Type |
|-----------|------------|
| `int` | `Int` |
| `float` | `Int` (Alloy has no floats) |
| `bool` | `Bool` (custom signature) |
| `string` | `String` |
| `percent` | `Int` |
| `money` | `Int` |
| `date` | `String` |
| `duration` | `String` |
| Custom struct | Custom signature |

### Example Type Mapping

**Yuho Code:**
```yh
struct Person {
    string name,
    int age,
    bool isMinor
}
```

**Generated Alloy:**
```alloy
sig Person {
  name: String,
  age: Int,
  isMinor: Bool
}
```

## Verification Workflow

### Step 1: Generate Alloy Specification

```bash
yuho alloy legal_concept.yh -o legal_concept.als
```

### Step 2: Verify with Alloy Analyzer

```bash
# Install Alloy Analyzer
# Download from https://alloytools.org/

# Run verification
java -jar alloy.jar legal_concept.als
```

### Step 3: Analyze Results

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

## Advanced Usage

### Custom Alloy Specifications

**Yuho Code:**
```yh
struct LegalConcept {
    string name,
    bool isValid,
    money penalty
}

match {
    case isValid && penalty > $1000.00 :=
        consequence "severe penalty";
    case isValid :=
        consequence "standard penalty";
    case _ :=
        consequence "no penalty";
}
```

**Generated Alloy:**
```alloy
sig LegalConcept {
  name: String,
  isValid: Bool,
  penalty: Int
}

pred MatchCase0[x: univ] {
  (isValid = True and penalty > 1000) => {
    // Consequence: severe penalty
  }
}

pred MatchCase1[x: univ] {
  (isValid = True) => {
    // Consequence: standard penalty
  }
}

pred MatchCase2[x: univ] {
  else => {
    // Consequence: no penalty
  }
}
```

### Complex Legal Relationships

**Yuho Code:**
```yh
struct LegalRelationship {
    string party1,
    string party2,
    bool isActive
}

match {
    case isActive :=
        consequence "relationship exists";
    case _ :=
        consequence "no relationship";
}
```

**Generated Alloy:**
```alloy
sig LegalRelationship {
  party1: String,
  party2: String,
  isActive: Bool
}

pred MatchCase0[x: univ] {
  (isActive = True) => {
    // Consequence: relationship exists
  }
}
```

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

## Next Steps

- [Draw Command](draw.md) - Generate visual diagrams
- [Draft Command](draft.md) - Create new Yuho files
- [REPL](repl.md) - Interactive development
- [Check Command](check.md) - Validate files before generating Alloy
