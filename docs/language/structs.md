# Structs

Structs are Yuho's primary data structure for representing legal concepts and relationships.

## Overview

Structs in Yuho are:

- **Immutable** - All fields are immutable once set
- **Type-Safe** - All fields have explicit types
- **Legal-Focused** - Designed for legal concepts
- **Flexible** - Can represent various data structures

## Basic Syntax

```yh
struct StructName {
    type field1,
    type field2,
    type field3
}
```

### Example

```yh
struct Person {
    string name,
    int age,
    bool isMinor
}
```

## Creating Struct Instances

### Basic Instantiation

```yh
Person defendant := {
    name := "Alice",
    age := 25,
    isMinor := FALSE
};
```

### Accessing Fields

```yh
string defendantName := defendant.name;
int defendantAge := defendant.age;
bool isMinor := defendant.isMinor;
```

## Legal Examples

### Criminal Offense

```yh
struct CriminalOffense {
    string name,
    string section,
    money maxFine,
    int maxSentence,
    bool isIndictable
}

CriminalOffense theft := {
    name := "theft",
    section := "378",
    maxFine := $5000.00,
    maxSentence := 7,
    isIndictable := TRUE
};
```

### Case Facts

```yh
struct CaseFacts {
    string caseNumber,
    string accused,
    date offenseDate,
    string location,
    bool isGuilty,
    money penalty
}

CaseFacts case1 := {
    caseNumber := "CR-2024-001",
    accused := "John Doe",
    offenseDate := 01-01-2024,
    location := "Singapore",
    isGuilty := TRUE,
    penalty := $1000.00
};
```

### Legal Entity

```yh
struct LegalEntity {
    string name,
    string type,  // "person", "corporation", "government"
    bool isMinor,
    date dateOfBirth,
    string nationality
}

LegalEntity defendant := {
    name := "Alice Smith",
    type := "person",
    isMinor := FALSE,
    dateOfBirth := 15-03-1990,
    nationality := "Singaporean"
};
```

## Nested Structs

### Hierarchical Structures

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

Person person := {
    name := "John Doe",
    age := 30,
    address := {
        street := "123 Main Street",
        city := "Singapore",
        postalCode := "123456"
    }
};
```

### Accessing Nested Fields

```yh
string street := person.address.street;
string city := person.address.city;
```

## Struct Patterns

### Pattern 1: Legal Concept

```yh
struct LegalConcept {
    string name,
    string definition,
    bool isActive,
    date effectiveDate
}

LegalConcept concept := {
    name := "theft",
    definition := "dishonest taking of movable property",
    isActive := TRUE,
    effectiveDate := 01-01-1872
};
```

### Pattern 2: Offense Elements

```yh
struct OffenseElements {
    string actusReus,  // physical element
    string mensRea,    // mental element
    bool isComplete,
    string consequence
}

OffenseElements theftElements := {
    actusReus := "dishonest taking of movable property",
    mensRea := "intention to permanently deprive",
    isComplete := TRUE,
    consequence := "guilty of theft"
};
```

### Pattern 3: Legal Relationship

```yh
struct LegalRelationship {
    string relationshipType,
    string party1,
    string party2,
    date startDate,
    bool isActive
}

LegalRelationship marriage := {
    relationshipType := "marriage",
    party1 := "Alice",
    party2 := "Bob",
    startDate := 15-06-2020,
    isActive := TRUE
};
```

## Alternative Data Structures

### Array-like Structure

```yh
struct Array3 {
    string 0,
    string 1,
    string 2
}

Array3 colors := {
    0 := "red",
    1 := "green",
    2 := "blue"
};

string firstColor := colors.0;  // "red"
string secondColor := colors.1; // "green"
```

### Tuple-like Structure

```yh
struct Tuple3 {
    string 0,
    int 1,
    bool 2
}

Tuple3 data := {
    0 := "hello",
    1 := 42,
    2 := TRUE
};
```

### Dictionary-like Structure

```yh
struct Dictionary {
    string key1,
    string key2,
    string key3
}

Dictionary config := {
    key1 := "value1",
    key2 := "value2",
    key3 := "value3"
};
```

### Enum-like Structure

```yh
struct Status {
    pending,
    approved,
    rejected
}

Status currentStatus := Status.pending;
```

## Working with Structs

### Pattern Matching

```yh
match defendant.isMinor {
    case TRUE := consequence "juvenile court";
    case FALSE := consequence "adult court";
    case _ := consequence "unknown";
}
```

### Conditional Logic

```yh
match {
    case defendant.age < 18 := consequence "juvenile";
    case defendant.age >= 18 := consequence "adult";
    case _ := consequence "unknown age";
}
```

### Function Parameters

```yh
bool func isEligible(Person person) {
    match {
        case person.age >= 18 := consequence TRUE;
        case _ := consequence FALSE;
    }
}

bool eligible := isEligible(defendant);
```

### Function Returns

```yh
Person func createPerson(string name, int age) {
    := {
        name := name,
        age := age,
        isMinor := age < 18
    }
}

Person newPerson := createPerson("Alice", 25);
```

## Struct Validation

### Type Checking

```yh
struct ValidPerson {
    string name,
    int age,
    bool isMinor
}

// Valid instantiation
ValidPerson person1 := {
    name := "Alice",
    age := 25,
    isMinor := FALSE
};

// Invalid instantiation (would cause error)
// ValidPerson person2 := {
//     name := "Bob",
//     age := "25",  // Error: string cannot be int
//     isMinor := FALSE
// };
```

### Field Validation

```yh
bool func validatePerson(Person person) {
    match {
        case person.name == "" := consequence FALSE;
        case person.age < 0 := consequence FALSE;
        case _ := consequence TRUE;
    }
}

bool isValid := validatePerson(defendant);
```

## Best Practices

### 1. Use Descriptive Names

```yh
// Good: Clear legal context
struct CriminalOffense {
    string name,
    money maxFine,
    int maxSentence
}

// Avoid: Generic names
struct Thing {
    string a,
    money b,
    int c
}
```

### 2. Group Related Fields

```yh
// Good: Logical grouping
struct Case {
    string caseNumber,
    string accused,
    date offenseDate,
    string location,
    bool isGuilty,
    money penalty
}

// Avoid: Mixed concerns
struct Case {
    string caseNumber,
    string weather,
    int randomNumber,
    bool isGuilty
}
```

### 3. Use Appropriate Types

```yh
// Good: Legal-specific types
struct Offense {
    string name,
    money maxFine,
    int maxSentence,
    date effectiveDate
}

// Avoid: Generic types
struct Offense {
    string name,
    float maxFine,
    string maxSentence,
    string effectiveDate
}
```

### 4. Document Legal Context

```yh
// Good: Include legal source
// Section 378 - Theft
struct Theft {
    string accused,
    bool dishonestIntention,
    bool movedProperty
}
```

## Common Patterns

### Pattern 1: Legal Definition

```yh
struct LegalDefinition {
    string term,
    string definition,
    string source,
    date effectiveDate
}

LegalDefinition theft := {
    term := "theft",
    definition := "dishonest taking of movable property",
    source := "Section 378, Penal Code",
    effectiveDate := 01-01-1872
};
```

### Pattern 2: Case Summary

```yh
struct CaseSummary {
    string caseNumber,
    string accused,
    string offense,
    bool isGuilty,
    money penalty,
    int sentence
}

CaseSummary summary := {
    caseNumber := "CR-2024-001",
    accused := "John Doe",
    offense := "theft",
    isGuilty := TRUE,
    penalty := $1000.00,
    sentence := 6
};
```

### Pattern 3: Legal Relationship

```yh
struct LegalRelationship {
    string relationshipType,
    string party1,
    string party2,
    date startDate,
    bool isActive
}

LegalRelationship marriage := {
    relationshipType := "marriage",
    party1 := "Alice",
    party2 := "Bob",
    startDate := 15-06-2020,
    isActive := TRUE
};
```

## Advanced Usage

### Generic Structs

```yh
struct Container {
    string 0,
    string 1,
    string 2
}

Container items := {
    0 := "item1",
    1 := "item2",
    2 := "item3"
};
```

### Recursive Structures

```yh
struct TreeNode {
    string value,
    TreeNode left,
    TreeNode right
}

TreeNode root := {
    value := "root",
    left := pass,
    right := pass
};
```

### Union Types in Structs

```yh
struct FlexibleValue {
    string || int || bool value
}

FlexibleValue flex1 := { value := "hello" };
FlexibleValue flex2 := { value := 42 };
FlexibleValue flex3 := { value := TRUE };
```

## Struct Limitations

### Immutability

```yh
struct Person {
    string name,
    int age
}

Person person := {
    name := "Alice",
    age := 25
};

// This would cause an error
// person.name := "Bob";  // Error: cannot modify immutable field
```

### No Dynamic Fields

```yh
// Structs have fixed fields
struct Person {
    string name,
    int age
}

// Cannot add fields dynamically
// person.email := "alice@example.com";  // Error: field doesn't exist
```

## Troubleshooting

### Common Errors

#### Error 1: Type Mismatch

```yh
struct Person {
    string name,
    int age
}

// Error: string cannot be int
// Person person := {
//     name := "Alice",
//     age := "25"  // Error: string cannot be int
// };
```

**Solution**: Use correct types:

```yh
Person person := {
    name := "Alice",
    age := 25  // Correct: int value
};
```

#### Error 2: Missing Fields

```yh
struct Person {
    string name,
    int age,
    bool isMinor
}

// Error: missing field
// Person person := {
//     name := "Alice",
//     age := 25
//     // Missing: isMinor
// };
```

**Solution**: Include all required fields:

```yh
Person person := {
    name := "Alice",
    age := 25,
    isMinor := FALSE
};
```

#### Error 3: Extra Fields

```yh
struct Person {
    string name,
    int age
}

// Error: extra field
// Person person := {
//     name := "Alice",
//     age := 25,
//     email := "alice@example.com"  // Error: field doesn't exist
// };
```

**Solution**: Only include defined fields:

```yh
Person person := {
    name := "Alice",
    age := 25
};
```

## Next Steps

- [Type System](types.md) - Understanding Yuho's type system
- [Match-Case](match-case.md) - Pattern matching with structs
- [Functions](functions.md) - Working with structs in functions
- [Syntax Reference](syntax.md) - Complete syntax guide
