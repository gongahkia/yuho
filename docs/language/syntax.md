# Language Syntax

Complete syntax reference for the Yuho language.

## Overview

Yuho is a domain-specific language designed for representing legal statutes and reasoning patterns. It features:

- **Strong, static typing** - All types known at compile time
- **Functional paradigm** - Immutable values, no side effects
- **Pattern matching** - Match-case as primary control structure
- **No loops** - Legal statutes don't contain loops
- **Clean syntax** - Designed for legal professionals

## File Structure

Yuho source files use the `.yh` extension and follow this general structure:

```yh
// Comments explaining the legal context
// Section 415 - Cheating

// Import statements (optional)
referencing Cheating from cheating_module

// Struct definitions
struct Cheating {
    string accused,
    bool deception,
    bool harm
}

// Variable declarations
string caseName := "Example Case"

// Match-case logic
match {
    case condition := consequence result;
    case _ := consequence default;
}
```

## Comments

Yuho supports both single-line and multi-line comments:

```yh
// Single-line comment

/*
Multi-line
comment
*/
```

### Best Practices

- Always include the legal source (e.g., "Section 415 - Cheating")
- Explain complex conditions
- Document the legal context

```yh
// Section 415 - Cheating
// This struct represents the elements of cheating under Singapore Penal Code

struct Cheating {
    // The person accused of cheating
    string accused,
    // Whether deception occurred
    bool deception,
    // Whether harm was caused
    bool harm
}
```

## Variable Declaration

Variables are declared with the `:=` operator and are immutable:

```yh
type variableName := value;
```

### Examples

```yh
// Basic types
int age := 25;
string name := "John Doe";
bool isGuilty := TRUE;
money fine := $500.00;

// Complex types
Cheating case1 := {
    accused := "Alice",
    deception := TRUE,
    harm := TRUE
};
```

### Union Types

Use `||` for variables that could be multiple types:

```yh
pass || money optionalFine := pass;
string || int flexibleValue := "hello";
```

## Naming Conventions

- **Files**: `snake_case.yh` (e.g., `criminal_law.yh`)
- **Variables**: `camelCase` (e.g., `isGuilty`)
- **Structs**: `PascalCase` (e.g., `Cheating`)
- **Functions**: `camelCase` (e.g., `checkValidity`)

## Operators

### Arithmetic Operators

```yh
+  // Addition
-  // Subtraction
*  // Multiplication
/  // Division
// // Integer division
%  // Modulo
```

### Comparison Operators

```yh
==  // Equality
!=  // Inequality
>   // Greater than
<   // Less than
>=  // Greater than or equal
<=  // Less than or equal
```

### Logical Operators

```yh
and  // Logical AND
or   // Logical OR
not  // Logical NOT
&&   // Alternative AND
||   // Alternative OR
!    // Alternative NOT
```

## Control Structures

### Match-Case

The primary control structure in Yuho:

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

### Examples

```yh
// Simple match
match {
    case isGuilty := consequence "guilty";
    case _ := consequence "not guilty";
}

// Match with expression
match age {
    case 18 := consequence "adult";
    case 17 := consequence "minor";
    case _ := consequence "other";
}

// Complex conditions
match {
    case deception && dishonest && harm := 
        consequence "guilty of cheating";
    case _ := 
        consequence "not guilty";
}
```

## Functions

Functions are declared with the `func` keyword:

```yh
returnType func functionName(parameterType parameterName) {
    // function body
    := returnExpression
}
```

### Examples

```yh
// Simple function
int func add(int a, int b) {
    := a + b
}

// Complex function
string func checkGuilt(bool deception, bool dishonest, bool harm) {
    match {
        case deception && dishonest && harm := 
            consequence "guilty";
        case _ := 
            consequence "not guilty";
    }
}
```

## Scopes and Modules

### Scopes

Create named scopes for organization:

```yh
scope LegalConcepts {
    struct Theft {
        string accused,
        bool dishonestIntention,
        bool movedProperty
    }
    
    bool func isTheft(Theft case) {
        match {
            case case.dishonestIntention && case.movedProperty := 
                consequence TRUE;
            case _ := 
                consequence FALSE;
        }
    }
}
```

### Imports

Import from other files:

```yh
// Import everything from a module
referencing theft_module

// Import specific scope
referencing Theft from theft_module

// Use imported elements
Theft case1 := {
    accused := "Alice",
    dishonestIntention := TRUE,
    movedProperty := TRUE
}
```

## Type System

### Primitive Types

```yh
int      // Integer numbers
float    // Floating-point numbers
bool     // TRUE or FALSE
string   // Text in quotes
percent  // Percentage (25%)
money    // Currency ($100.50)
date     // Dates (DD-MM-YYYY)
duration // Time periods (5 days)
```

### Custom Types

Define custom types using structs:

```yh
struct LegalConcept {
    string name,
    bool isValid,
    money penalty
}
```

## Error Handling

Yuho uses pattern matching for error handling:

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

### 2. Use Descriptive Names

```yh
// Good
struct Cheating {
    string accused,
    bool deception,
    bool harm
}

// Avoid
struct C {
    string a,
    bool d,
    bool h
}
```

### 3. Comment Legal Context

```yh
// Section 415 - Cheating
// Whoever, by deceiving any person, fraudulently or dishonestly...
struct Cheating {
    // The person accused of the offense
    string accused,
    // Whether deception occurred
    bool deception,
    // Whether harm was caused
    bool harm
}
```

### 4. Complete Case Coverage

```yh
match {
    case severeCondition := consequence "severe punishment";
    case moderateCondition := consequence "moderate punishment";
    case minorCondition := consequence "minor punishment";
    // Always include default
    case _ := consequence "not guilty";
}
```

## Common Patterns

### Pattern 1: Conjunctive Requirements

When ALL elements must be present:

```yh
match {
    case element1 && element2 && element3 := consequence "guilty";
    case _ := consequence "not guilty";
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

## Syntax Validation

Use the CLI to validate syntax:

```bash
# Check syntax
yuho check example.yh

# Check with verbose output
yuho check example.yh --verbose
```

## Next Steps

- [Type System](types.md) - Learn about Yuho's type system
- [Structs](structs.md) - Working with data structures
- [Match-Case](match-case.md) - Pattern matching patterns
- [Functions](functions.md) - Function definitions and usage
- [Comments](comments.md) - Documentation best practices
