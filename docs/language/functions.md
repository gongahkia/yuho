# Functions

Functions in Yuho provide a way to encapsulate legal logic and create reusable code patterns.

## Overview

Functions in Yuho are:

- **Pure** - No side effects, same input always produces same output
- **Type-Safe** - All parameters and return types are explicit
- **Immutable** - Cannot modify external state
- **Legal-Focused** - Designed for legal reasoning patterns

## Basic Syntax

```yh
returnType func functionName(parameterType parameterName) {
    // function body
    := returnExpression
}
```

### Example

```yh
int func add(int a, int b) {
    := a + b
}

int result := add(5, 3);  // result is 8
```

## Function Parameters

### Single Parameter

```yh
bool func isAdult(int age) {
    match age {
        case 18 := consequence TRUE;
        case _ := consequence FALSE;
    }
}

bool adult := isAdult(25);  // adult is TRUE
```

### Multiple Parameters

```yh
string func formatName(string firstName, string lastName) {
    := firstName + " " + lastName
}

string fullName := formatName("John", "Doe");  // fullName is "John Doe"
```

### Complex Parameters

```yh
struct Person {
    string name,
    int age,
    bool isMinor
}

bool func canVote(Person person) {
    match {
        case person.age >= 18 := consequence TRUE;
        case _ := consequence FALSE;
    }
}

Person voter := {
    name := "Alice",
    age := 25,
    isMinor := FALSE
};

bool eligible := canVote(voter);  // eligible is TRUE
```

## Return Types

### Simple Return Types

```yh
// Boolean return
bool func isGuilty(bool deception, bool dishonest, bool harm) {
    match {
        case deception && dishonest && harm := consequence TRUE;
        case _ := consequence FALSE;
    }
}

// String return
string func getOffenseType(string offense) {
    match offense {
        case "theft" := consequence "property crime";
        case "assault" := consequence "violent crime";
        case _ := consequence "other offense";
    }
}

// Integer return
int func calculateSentence(int baseSentence, bool isRepeatOffender) {
    match {
        case isRepeatOffender := consequence baseSentence * 2;
        case _ := consequence baseSentence;
    }
}
```

### Complex Return Types

```yh
struct Sentence {
    string type,
    int duration,
    money fine
}

Sentence func determineSentence(string offense, int age) {
    match offense {
        case "theft" := consequence {
            type := "imprisonment",
            duration := 2,
            fine := $1000.00
        };
        case "assault" := consequence {
            type := "imprisonment",
            duration := 5,
            fine := $2000.00
        };
        case _ := consequence {
            type := "unknown",
            duration := 0,
            fine := $0.00
        };
    }
}

Sentence sentence := determineSentence("theft", 25);
```

## Legal Examples

### Cheating Offense Check

```yh
struct Cheating {
    bool deception,
    bool dishonest,
    bool harm
}

bool func isCheating(Cheating case) {
    match {
        case case.deception && case.dishonest && case.harm := 
            consequence TRUE;
        case _ := 
            consequence FALSE;
    }
}

Cheating case1 := {
    deception := TRUE,
    dishonest := TRUE,
    harm := TRUE
};

bool guilty := isCheating(case1);  // guilty is TRUE
```

### Theft Offense Check

```yh
struct Theft {
    bool dishonestIntention,
    bool movableProperty,
    bool withoutConsent,
    bool movedProperty
}

bool func isTheft(Theft case) {
    match {
        case case.dishonestIntention && case.movableProperty && 
             case.withoutConsent && case.movedProperty :=
            consequence TRUE;
        case _ :=
            consequence FALSE;
    }
}

Theft case1 := {
    dishonestIntention := TRUE,
    movableProperty := TRUE,
    withoutConsent := TRUE,
    movedProperty := TRUE
};

bool guilty := isTheft(case1);  // guilty is TRUE
```

### Age-Based Sentencing

```yh
string func determineCourt(int age) {
    match {
        case age < 18 := consequence "juvenile court";
        case age >= 18 := consequence "adult court";
        case _ := consequence "unknown court";
    }
}

string court := determineCourt(25);  // court is "adult court"
```

### Offense Classification

```yh
string func classifyOffense(string offense) {
    match offense {
        case "theft" := consequence "property crime";
        case "assault" := consequence "violent crime";
        case "fraud" := consequence "white-collar crime";
        case _ := consequence "other offense";
    }
}

string classification := classifyOffense("theft");  // classification is "property crime"
```

## Advanced Patterns

### Pattern 1: Legal Element Validation

```yh
struct LegalElements {
    bool element1,
    bool element2,
    bool element3
}

bool func validateElements(LegalElements elements) {
    match {
        case elements.element1 && elements.element2 && elements.element3 :=
            consequence TRUE;
        case _ :=
            consequence FALSE;
    }
}
```

### Pattern 2: Conditional Logic

```yh
string func determinePunishment(string offense, int age, bool isRepeatOffender) {
    match {
        case offense == "theft" && age < 18 := consequence "juvenile probation";
        case offense == "theft" && isRepeatOffender := consequence "2 years imprisonment";
        case offense == "theft" := consequence "1 year imprisonment";
        case offense == "assault" && age < 18 := consequence "juvenile detention";
        case offense == "assault" := consequence "5 years imprisonment";
        case _ := consequence "unknown punishment";
    }
}
```

### Pattern 3: Hierarchical Decisions

```yh
string func determineCourt(int age, string offense) {
    match {
        case age < 18 := consequence "juvenile court";
        case age >= 18 && offense == "theft" := consequence "criminal court";
        case age >= 18 && offense == "assault" := consequence "criminal court";
        case _ := consequence "unknown court";
    }
}
```

## Function Composition

### Chaining Functions

```yh
bool func isEligible(int age) {
    match age {
        case 18 := consequence TRUE;
        case _ := consequence FALSE;
    }
}

string func getStatus(bool eligible) {
    match eligible {
        case TRUE := consequence "eligible";
        case FALSE := consequence "not eligible";
    }
}

string status := getStatus(isEligible(25));  // status is "eligible"
```

### Nested Function Calls

```yh
int func add(int a, int b) {
    := a + b
}

int func multiply(int a, int b) {
    := a * b
}

int result := multiply(add(2, 3), add(4, 1));  // result is 25
```

## Error Handling

### Validation Functions

```yh
bool func isValidAge(int age) {
    match {
        case age >= 0 && age <= 150 := consequence TRUE;
        case _ := consequence FALSE;
    }
}

bool func isValidName(string name) {
    match {
        case name != "" := consequence TRUE;
        case _ := consequence FALSE;
    }
}
```

### Error Return Values

```yh
string func processCase(string caseNumber, int age) {
    match {
        case caseNumber == "" := consequence "error: missing case number";
        case age < 0 := consequence "error: invalid age";
        case age < 18 := consequence "juvenile case";
        case age >= 18 := consequence "adult case";
        case _ := consequence "error: unknown age";
    }
}
```

## Best Practices

### 1. Use Descriptive Names

```yh
// Good: Clear function name
bool func isCheating(Cheating case) {
    // function body
}

// Avoid: Unclear function name
bool func check(Cheating case) {
    // function body
}
```

### 2. Use Appropriate Types

```yh
// Good: Legal-specific types
bool func isEligible(Person person) {
    match person.age {
        case 18 := consequence TRUE;
        case _ := consequence FALSE;
    }
}

// Avoid: Generic types
bool func isEligible(string name, int age) {
    match age {
        case 18 := consequence TRUE;
        case _ := consequence FALSE;
    }
}
```

### 3. Document Legal Context

```yh
// Good: Include legal source
// Section 415 - Cheating
bool func isCheating(Cheating case) {
    match {
        case case.deception && case.dishonest && case.harm :=
            consequence TRUE;
        case _ :=
            consequence FALSE;
    }
}
```

### 4. Use Match-Case for Logic

```yh
// Good: Use match-case for conditional logic
string func determineCourt(int age) {
    match {
        case age < 18 := consequence "juvenile court";
        case age >= 18 := consequence "adult court";
        case _ := consequence "unknown court";
    }
}

// Avoid: Complex nested conditions
string func determineCourt(int age) {
    // Complex nested logic would be harder to read
}
```

## Common Patterns

### Pattern 1: Validation Functions

```yh
bool func validateInput(string input) {
    match {
        case input != "" := consequence TRUE;
        case _ := consequence FALSE;
    }
}
```

### Pattern 2: Classification Functions

```yh
string func classifyOffense(string offense) {
    match offense {
        case "theft" := consequence "property crime";
        case "assault" := consequence "violent crime";
        case _ := consequence "other offense";
    }
}
```

### Pattern 3: Decision Functions

```yh
string func makeDecision(bool condition1, bool condition2) {
    match {
        case condition1 && condition2 := consequence "decision A";
        case condition1 := consequence "decision B";
        case condition2 := consequence "decision C";
        case _ := consequence "decision D";
    }
}
```

## Troubleshooting

### Common Errors

#### Error 1: Missing Return Expression

```yh
// Error: Missing return expression
int func add(int a, int b) {
    // Missing: := a + b
}
```

**Solution**: Always include return expression:

```yh
int func add(int a, int b) {
    := a + b
}
```

#### Error 2: Type Mismatch

```yh
// Error: string cannot be int
int func getAge(string name) {
    := "25"  // Error: string cannot be int
}
```

**Solution**: Use correct types:

```yh
int func getAge(string name) {
    := 25  // Correct: int value
}
```

#### Error 3: Missing Parameters

```yh
// Error: Missing parameter
int func add(int a) {
    := a + b  // Error: b is not defined
}
```

**Solution**: Include all required parameters:

```yh
int func add(int a, int b) {
    := a + b
}
```

## Performance Considerations

### Simple Functions

```yh
// Good: Simple, fast function
bool func isTrue(bool value) {
    match value {
        case TRUE := consequence TRUE;
        case FALSE := consequence FALSE;
    }
}
```

### Complex Functions

```yh
// Good: Break complex logic into smaller functions
bool func isCheating(Cheating case) {
    match {
        case case.deception && case.dishonest && case.harm :=
            consequence TRUE;
        case _ :=
            consequence FALSE;
    }
}
```

## Next Steps

- [Match-Case](match-case.md) - Using match-case in functions
- [Structs](structs.md) - Working with structs in functions
- [Type System](types.md) - Type-safe function parameters
- [Syntax Reference](syntax.md) - Complete syntax guide
