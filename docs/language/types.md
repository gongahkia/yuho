# Type System

Yuho's type system provides strong, static typing designed for legal reasoning.

## Overview

Yuho features a comprehensive type system that ensures:

- **Type Safety** - All types are known at compile time
- **Immutability** - All values are immutable by default
- **Legal Relevance** - Types designed for legal concepts
- **No Type Coercion** - Strict type checking prevents errors

## Primitive Types

### Numeric Types

#### Integer (`int`)
Whole numbers of any precision:

```yh
int age := 25;
int count := 1000;
int negative := -42;
```

#### Float (`float`)
Floating-point numbers:

```yh
float percentage := 0.25;
float precise := 3.14159;
float negative := -2.5;
```

#### Percent (`percent`)
Percentage values with `%` suffix:

```yh
percent taxRate := 25%;  // Evaluates to 0.25
percent discount := 10%; // Evaluates to 0.10
percent penalty := 100%; // Evaluates to 1.00
```

#### Money (`money`)
Currency values with `$` prefix:

```yh
money fine := $500.00;
money salary := $50,000.00;
money largeAmount := $1,000,000.00;
```

### Text Types

#### String (`string`)
Text enclosed in double quotes:

```yh
string name := "John Doe";
string offense := "theft";
string description := "A person commits theft when...";
```

### Boolean (`bool`)
Logical values:

```yh
bool isGuilty := TRUE;
bool isMinor := FALSE;
bool hasPermission := TRUE;
```

### Temporal Types

#### Date (`date`)
Dates in DD-MM-YYYY format:

```yh
date birthDate := 15-03-1990;
date offenseDate := 01-01-2024;
date courtDate := 15-12-2024;
```

#### Duration (`duration`)
Time periods with day/month/year suffixes:

```yh
duration sentence := 5 years;
duration probation := 2 years 6 months;
duration remand := 30 days;
```

## Custom Types

### Struct Types

Define custom types using structs:

```yh
struct Person {
    string name,
    int age,
    bool isMinor
}

struct Offense {
    string name,
    money penalty,
    int maxSentence
}
```

### Using Custom Types

```yh
Person defendant := {
    name := "Alice",
    age := 25,
    isMinor := FALSE
};

Offense theft := {
    name := "theft",
    penalty := $1000.00,
    maxSentence := 7
};
```

## Union Types

Use `||` to specify multiple possible types:

```yh
// Variable that could be money or pass (null)
pass || money optionalFine := pass;

// Variable that could be string or int
string || int flexibleValue := "hello";

// Complex union type
Person || Offense || pass complexValue := pass;
```

### Union Type Examples

```yh
// Optional penalty
pass || money penalty := pass;

// Later assignment
penalty := $500.00;

// Check if value exists
match penalty {
    case pass := consequence "no penalty";
    case _ := consequence "penalty applied";
}
```

## Type Annotations

### Variable Declarations

```yh
// Explicit type annotation
int age := 25;
string name := "John";
bool isGuilty := TRUE;

// Type inference (when possible)
age := 25;        // Inferred as int
name := "John";   // Inferred as string
isGuilty := TRUE; // Inferred as bool
```

### Function Parameters

```yh
bool func checkAge(int age) {
    match age {
        case 18 := consequence TRUE;
        case _ := consequence FALSE;
    }
}

string func formatName(string firstName, string lastName) {
    := firstName + " " + lastName
}
```

### Return Types

```yh
// Simple return type
int func add(int a, int b) {
    := a + b
}

// Complex return type
Person func createPerson(string name, int age) {
    := {
        name := name,
        age := age,
        isMinor := age < 18
    }
}
```

## Type Checking

### Compile-Time Checking

Yuho performs type checking at compile time:

```yh
int x := 42;
string y := "hello";

// This would cause a type error
// int z := x + y;  // Error: cannot add int and string
```

### Type Compatibility

```yh
// Compatible types
int a := 10;
int b := 20;
int sum := a + b;  // OK: both are int

// Incompatible types
int x := 10;
string y := "hello";
// int z := x + y;  // Error: type mismatch
```

## Type Conversions

### Explicit Conversions

```yh
// Convert int to float
int wholeNumber := 42;
float decimalNumber := float(wholeNumber);

// Convert float to int (truncates)
float precise := 3.14159;
int rounded := int(precise);  // Results in 3
```

### Implicit Conversions

```yh
// Percent to float
percent rate := 25%;
float decimalRate := rate;  // Automatically converts to 0.25

// Money to float
money amount := $100.00;
float value := amount;  // Automatically converts to 100.0
```

## Type Safety Features

### No Type Coercion

Yuho prevents automatic type conversions:

```yh
int x := 42;
string y := "42";

// These are different types
// bool same := x == y;  // Error: cannot compare int and string
```

### Null Safety

Use `pass` for nullable types:

```yh
// Nullable money type
pass || money optionalFine := pass;

// Check for null
match optionalFine {
    case pass := consequence "no fine";
    case _ := consequence "fine applied";
}
```

## Legal-Specific Types

### Money Type

The `money` type is designed for legal contexts:

```yh
money fine := $500.00;
money compensation := $10,000.00;
money damages := $1,000,000.00;

// Money arithmetic
money total := fine + compensation;
money discounted := total * 0.9;  // 10% discount
```

### Date Type

The `date` type handles legal dates:

```yh
date offenseDate := 01-01-2024;
date courtDate := 15-12-2024;
date birthDate := 15-03-1990;

// Date arithmetic
duration age := courtDate - birthDate;
duration timeSinceOffense := courtDate - offenseDate;
```

### Duration Type

The `duration` type represents legal time periods:

```yh
duration sentence := 5 years;
duration probation := 2 years 6 months;
duration remand := 30 days;

// Duration arithmetic
duration totalTime := sentence + probation;
```

## Type Patterns

### Pattern 1: Legal Entity

```yh
struct LegalEntity {
    string name,
    string type,  // "person", "corporation", "government"
    bool isMinor,
    date dateOfBirth
}
```

### Pattern 2: Offense Definition

```yh
struct Offense {
    string name,
    string section,
    money maxFine,
    int maxSentence,
    bool isIndictable
}
```

### Pattern 3: Case Facts

```yh
struct CaseFacts {
    string caseNumber,
    date offenseDate,
    string location,
    bool isGuilty,
    money penalty
}
```

## Type Validation

### Compile-Time Validation

```yh
// Valid types
int age := 25;
string name := "John";
bool isGuilty := TRUE;

// Invalid types (would cause errors)
// int invalid := "hello";  // Error: string cannot be int
// bool invalid := 42;      // Error: int cannot be bool
```

### Runtime Type Checking

```yh
// Use match-case for type checking
match value {
    case int _ := consequence "it's an integer";
    case string _ := consequence "it's a string";
    case bool _ := consequence "it's a boolean";
    case _ := consequence "unknown type";
}
```

## Best Practices

### 1. Use Appropriate Types

```yh
// Good: Use money for currency
money fine := $500.00;

// Avoid: Use float for currency
float fine := 500.00;  // Less clear, no currency context
```

### 2. Use Union Types for Optional Values

```yh
// Good: Optional fine
pass || money optionalFine := pass;

// Avoid: Always required
money fine := $0.00;  // Unclear if 0 means "no fine" or "fine is 0"
```

### 3. Use Descriptive Type Names

```yh
// Good: Clear legal context
struct CriminalOffense {
    string name,
    money penalty,
    int maxSentence
}

// Avoid: Generic names
struct Thing {
    string a,
    money b,
    int c
}
```

### 4. Use Type Annotations for Clarity

```yh
// Good: Clear return type
bool func isGuilty(Offense offense) {
    // function body
}

// Avoid: Unclear return type
func check(Offense offense) {
    // function body
}
```

## Common Type Errors

### Error 1: Type Mismatch

```yh
int x := 42;
string y := "hello";
// int z := x + y;  // Error: cannot add int and string
```

**Solution**: Use explicit conversion or match types:

```yh
int x := 42;
string y := "hello";
string z := string(x) + y;  // Convert int to string first
```

### Error 2: Null Access

```yh
pass || money optionalFine := pass;
// money amount := optionalFine;  // Error: optionalFine might be pass
```

**Solution**: Use match-case to handle null:

```yh
pass || money optionalFine := pass;
match optionalFine {
    case pass := consequence "no fine";
    case _ := consequence "fine exists";
}
```

### Error 3: Type Inference Failure

```yh
// This might not infer the correct type
value := 42;  // Could be int or float
```

**Solution**: Use explicit type annotation:

```yh
int value := 42;  // Explicitly int
float value := 42.0;  // Explicitly float
```

## Type System Benefits

### 1. Compile-Time Safety

- Catches type errors before runtime
- Prevents common programming mistakes
- Ensures type consistency

### 2. Legal Context

- Types designed for legal concepts
- Money type for currency
- Date type for legal dates
- Duration type for sentences

### 3. Immutability

- All values are immutable
- Prevents accidental modifications
- Ensures data integrity

### 4. Pattern Matching

- Type-safe pattern matching
- Exhaustive case coverage
- Clear error handling

## Next Steps

- [Syntax Reference](syntax.md) - Complete syntax guide
- [Structs](structs.md) - Working with data structures
- [Match-Case](match-case.md) - Pattern matching patterns
- [Functions](functions.md) - Function definitions and usage
