# Comments

Comments in Yuho provide documentation and context for legal code.

## Overview

Comments in Yuho serve several purposes:

- **Legal Context** - Explain the legal source and reasoning
- **Code Documentation** - Describe what the code does
- **Clarity** - Make complex legal logic understandable
- **Maintenance** - Help future developers understand the code

## Comment Types

### Single-Line Comments

Use `//` for single-line comments:

```yh
// This is a single-line comment
string name := "John Doe";

// Section 415 - Cheating
struct Cheating {
    bool deception,
    bool dishonest,
    bool harm
}
```

### Multi-Line Comments

Use `/* */` for multi-line comments:

```yh
/*
This is a multi-line comment
that can span multiple lines
and is useful for longer explanations
*/

struct LegalConcept {
    string name,
    bool isValid
}
```

## Legal Documentation

### Legal Source Attribution

Always include the legal source:

```yh
// Section 415 - Cheating
// Whoever, by deceiving any person, fraudulently or dishonestly...
struct Cheating {
    bool deception,
    bool dishonest,
    bool harm
}
```

### Legal Context

Explain the legal reasoning:

```yh
// Cheating requires three elements:
// 1. Deception - the accused must deceive someone
// 2. Dishonesty - the accused must act dishonestly
// 3. Harm - the deception must cause harm
struct Cheating {
    bool deception,    // Element 1: Deception
    bool dishonest,    // Element 2: Dishonesty
    bool harm          // Element 3: Harm
}
```

### Legal Precedents

Reference relevant cases:

```yh
// Based on R v. Ghosh [1982] QB 1053
// Dishonesty is determined by the objective test
struct DishonestyTest {
    bool objectiveTest,  // Would reasonable person consider it dishonest?
    bool subjectiveTest  // Did accused know it was dishonest?
}
```

## Code Documentation

### Function Documentation

```yh
// Determines if a person is guilty of cheating
// Parameters:
//   - case: Cheating struct with all elements
// Returns:
//   - TRUE if all elements are present, FALSE otherwise
bool func isCheating(Cheating case) {
    match {
        case case.deception && case.dishonest && case.harm :=
            consequence TRUE;
        case _ :=
            consequence FALSE;
    }
}
```

### Struct Documentation

```yh
// Represents the elements of theft under Section 378
// All elements must be present for theft to be established
struct Theft {
    bool dishonestIntention,  // Intention to take dishonestly
    bool movableProperty,     // Property must be movable
    bool withoutConsent,      // Taken without owner's consent
    bool movedProperty        // Property must be moved
}
```

### Variable Documentation

```yh
// The maximum fine for theft offenses
money maxFine := $5000.00;

// The minimum age for adult court jurisdiction
int adultAge := 18;

// Whether the case involves a minor
bool isMinor := FALSE;
```

## Complex Logic Documentation

### Match-Case Documentation

```yh
match {
    // Cheating requires: deception + (fraudulent OR dishonest) + harm
    case deception && (fraudulent || dishonest) && harm :=
        consequence "guilty of cheating";
    
    // If any element is missing, not guilty
    case _ :=
        consequence "not guilty of cheating";
}
```

### Conditional Logic

```yh
match {
    // Juvenile cases go to juvenile court
    case age < 18 := consequence "juvenile court";
    
    // Adult cases go to adult court
    case age >= 18 := consequence "adult court";
    
    // Invalid age (should not happen)
    case _ := consequence "unknown court";
}
```

### Nested Conditions

```yh
match {
    // Severe punishment for violent offenses by repeat offenders
    case violentOffense && repeatOffender := consequence "life imprisonment";
    
    // Moderate punishment for violent offenses
    case violentOffender := consequence "10 years imprisonment";
    
    // Light punishment for property offenses
    case propertyOffense := consequence "2 years imprisonment";
    
    // Default case
    case _ := consequence "not guilty";
}
```

## Best Practices

### 1. Always Include Legal Source

```yh
// Good: Includes legal source
// Section 415 - Cheating
struct Cheating {
    bool deception,
    bool dishonest,
    bool harm
}

// Avoid: No legal context
struct Cheating {
    bool deception,
    bool dishonest,
    bool harm
}
```

### 2. Explain Complex Logic

```yh
// Good: Explains complex condition
// Cheating requires: deception + (fraudulent OR dishonest) + harm
match {
    case deception && (fraudulent || dishonest) && harm :=
        consequence "guilty of cheating";
    case _ :=
        consequence "not guilty of cheating";
}

// Avoid: No explanation
match {
    case a && (b || c) && d :=
        consequence "guilty";
    case _ :=
        consequence "not guilty";
}
```

### 3. Document Field Purposes

```yh
// Good: Explains each field
struct Theft {
    bool dishonestIntention,  // Intention to take dishonestly
    bool movableProperty,     // Property must be movable
    bool withoutConsent,      // Taken without owner's consent
    bool movedProperty        // Property must be moved
}

// Avoid: No field documentation
struct Theft {
    bool dishonestIntention,
    bool movableProperty,
    bool withoutConsent,
    bool movedProperty
}
```

### 4. Use Clear, Legal Language

```yh
// Good: Clear legal language
// The accused must have the intention to permanently deprive the owner
bool dishonestIntention := TRUE;

// Avoid: Informal language
// The guy needs to want to keep the stuff
bool dishonestIntention := TRUE;
```

## Comment Styles

### Legal Style

```yh
// Section 378 - Theft
// Whoever, intending to take dishonestly any movable property out of the possession of any person without that person's consent, moves that property in order to such taking, is said to commit theft.
struct Theft {
    bool dishonestIntention,  // Intention to take dishonestly
    bool movableProperty,      // Property must be movable
    bool withoutConsent,       // Taken without consent
    bool movedProperty         // Property must be moved
}
```

### Technical Style

```yh
// Theft offense validation
// Checks if all required elements are present
bool func isTheft(Theft case) {
    match {
        case case.dishonestIntention && case.movableProperty && 
             case.withoutConsent && case.movedProperty :=
            consequence TRUE;
        case _ :=
            consequence FALSE;
    }
}
```

### Educational Style

```yh
// This example demonstrates the elements of cheating
// Students should understand that ALL elements must be present
struct CheatingExample {
    bool deception,    // Did the accused deceive someone?
    bool dishonest,    // Did the accused act dishonestly?
    bool harm          // Did the deception cause harm?
}
```

## Common Patterns

### Pattern 1: Legal Definition

```yh
// Section 415 - Cheating
// Whoever, by deceiving any person, fraudulently or dishonestly induces the person so deceived to deliver any property to any person, or to consent that any person shall retain any property, or intentionally induces the person so deceived to do or omit to do anything which he would not do or omit if he were not so deceived, and which act or omission causes or is likely to cause damage or harm to that person in body, mind, reputation or property, is said to "cheat".
struct Cheating {
    bool deception,
    bool dishonest,
    bool harm
}
```

### Pattern 2: Case Study

```yh
// Case Study: R v. Ghosh [1982] QB 1053
// This case established the two-stage test for dishonesty:
// 1. Objective test: Would reasonable person consider it dishonest?
// 2. Subjective test: Did accused know it was dishonest?
struct DishonestyTest {
    bool objectiveTest,  // Stage 1: Objective test
    bool subjectiveTest  // Stage 2: Subjective test
}
```

### Pattern 3: Legal Reasoning

```yh
// Legal Reasoning: Cheating requires three elements
// 1. Deception - the accused must deceive someone
// 2. Dishonesty - the accused must act dishonestly  
// 3. Harm - the deception must cause harm
// All three elements must be present for cheating to be established
struct Cheating {
    bool deception,    // Element 1: Deception
    bool dishonest,    // Element 2: Dishonesty
    bool harm          // Element 3: Harm
}
```

## Documentation Standards

### File Header

```yh
/*
Yuho v3.0 - Legal Domain-Specific Language
File: cheating.yh
Purpose: Represents the offense of cheating under Section 415
Author: Legal Team
Date: 2024-01-01
Legal Source: Section 415, Penal Code of Singapore
*/
```

### Function Header

```yh
// Determines if a person is guilty of cheating
// Legal Basis: Section 415, Penal Code
// Parameters:
//   - case: Cheating struct containing all elements
// Returns:
//   - TRUE if all elements are present (guilty)
//   - FALSE if any element is missing (not guilty)
bool func isCheating(Cheating case) {
    // Implementation
}
```

### Struct Header

```yh
// Represents the elements of cheating under Section 415
// Legal Requirements: All elements must be present
// Elements:
//   - deception: The accused must deceive someone
//   - dishonest: The accused must act dishonestly
//   - harm: The deception must cause harm
struct Cheating {
    bool deception,
    bool dishonest,
    bool harm
}
```

## Troubleshooting

### Common Issues

#### Issue 1: Missing Legal Context

```yh
// Problem: No legal source
struct Cheating {
    bool deception,
    bool dishonest,
    bool harm
}
```

**Solution**: Add legal source:

```yh
// Section 415 - Cheating
struct Cheating {
    bool deception,
    bool dishonest,
    bool harm
}
```

#### Issue 2: Unclear Field Names

```yh
// Problem: Unclear field names
struct Cheating {
    bool a,
    bool b,
    bool c
}
```

**Solution**: Use descriptive names and comments:

```yh
// Section 415 - Cheating
struct Cheating {
    bool deception,    // Element 1: Deception
    bool dishonest,    // Element 2: Dishonesty
    bool harm          // Element 3: Harm
}
```

#### Issue 3: Complex Logic Without Explanation

```yh
// Problem: Complex logic without explanation
match {
    case a && (b || c) && d := consequence "guilty";
    case _ := consequence "not guilty";
}
```

**Solution**: Add explanatory comments:

```yh
// Cheating requires: deception + (fraudulent OR dishonest) + harm
match {
    case deception && (fraudulent || dishonest) && harm :=
        consequence "guilty of cheating";
    case _ :=
        consequence "not guilty of cheating";
}
```

## Next Steps

- [Syntax Reference](syntax.md) - Complete syntax guide
- [Type System](types.md) - Understanding Yuho's type system
- [Structs](structs.md) - Working with data structures
- [Match-Case](match-case.md) - Pattern matching patterns
