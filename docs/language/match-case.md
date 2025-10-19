# Match-Case

Match-case is Yuho's primary control structure for pattern matching and conditional logic.

## Overview

Match-case in Yuho provides:

- **Pattern Matching** - Match values against patterns
- **Exhaustive Coverage** - Must handle all possible cases
- **Legal Logic** - Designed for legal reasoning patterns
- **Type Safety** - Compile-time pattern validation

## Basic Syntax

```yh
match {
    case condition1 := consequence result1;
    case condition2 := consequence result2;
    case _ := consequence default;
}
```

### With Expression

```yh
match expression {
    case value1 := consequence result1;
    case value2 := consequence result2;
    case _ := consequence default;
}
```

## Simple Examples

### Boolean Matching

```yh
bool isGuilty := TRUE;

match isGuilty {
    case TRUE := consequence "guilty";
    case FALSE := consequence "not guilty";
    case _ := consequence "unknown";
}
```

### String Matching

```yh
string offense := "theft";

match offense {
    case "theft" := consequence "property crime";
    case "assault" := consequence "violent crime";
    case "fraud" := consequence "white-collar crime";
    case _ := consequence "other offense";
}
```

### Integer Matching

```yh
int age := 25;

match age {
    case 18 := consequence "just became adult";
    case 21 := consequence "legal drinking age";
    case 65 := consequence "retirement age";
    case _ := consequence "other age";
}
```

## Legal Examples

### Cheating Offense

```yh
struct Cheating {
    bool deception,
    bool dishonest,
    bool harm
}

Cheating case1 := {
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

### Theft Offense

```yh
struct Theft {
    bool dishonestIntention,
    bool movableProperty,
    bool withoutConsent,
    bool movedProperty
}

Theft case1 := {
    dishonestIntention := TRUE,
    movableProperty := TRUE,
    withoutConsent := TRUE,
    movedProperty := TRUE
};

match {
    case case1.dishonestIntention && case1.movableProperty && 
         case1.withoutConsent && case1.movedProperty :=
        consequence "guilty of theft";
    case _ :=
        consequence "not guilty of theft";
}
```

### Age-Based Sentencing

```yh
int age := 25;
bool isFirstOffense := TRUE;

match {
    case age < 18 := consequence "juvenile court";
    case age >= 18 && isFirstOffense := consequence "probation";
    case age >= 18 && not isFirstOffense := consequence "prison";
    case _ := consequence "unknown";
}
```

## Complex Patterns

### Pattern 1: Conjunctive Requirements

When ALL elements must be present:

```yh
match {
    case element1 && element2 && element3 := consequence "guilty";
    case _ := consequence "not guilty";
}
```

**Example**: Theft requires ALL of: dishonest intention, movable property, without consent, movement.

```yh
match {
    case dishonestIntention && movableProperty && 
         withoutConsent && movedProperty :=
        consequence "guilty of theft";
    case _ :=
        consequence "not guilty of theft";
}
```

### Pattern 2: Disjunctive Requirements

When ANY element is sufficient:

```yh
match {
    case element1 || element2 || element3 := consequence "guilty";
    case _ := consequence "not guilty";
}
```

**Example**: Cheating can involve delivery of property OR consent to retain OR induced action/omission.

```yh
match {
    case inducedDeliveryOfProperty || inducedConsentToRetain || 
         inducedActionOrOmission :=
        consequence "guilty of cheating";
    case _ :=
        consequence "not guilty of cheating";
}
```

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

```yh
match {
    case deception && (fraudulent || dishonest) && 
         (inducedDeliveryOfProperty || inducedConsentToRetain || 
          inducedActionOrOmission) && causesDamageOrHarm :=
        consequence "guilty of cheating";
    case _ :=
        consequence "not guilty of cheating";
}
```

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

**Example**: Sentencing based on offense severity.

```yh
match {
    case violentOffense && repeatOffender := consequence "life imprisonment";
    case violentOffense := consequence "10 years imprisonment";
    case propertyOffense := consequence "2 years imprisonment";
    case _ := consequence "not guilty";
}
```

## Advanced Patterns

### Pattern 5: Hierarchical Conditions

```yh
match {
    case isMinor && violentOffense := consequence "juvenile detention";
    case isMinor := consequence "juvenile probation";
    case violentOffense := consequence "prison";
    case _ := consequence "probation";
}
```

### Pattern 6: Threshold Conditions

```yh
int damageAmount := 5000;

match {
    case damageAmount >= 10000 := consequence "felony";
    case damageAmount >= 1000 := consequence "misdemeanor";
    case damageAmount > 0 := consequence "infraction";
    case _ := consequence "no offense";
}
```

### Pattern 7: Temporal Conditions

```yh
date offenseDate := 01-01-2024;
date currentDate := 15-12-2024;
duration timeSinceOffense := currentDate - offenseDate;

match {
    case timeSinceOffense < 30 days := consequence "recent offense";
    case timeSinceOffense < 1 year := consequence "recent offense";
    case timeSinceOffense < 5 years := consequence "old offense";
    case _ := consequence "very old offense";
}
```

## Working with Structs

### Struct Field Matching

```yh
struct Person {
    string name,
    int age,
    bool isMinor
}

Person person := {
    name := "Alice",
    age := 25,
    isMinor := FALSE
};

match person.isMinor {
    case TRUE := consequence "juvenile court";
    case FALSE := consequence "adult court";
    case _ := consequence "unknown";
}
```

### Multiple Struct Fields

```yh
match {
    case person.isMinor && person.age < 16 := consequence "child court";
    case person.isMinor := consequence "juvenile court";
    case person.age >= 18 := consequence "adult court";
    case _ := consequence "unknown";
}
```

### Struct Type Matching

```yh
struct Offense {
    string name,
    money penalty
}

Offense offense := {
    name := "theft",
    penalty := $1000.00
};

match offense.name {
    case "theft" := consequence "property crime";
    case "assault" := consequence "violent crime";
    case "fraud" := consequence "white-collar crime";
    case _ := consequence "other offense";
}
```

## Function Integration

### Match-Case in Functions

```yh
string func determineCourt(Person person) {
    match {
        case person.isMinor := consequence "juvenile court";
        case person.age >= 18 := consequence "adult court";
        case _ := consequence "unknown court";
    }
}

string court := determineCourt(person);
```

### Match-Case as Return Value

```yh
bool func isEligible(Person person) {
    match {
        case person.age >= 18 := consequence TRUE;
        case _ := consequence FALSE;
    }
}

bool eligible := isEligible(person);
```

### Complex Function Logic

```yh
string func determineSentence(Offense offense, Person person) {
    match {
        case offense.name == "theft" && person.isMinor := 
            consequence "juvenile probation";
        case offense.name == "theft" := 
            consequence "2 years imprisonment";
        case offense.name == "assault" && person.isMinor := 
            consequence "juvenile detention";
        case offense.name == "assault" := 
            consequence "5 years imprisonment";
        case _ := 
            consequence "unknown sentence";
    }
}

string sentence := determineSentence(offense, person);
```

## Error Handling

### Default Cases

Always include a default case:

```yh
match {
    case condition1 := consequence result1;
    case condition2 := consequence result2;
    // Always include default case
    case _ := consequence default;
}
```

### Exhaustive Coverage

Ensure all possible cases are covered:

```yh
bool isGuilty := TRUE;

match isGuilty {
    case TRUE := consequence "guilty";
    case FALSE := consequence "not guilty";
    // No default case needed - all boolean values covered
}
```

### Error Cases

```yh
match {
    case validCondition := consequence "success";
    case invalidCondition := consequence "error";
    case _ := consequence "unknown error";
}
```

## Best Practices

### 1. Always Include Default Cases

```yh
match {
    case condition1 := consequence result1;
    case condition2 := consequence result2;
    // Always include default case
    case _ := consequence default;
}
```

### 2. Use Clear Conditions

```yh
// Good: Clear conditions
match {
    case deception && dishonest && harm := consequence "guilty";
    case _ := consequence "not guilty";
}

// Avoid: Unclear conditions
match {
    case a && b && c := consequence "guilty";
    case _ := consequence "not guilty";
}
```

### 3. Group Related Cases

```yh
match {
    case violentOffense := consequence "severe punishment";
    case propertyOffense := consequence "moderate punishment";
    case minorOffense := consequence "light punishment";
    case _ := consequence "not guilty";
}
```

### 4. Use Comments for Complex Logic

```yh
match {
    // Cheating requires: deception + (fraudulent OR dishonest) + harm
    case deception && (fraudulent || dishonest) && harm := 
        consequence "guilty of cheating";
    case _ := 
        consequence "not guilty of cheating";
}
```

## Common Patterns

### Pattern 1: Legal Elements

```yh
match {
    case actusReus && mensRea := consequence "guilty";
    case _ := consequence "not guilty";
}
```

### Pattern 2: Age-Based Logic

```yh
match {
    case age < 18 := consequence "juvenile";
    case age >= 18 := consequence "adult";
    case _ := consequence "unknown age";
}
```

### Pattern 3: Offense Severity

```yh
match {
    case violentOffense := consequence "severe punishment";
    case propertyOffense := consequence "moderate punishment";
    case minorOffense := consequence "light punishment";
    case _ := consequence "not guilty";
}
```

### Pattern 4: Conditional Requirements

```yh
match {
    case baseCondition && (option1 || option2) && finalCondition :=
        consequence "guilty";
    case _ :=
        consequence "not guilty";
}
```

## Troubleshooting

### Common Errors

#### Error 1: Missing Default Case

```yh
// Error: Missing default case
match {
    case condition1 := consequence result1;
    case condition2 := consequence result2;
    // Missing: case _ := consequence default;
}
```

**Solution**: Always include default case:

```yh
match {
    case condition1 := consequence result1;
    case condition2 := consequence result2;
    case _ := consequence default;
}
```

#### Error 2: Type Mismatch

```yh
int age := 25;

// Error: string cannot be int
// match age {
//     case "25" := consequence "age 25";
//     case _ := consequence "other age";
// }
```

**Solution**: Use correct types:

```yh
match age {
    case 25 := consequence "age 25";
    case _ := consequence "other age";
}
```

#### Error 3: Incomplete Coverage

```yh
bool isGuilty := TRUE;

// Error: Missing FALSE case
// match isGuilty {
//     case TRUE := consequence "guilty";
//     // Missing: case FALSE := consequence "not guilty";
// }
```

**Solution**: Cover all possible values:

```yh
match isGuilty {
    case TRUE := consequence "guilty";
    case FALSE := consequence "not guilty";
}
```

## Performance Considerations

### Simple Conditions First

```yh
match {
    case simpleCondition := consequence "simple result";
    case complexCondition := consequence "complex result";
    case _ := consequence "default";
}
```

### Avoid Redundant Conditions

```yh
// Good: Non-overlapping conditions
match {
    case age < 18 := consequence "juvenile";
    case age >= 18 := consequence "adult";
    case _ := consequence "unknown";
}

// Avoid: Overlapping conditions
match {
    case age < 18 := consequence "juvenile";
    case age < 21 := consequence "young adult";  // Overlaps with above
    case age >= 18 := consequence "adult";
    case _ := consequence "unknown";
}
```

## Next Steps

- [Functions](functions.md) - Using match-case in functions
- [Structs](structs.md) - Pattern matching with structs
- [Type System](types.md) - Type-safe pattern matching
- [Syntax Reference](syntax.md) - Complete syntax guide
