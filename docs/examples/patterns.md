# Custom Patterns

Advanced legal patterns and reusable code structures for complex legal reasoning.

## Overview

This page demonstrates advanced patterns for representing complex legal concepts in Yuho:

- **Hierarchical Patterns** - Multi-level legal structures
- **Conditional Patterns** - Complex decision logic
- **Reusable Patterns** - Modular legal components
- **Integration Patterns** - Combining multiple legal concepts

## Pattern 1: Hierarchical Legal Structure

### Multi-Level Offense Classification

```yh
// Base offense structure
struct BaseOffense {
    string name,
    string section,
    bool isIndictable,
    money maxFine,
    int maxSentence
}

// Specific offense types
struct PropertyOffense {
    BaseOffense base,
    bool involvesTheft,
    bool involvesDamage,
    money value
}

struct ViolentOffense {
    BaseOffense base,
    bool involvesInjury,
    bool involvesWeapon,
    string injuryType
}

// Offense classification logic
match {
    case offense.base.isIndictable && offense.base.maxSentence > 7 :=
        consequence "serious offense";
    
    case offense.base.isIndictable :=
        consequence "indictable offense";
    
    case _ :=
        consequence "summary offense";
}
```

### Legal Hierarchy

```yh
// Legal system hierarchy
struct LegalSystem {
    string jurisdiction,
    string courtLevel,
    string offenseType
}

match {
    case courtLevel == "Supreme Court" :=
        consequence "highest court";
    
    case courtLevel == "High Court" :=
        consequence "superior court";
    
    case courtLevel == "District Court" :=
        consequence "inferior court";
    
    case _ :=
        consequence "unknown court level";
}
```

## Pattern 2: Conditional Legal Logic

### Age-Based Legal Treatment

```yh
struct Person {
    string name,
    int age,
    bool isMinor,
    bool isEligible
}

// Age-based legal treatment
match {
    case age < 18 :=
        consequence "juvenile treatment";
    
    case age >= 18 && age < 21 :=
        consequence "young adult treatment";
    
    case age >= 21 :=
        consequence "adult treatment";
    
    case _ :=
        consequence "unknown age treatment";
}
```

### Offense Severity Classification

```yh
struct OffenseSeverity {
    string offenseType,
    bool isViolent,
    bool isRepeat,
    money damageAmount
}

match {
    case isViolent && isRepeat :=
        consequence "severe punishment";
    
    case isViolent :=
        consequence "moderate punishment";
    
    case isRepeat :=
        consequence "enhanced punishment";
    
    case _ :=
        consequence "standard punishment";
}
```

## Pattern 3: Reusable Legal Components

### Legal Element Validation

```yh
// Reusable validation function
bool func validateLegalElements(bool element1, bool element2, bool element3) {
    match {
        case element1 && element2 && element3 :=
            consequence TRUE;
        case _ :=
            consequence FALSE;
    }
}

// Use in different contexts
struct Theft {
    bool dishonestIntention,
    bool movableProperty,
    bool withoutConsent,
    bool movedProperty
}

struct Cheating {
    bool deception,
    bool dishonest,
    bool harm
}

// Apply validation
bool theftValid := validateLegalElements(
    theft.dishonestIntention,
    theft.movableProperty,
    theft.withoutConsent
);

bool cheatingValid := validateLegalElements(
    cheating.deception,
    cheating.dishonest,
    cheating.harm
);
```

### Legal Relationship Patterns

```yh
// Legal relationship structure
struct LegalRelationship {
    string relationshipType,
    string party1,
    string party2,
    date startDate,
    bool isActive
}

// Relationship validation
bool func isValidRelationship(LegalRelationship rel) {
    match {
        case rel.isActive && rel.startDate != pass :=
            consequence TRUE;
        case _ :=
            consequence FALSE;
    }
}

// Use in different contexts
LegalRelationship marriage := {
    relationshipType := "marriage",
    party1 := "Alice",
    party2 := "Bob",
    startDate := 15-06-2020,
    isActive := TRUE
};

LegalRelationship contract := {
    relationshipType := "contract",
    party1 := "Company A",
    party2 := "Company B",
    startDate := 01-01-2024,
    isActive := TRUE
};
```

## Pattern 4: Integration Patterns

### Multi-Offense Scenarios

```yh
// Multiple offenses in one case
struct MultiOffenseCase {
    string caseNumber,
    bool hasTheft,
    bool hasCheating,
    bool hasAssault,
    bool isRepeatOffender
}

match {
    case hasTheft && hasCheating && hasAssault :=
        consequence "multiple serious offenses";
    
    case hasTheft && hasCheating :=
        consequence "property offenses";
    
    case hasAssault :=
        consequence "violent offense";
    
    case _ :=
        consequence "single offense";
}
```

### Legal Process Flow

```yh
// Legal process stages
struct LegalProcess {
    string stage,
    bool isComplete,
    string nextStage
}

match {
    case stage == "investigation" && isComplete :=
        consequence "proceed to charging";
    
    case stage == "charging" && isComplete :=
        consequence "proceed to trial";
    
    case stage == "trial" && isComplete :=
        consequence "proceed to sentencing";
    
    case stage == "sentencing" && isComplete :=
        consequence "case concluded";
    
    case _ :=
        consequence "continue current stage";
}
```

## Pattern 5: Temporal Legal Logic

### Time-Based Legal Rules

```yh
struct TemporalCase {
    date offenseDate,
    date currentDate,
    duration timeSinceOffense,
    bool isWithinLimitation
}

// Limitation period logic
match {
    case timeSinceOffense < 6 months :=
        consequence "recent offense";
    
    case timeSinceOffense < 2 years :=
        consequence "recent offense";
    
    case timeSinceOffense < 7 years :=
        consequence "old offense";
    
    case _ :=
        consequence "very old offense";
}
```

### Legal Deadlines

```yh
struct LegalDeadline {
    date deadline,
    date currentDate,
    bool isOverdue,
    string consequence
}

match {
    case isOverdue :=
        consequence "deadline missed";
    
    case deadline - currentDate < 7 days :=
        consequence "deadline approaching";
    
    case _ :=
        consequence "deadline on track";
}
```

## Pattern 6: Complex Decision Trees

### Legal Decision Matrix

```yh
struct LegalDecision {
    bool element1,
    bool element2,
    bool element3,
    bool element4,
    string result
}

match {
    case element1 && element2 && element3 && element4 :=
        consequence "all elements present - guilty";
    
    case element1 && element2 && element3 :=
        consequence "three elements present - likely guilty";
    
    case element1 && element2 :=
        consequence "two elements present - possibly guilty";
    
    case element1 :=
        consequence "one element present - unlikely guilty";
    
    case _ :=
        consequence "no elements present - not guilty";
}
```

### Legal Precedent Application

```yh
struct LegalPrecedent {
    string caseName,
    string legalPrinciple,
    bool isApplicable,
    string outcome
}

match {
    case isApplicable && legalPrinciple == "strict liability" :=
        consequence "apply strict liability";
    
    case isApplicable && legalPrinciple == "negligence" :=
        consequence "apply negligence standard";
    
    case isApplicable && legalPrinciple == "intent" :=
        consequence "apply intent requirement";
    
    case _ :=
        consequence "no applicable precedent";
}
```

## Pattern 7: Modular Legal Components

### Legal Module System

```yh
// Base legal module
scope LegalBase {
    struct LegalEntity {
        string name,
        string type,
        bool isActive
    }
    
    bool func isActive(LegalEntity entity) {
        match entity.isActive {
            case TRUE := consequence TRUE;
            case FALSE := consequence FALSE;
        }
    }
}

// Criminal law module
scope CriminalLaw {
    referencing LegalBase
    
    struct CriminalOffense {
        string name,
        string section,
        bool isIndictable,
        money maxFine,
        int maxSentence
    }
    
    bool func isSeriousOffense(CriminalOffense offense) {
        match {
            case offense.isIndictable && offense.maxSentence > 7 :=
                consequence TRUE;
            case _ :=
                consequence FALSE;
        }
    }
}

// Civil law module
scope CivilLaw {
    referencing LegalBase
    
    struct CivilClaim {
        string claimType,
        money amount,
        bool isSettled
    }
    
    bool func isHighValue(CivilClaim claim) {
        match {
            case claim.amount > $10000.00 :=
                consequence TRUE;
            case _ :=
                consequence FALSE;
        }
    }
}
```

## Pattern 8: Legal Validation Patterns

### Comprehensive Legal Validation

```yh
struct LegalValidation {
    bool syntaxValid,
    bool semanticValid,
    bool logicValid,
    bool completeValid
}

bool func validateLegalCode(LegalValidation validation) {
    match {
        case validation.syntaxValid && validation.semanticValid && 
             validation.logicValid && validation.completeValid :=
            consequence TRUE;
        case _ :=
            consequence FALSE;
    }
}

// Use in different contexts
LegalValidation theftValidation := {
    syntaxValid := TRUE,
    semanticValid := TRUE,
    logicValid := TRUE,
    completeValid := TRUE
};

LegalValidation cheatingValidation := {
    syntaxValid := TRUE,
    semanticValid := TRUE,
    logicValid := TRUE,
    completeValid := TRUE
};
```

## Best Practices for Patterns

### 1. Use Descriptive Names

```yh
// Good: Clear pattern names
struct LegalDecisionMatrix {
    bool element1,
    bool element2,
    bool element3
}

// Avoid: Generic names
struct Pattern {
    bool a,
    bool b,
    bool c
}
```

### 2. Document Legal Context

```yh
// Good: Include legal source
// Based on Section 415 - Cheating
struct CheatingPattern {
    bool deception,
    bool dishonest,
    bool harm
}
```

### 3. Use Modular Design

```yh
// Good: Modular components
scope LegalBase {
    // Base legal structures
}

scope CriminalLaw {
    referencing LegalBase
    // Criminal law specific structures
}
```

### 4. Validate Patterns

```yh
// Good: Include validation
bool func validatePattern(Pattern pattern) {
    match {
        case pattern.element1 && pattern.element2 :=
            consequence TRUE;
        case _ :=
            consequence FALSE;
    }
}
```

## Common Pattern Mistakes

### Mistake 1: Overly Complex Patterns

```yh
// Wrong: Too complex
struct OverlyComplex {
    bool a, bool b, bool c, bool d, bool e, bool f, bool g, bool h
}

match {
    case a && b && c && d && e && f && g && h :=
        consequence "result";
    case _ :=
        consequence "default";
}
```

**Fix**: Break into smaller patterns:

```yh
struct SimplePattern1 {
    bool a, bool b, bool c, bool d
}

struct SimplePattern2 {
    bool e, bool f, bool g, bool h
}
```

### Mistake 2: Missing Validation

```yh
// Wrong: No validation
struct Pattern {
    bool element1,
    bool element2
}

match {
    case element1 && element2 :=
        consequence "result";
    case _ :=
        consequence "default";
}
```

**Fix**: Include validation:

```yh
bool func validatePattern(Pattern pattern) {
    match {
        case pattern.element1 && pattern.element2 :=
            consequence TRUE;
        case _ :=
            consequence FALSE;
    }
}
```

### Mistake 3: Inconsistent Naming

```yh
// Wrong: Inconsistent naming
struct LegalPattern {
    bool element1,
    bool element2,
    bool element3
}

match {
    case element1 && element2 && element3 :=
        consequence "result";
    case _ :=
        consequence "default";
}
```

**Fix**: Use consistent naming:

```yh
struct LegalPattern {
    bool isElement1,
    bool isElement2,
    bool isElement3
}

match {
    case isElement1 && isElement2 && isElement3 :=
        consequence "result";
    case _ :=
        consequence "default";
}
```

## Resources

- [Language Syntax](../language/syntax.md) - Complete Yuho reference
- [CLI Commands](../cli/commands.md) - Command-line tools
- [Transpilers](../transpilers/overview.md) - Generate diagrams and specifications
- [Cheating Examples](cheating.md) - Specific legal examples

## Next Steps

- [Language Guide](../language/overview.md) - Complete Yuho reference
- [CLI Commands](../cli/commands.md) - Command-line tools
- [Transpilers](../transpilers/overview.md) - Generate diagrams and specifications
- [Development Guide](../development/contributing.md) - Contributing to Yuho
