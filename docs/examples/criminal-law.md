# Criminal Law Examples

Real-world examples of representing Singapore Criminal Law statutes in Yuho.

## Overview

These examples demonstrate how Yuho represents actual legal statutes from Singapore's Penal Code. Each example shows the progression from legal text to Yuho code to visual diagrams.

## Example 1: Cheating (Section 415)

### Legal Text

**Section 415 of the Penal Code**:

> Whoever, by deceiving any person, fraudulently or dishonestly induces the person so deceived to deliver any property to any person, or to consent that any person shall retain any property, or intentionally induces the person so deceived to do or omit to do anything which he would not do or omit if he were not so deceived, and which act or omission causes or is likely to cause damage or harm to that person in body, mind, reputation or property, is said to "cheat".

### Yuho Representation

```yh
// Section 415 - Cheating
struct Cheating {
    string accused,
    string victim,
    string action,
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

### Illustration A: False Government Service

**Legal Text**:
> "A, by falsely pretending to be in the Government service, intentionally deceives Z, and thus dishonestly induces Z to let him have on credit goods for which he does not mean to pay. A cheats."

**Yuho Code**:
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

**Key Points**:
- A deceived Z by false pretense
- A acted dishonestly (no intention to pay)
- Z was induced to give goods on credit
- Z suffered property damage (goods without payment)

---

## Example 2: Theft (Section 378)

### Legal Text

**Section 378 of the Penal Code**:

> Whoever, intending to take dishonestly any movable property out of the possession of any person without that person's consent, moves that property in order to such taking, is said to commit theft.

### Yuho Representation

```yh
// Section 378 - Theft
struct Theft {
    string accused,
    string victim,
    string property,
    bool dishonestIntention,
    bool movableProperty,
    bool outOfPossession,
    bool withoutConsent,
    bool movedProperty
}

match {
    case dishonestIntention && movableProperty && 
         outOfPossession && withoutConsent && movedProperty :=
        consequence "guilty of theft under Section 378";
    
    case _ :=
        consequence "not guilty of theft";
}
```

### Elements of Theft

1. **Dishonest Intention**: Intent to take dishonestly
2. **Movable Property**: Property must be movable
3. **Out of Possession**: Takes from another's possession
4. **Without Consent**: No permission from owner
5. **Movement**: Actually moves the property

### Simple Example

```yh
// Simple theft example
struct SimpleTheft {
    string accused := "John",
    string victim := "Shop Owner",
    string property := "Mobile phone",
    bool dishonestIntention := TRUE,
    bool movableProperty := TRUE,
    bool withoutConsent := TRUE,
    bool movedProperty := TRUE
}

match {
    case dishonestIntention && movableProperty && withoutConsent && movedProperty :=
        consequence "John commits theft";
    case _ :=
        consequence "not theft";
}
```

---

## Example 3: Criminal Trespass (Section 441)

### Legal Text

**Section 441 of the Penal Code**:

> Whoever enters into or upon property in the possession of another with intent to commit an offence or to intimidate, insult or annoy any person in possession of such property, or having lawfully entered into or upon such property, unlawfully remains there with intent thereby to intimidate, insult or annoy any such person, or with intent to commit an offence, is said to commit "criminal trespass".

### Yuho Representation

```yh
// Section 441 - Criminal Trespass
struct CriminalTrespass {
    string accused,
    string victim,
    string property,
    bool enteredProperty,
    bool unlawfulEntry,
    bool unlawfulRemaining,
    bool intentToCommitOffence,
    bool intentToIntimidate,
    bool intentToInsult,
    bool intentToAnnoy
}

match {
    case (enteredProperty && 
         (intentToCommitOffence || intentToIntimidate || intentToInsult || intentToAnnoy)) :=
        consequence "guilty of criminal trespass - unlawful entry";
    
    case (unlawfulRemaining && 
         (intentToCommitOffence || intentToIntimidate || intentToInsult || intentToAnnoy)) :=
        consequence "guilty of criminal trespass - unlawful remaining";
    
    case _ :=
        consequence "not guilty of criminal trespass";
}
```

### Two Forms of Criminal Trespass

**Form 1: Unlawful Entry**
- Enters property
- With specific intent (offence/intimidate/insult/annoy)

**Form 2: Unlawful Remaining**
- Lawfully entered initially
- Unlawfully remains
- With specific intent

---

## Example 4: Extortion (Section 383)

### Legal Text

**Section 383 of the Penal Code**:

> Whoever intentionally puts any person in fear of any harm to that person or to any other, and thereby dishonestly induces the person so put in fear to deliver to any person any property or valuable security, or anything signed or sealed which may be converted into a valuable security, commits "extortion".

### Yuho Representation

```yh
// Section 383 - Extortion
struct Extortion {
    string accused,
    string victim,
    bool intentionallyPutInFear,
    bool fearOfHarm,
    bool dishonestlyInduced,
    bool deliveredProperty,
    bool deliveredValuableSecurity
}

match {
    case intentionallyPutInFear && fearOfHarm && dishonestlyInduced &&
         (deliveredProperty || deliveredValuableSecurity) :=
        consequence "guilty of extortion under Section 383";
    
    case _ :=
        consequence "not guilty of extortion";
}
```

### Elements of Extortion

1. **Intentional Fear**: Intentionally puts person in fear
2. **Fear of Harm**: Fear of harm to that person or another
3. **Dishonest Inducement**: Dishonestly induces the frightened person
4. **Delivery**: Victim delivers property or valuable security

### Example Scenario

```yh
// Extortion example
struct ExtortionCase {
    string accused := "Gangster",
    string victim := "Shopkeeper",
    bool intentionallyPutInFear := TRUE,
    bool fearOfHarm := TRUE,
    bool dishonestlyInduced := TRUE,
    bool deliveredProperty := TRUE  // Protection money
}

match {
    case intentionallyPutInFear && fearOfHarm && 
         dishonestlyInduced && deliveredProperty :=
        consequence "guilty of extortion";
    case _ :=
        consequence "not guilty";
}
```

---

## Working with Examples

### Check an Example

```bash
# Validate the cheating example
yuho check example/cheating/cheating_illustration_A.yh
```

### Visualize an Example

```bash
# Generate flowchart
yuho draw example/cheating/s415_cheating_definition.yh -f flowchart -o cheating_flow.mmd

# Generate mindmap
yuho draw example/cheating/s415_cheating_definition.yh -f mindmap -o cheating_mind.mmd
```

### Verify an Example

```bash
# Generate Alloy specification
yuho alloy example/cheating/s415_cheating_definition.yh -o cheating.als

# Verify with Alloy Analyzer (if installed)
java -jar alloy.jar cheating.als
```

---

## Legal Reasoning Patterns

### Pattern 1: Conjunctive Requirements

When ALL elements must be present:

```yh
match {
    case element1 && element2 && element3 := consequence "guilty";
    case _ := consequence "not guilty";
}
```

**Example**: Theft requires ALL of: dishonest intention, movable property, without consent, movement.

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

---

## Best Practices

### 1. Clear Naming

```yh
// Good: Descriptive names
struct Cheating {
    string accused,
    bool deception,
    bool causedHarm
}

// Avoid: Unclear abbreviations
struct Ch {
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

---

## Additional Examples

Explore more examples in the repository:

- `example/cheating/` - Multiple cheating scenarios (A through K)
- See [GitHub Repository](https://github.com/gongahkia/yuho/tree/main/example)

---

## Resources

- [Penal Code of Singapore](https://sso.agc.gov.sg/Act/PC1871)
- [Language Syntax](../language/syntax.md)
- [CLI Commands](../cli/commands.md)
- [Transpilers](../transpilers/overview.md)

---

## Next Steps

- [Learn the full syntax](../language/syntax.md)
- [Try the quickstart guide](../getting-started/quickstart.md)
- [Explore match-case patterns](../language/match-case.md)
- [Use the CLI effectively](../cli/commands.md)

