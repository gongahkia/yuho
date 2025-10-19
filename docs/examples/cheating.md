# Cheating Offenses

Real-world examples of representing cheating offenses in Yuho, based on Section 415 of the Singapore Penal Code.

## Overview

This page demonstrates how Yuho represents the offense of cheating under Section 415 of the Penal Code. Each example shows the progression from legal text to Yuho code to visual diagrams.

## Legal Source

**Section 415 of the Penal Code**:

> Whoever, by deceiving any person, fraudulently or dishonestly induces the person so deceived to deliver any property to any person, or to consent that any person shall retain any property, or intentionally induces the person so deceived to do or omit to do anything which he would not do or omit if he were not so deceived, and which act or omission causes or is likely to cause damage or harm to that person in body, mind, reputation or property, is said to "cheat".

## Basic Cheating Definition

### Yuho Representation

```yh
// Section 415 - Cheating
struct Cheating {
    string accused,
    string victim,
    bool deception,
    bool fraudulent,
    bool dishonest,
    bool inducedDeliveryOfProperty,
    bool inducedConsentToRetain,
    bool inducedActionOrOmission,
    bool causesDamageOrHarm,
    string damageType  // body, mind, reputation, or property
}

match {
    case deception && (fraudulent || dishonest) && 
         (inducedDeliveryOfProperty || inducedConsentToRetain || inducedActionOrOmission) &&
         causesDamageOrHarm := 
        consequence "guilty of cheating under Section 415";
    
    case _ := 
        consequence "not guilty of cheating";
}
```

### Breaking Down the Elements

The offense of cheating requires:

1. **Deception**: The accused must deceive someone
2. **Mental Element**: Either fraudulent OR dishonest
3. **Inducement** (any one of):
   - Deliver property
   - Consent to retain property
   - Do or omit to do something
4. **Harm**: Causes or likely to cause damage/harm

## Illustration A: False Government Service

### Legal Text

> "A, by falsely pretending to be in the Government service, intentionally deceives Z, and thus dishonestly induces Z to let him have on credit goods for which he does not mean to pay. A cheats."

### Yuho Code

```yh
/*
Illustration A - Cheating by false pretense
A falsely claims to be in government service to get goods on credit
*/

struct CheatingIllustrationA {
    string accused := "A",
    string victim := "Z",
    string action := "falsely pretending to be in Government service",
    bool deception := TRUE,
    bool dishonest := TRUE,
    bool inducedConsentToRetain := TRUE,
    bool causesDamageOrHarm := TRUE,
    string damageType := "property"
}

match {
    case deception && dishonest && inducedConsentToRetain && causesDamageOrHarm :=
        consequence "A cheats";
    case _ :=
        consequence "not cheating";
}
```

### Key Points

- A deceived Z by false pretense
- A acted dishonestly (no intention to pay)
- Z was induced to give goods on credit
- Z suffered property damage (goods without payment)

## Illustration B: False Promise

### Legal Text

> "A, by putting a counterfeit mark on an article, intentionally deceives Z into a belief that this article was made by a certain celebrated manufacturer, and thus dishonestly induces Z to buy and pay for the article. A cheats."

### Yuho Code

```yh
/*
Illustration B - Cheating by false promise
A uses counterfeit mark to deceive Z into buying article
*/

struct CheatingIllustrationB {
    string accused := "A",
    string victim := "Z",
    string action := "putting counterfeit mark on article",
    bool deception := TRUE,
    bool dishonest := TRUE,
    bool inducedDeliveryOfProperty := TRUE,
    bool causesDamageOrHarm := TRUE,
    string damageType := "property"
}

match {
    case deception && dishonest && inducedDeliveryOfProperty && causesDamageOrHarm :=
        consequence "A cheats";
    case _ :=
        consequence "not cheating";
}
```

### Key Points

- A deceived Z by counterfeit mark
- A acted dishonestly (intentional deception)
- Z was induced to buy and pay for article
- Z suffered property damage (paid for counterfeit goods)

## Illustration C: False Representation

### Legal Text

> "A, by exhibiting to Z a false sample of an article, intentionally deceives Z into believing that the article which A offers to sell to Z corresponds to the sample, and thus dishonestly induces Z to buy and pay for the article. A cheats."

### Yuho Code

```yh
/*
Illustration C - Cheating by false representation
A shows false sample to deceive Z into buying article
*/

struct CheatingIllustrationC {
    string accused := "A",
    string victim := "Z",
    string action := "exhibiting false sample of article",
    bool deception := TRUE,
    bool dishonest := TRUE,
    bool inducedDeliveryOfProperty := TRUE,
    bool causesDamageOrHarm := TRUE,
    string damageType := "property"
}

match {
    case deception && dishonest && inducedDeliveryOfProperty && causesDamageOrHarm :=
        consequence "A cheats";
    case _ :=
        consequence "not cheating";
}
```

### Key Points

- A deceived Z by false sample
- A acted dishonestly (intentional deception)
- Z was induced to buy and pay for article
- Z suffered property damage (paid for misrepresented goods)

## Working with Examples

### Check an Example

```bash
# Validate the cheating example
yuho check examples/cheating/cheating_illustration_A.yh
```

### Visualize an Example

```bash
# Generate flowchart
yuho draw examples/cheating/cheating_illustration_A.yh -f flowchart -o cheating_flow.mmd

# Generate mindmap
yuho draw examples/cheating/cheating_illustration_A.yh -f mindmap -o cheating_mind.mmd
```

### Verify an Example

```bash
# Generate Alloy specification
yuho alloy examples/cheating/cheating_illustration_A.yh -o cheating.als

# Verify with Alloy Analyzer (if installed)
java -jar alloy.jar cheating.als
```

## Legal Reasoning Patterns

### Pattern 1: Conjunctive Requirements

When ALL elements must be present:

```yh
match {
    case element1 && element2 && element3 := consequence "guilty";
    case _ := consequence "not guilty";
}
```

**Example**: Cheating requires ALL of: deception, dishonesty, inducement, harm.

### Pattern 2: Disjunctive Requirements

When ANY element is sufficient:

```yh
match {
    case element1 || element2 || element3 := consequence "guilty";
    case _ := consequence "not guilty";
}
```

**Example**: Cheating can involve delivery of property OR consent to retain OR induced action/omission.

### Pattern 3: Nested Conditions

Complex combinations:

```yh
match {
    case baseElement && (option1 || option2 || option3) && finalElement :=
        consequence "guilty";
    case _ :=
        consequence "not guilty";
}
```

**Example**: Cheating = deception + (fraudulent OR dishonest) + (one of three inducement types) + harm.

### Pattern 4: Multiple Consequences

Different outcomes based on conditions:

```yh
match {
    case severeCondition := consequence "severe punishment";
    case moderateCondition := consequence "moderate punishment";
    case minorCondition := consequence "minor punishment";
    case _ := consequence "not guilty";
}
```

## Best Practices

### 1. Clear Naming

```yh
// Good: Descriptive names
struct Cheating {
    string accused,
    bool deception,
    bool harm
}

// Avoid: Unclear abbreviations
struct C {
    string a,
    bool d,
    bool h
}
```

### 2. Comments for Context

```yh
// Always include the legal source
// Section 415 - Cheating

// Explain complex conditions
case deception && dishonest :=
    // Both deception and dishonesty are required
    consequence "guilty";
```

### 3. Complete Case Coverage

```yh
match {
    case condition1 := consequence "result1";
    case condition2 := consequence "result2";
    // Always include default case
    case _ := consequence "default";
}
```

### 4. Type Safety

```yh
// Use appropriate types
struct Offense {
    string accused,        // Names are strings
    int age,              // Age is integer
    bool guilty,          // Guilt is boolean
    money fine := $500.00 // Fines are money type
}
```

## Advanced Examples

### Complex Cheating Scenario

```yh
// Complex cheating with multiple elements
struct ComplexCheating {
    string accused,
    string victim,
    bool deception,
    bool fraudulent,
    bool dishonest,
    bool inducedDeliveryOfProperty,
    bool inducedConsentToRetain,
    bool inducedActionOrOmission,
    bool causesDamageOrHarm,
    string damageType,
    money amount
}

match {
    case deception && (fraudulent || dishonest) && 
         (inducedDeliveryOfProperty || inducedConsentToRetain || inducedActionOrOmission) &&
         causesDamageOrHarm && amount > $1000.00 :=
        consequence "guilty of aggravated cheating";
    
    case deception && (fraudulent || dishonest) && 
         (inducedDeliveryOfProperty || inducedConsentToRetain || inducedActionOrOmission) &&
         causesDamageOrHarm :=
        consequence "guilty of cheating";
    
    case _ :=
        consequence "not guilty of cheating";
}
```

### Cheating with Defenses

```yh
// Cheating with possible defenses
struct CheatingWithDefenses {
    string accused,
    string victim,
    bool deception,
    bool dishonest,
    bool harm,
    bool consent,
    bool mistake,
    bool duress
}

match {
    case deception && dishonest && harm && not consent && not mistake && not duress :=
        consequence "guilty of cheating";
    
    case consent :=
        consequence "not guilty - victim consented";
    
    case mistake :=
        consequence "not guilty - honest mistake";
    
    case duress :=
        consequence "not guilty - under duress";
    
    case _ :=
        consequence "not guilty of cheating";
}
```

## Common Mistakes

### Mistake 1: Missing Elements

```yh
// Wrong: Missing required elements
match {
    case deception := consequence "guilty";
    case _ := consequence "not guilty";
}
```

**Fix**: Include all required elements:

```yh
match {
    case deception && dishonest && harm := consequence "guilty";
    case _ := consequence "not guilty";
}
```

### Mistake 2: Incorrect Logic

```yh
// Wrong: Using OR instead of AND
match {
    case deception || dishonest || harm := consequence "guilty";
    case _ := consequence "not guilty";
}
```

**Fix**: Use correct logic:

```yh
match {
    case deception && dishonest && harm := consequence "guilty";
    case _ := consequence "not guilty";
}
```

### Mistake 3: Missing Default Case

```yh
// Wrong: No default case
match {
    case condition1 := consequence "result1";
    case condition2 := consequence "result2";
}
```

**Fix**: Always include default case:

```yh
match {
    case condition1 := consequence "result1";
    case condition2 := consequence "result2";
    case _ := consequence "default";
}
```

## Resources

- [Penal Code of Singapore](https://sso.agc.gov.sg/Act/PC1871)
- [Language Syntax](../language/syntax.md)
- [CLI Commands](../cli/commands.md)
- [Transpilers](../transpilers/overview.md)

## Next Steps

- [Custom Patterns](patterns.md) - Advanced legal patterns
- [Language Guide](../language/overview.md) - Complete Yuho reference
- [CLI Commands](../cli/commands.md) - Command-line tools
- [Transpilers](../transpilers/overview.md) - Generate diagrams and specifications
