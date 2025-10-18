# Language Overview

Yuho is a domain-specific language (DSL) designed specifically for representing legal statutes and reasoning patterns.

## Design Philosophy

Yuho is built on several core principles:

1. **Readability**: Legal professionals should be able to read and understand Yuho code
2. **Immutability**: All values are immutable, reflecting the fixed nature of statutes
3. **Type Safety**: Strong typing prevents logical errors
4. **Completeness**: Match-case patterns must cover all cases, mirroring legal completeness

## Language Characteristics

### Strongly, Statically Typed

Every variable has a type known at compile time:

```yh
int x := 42;           // Integer
string s := "hello";    // String
bool b := TRUE;         // Boolean
```

### Functional

- All values are immutable
- Every statement is an expression
- No side effects

### No Loops

Legal statutes don't contain loops, so Yuho doesn't either:

- No `for` loops
- No `while` loops
- No recursion (intentionally limited)

### Pattern Matching

Match-case is the primary control structure:

```yh
match {
    case condition1 := consequence result1;
    case condition2 := consequence result2;
    case _ := consequence defaultResult;
}
```

## Quick Reference

### Comments

```yh
// Single-line comment

/*
Multi-line
comment
*/
```

### Types

- `int` - Integer numbers
- `float` - Floating-point numbers
- `bool` - TRUE or FALSE
- `string` - Text in quotes
- `percent` - Percentage (25%)
- `money` - Currency ($100.50)
- `date` - Dates (DD-MM-YYYY)
- `duration` - Time periods (5 days)

### Structs

```yh
struct StructName {
    type field1,
    type field2
}
```

### Variables

```yh
type variableName := value;
```

### Match-Case

```yh
match {
    case condition := consequence result;
    case _ := consequence default;
}
```

## File Structure

A typical Yuho file (`.yh`) contains:

1. Comments explaining the legal context
2. Struct definitions for legal concepts
3. Variable declarations
4. Match-case logic for conditions

Example:

```yh
// Section 415 - Cheating

struct Cheating {
    string accused,
    bool deception,
    bool harm
}

match {
    case deception && harm := consequence "guilty";
    case _ := consequence "not guilty";
}
```

## Naming Conventions

- **Files**: snake_case (e.g., `criminal_law.yh`)
- **Variables**: camelCase (e.g., `isGuilty`)
- **Structs**: PascalCase (e.g., `Cheating`)
- **Functions**: camelCase (e.g., `checkValidity`)

## Next Steps

- [Detailed Syntax Reference](syntax.md)
- [Type System](types.md)
- [Structs](structs.md)
- [Match-Case Patterns](match-case.md)

For the complete original syntax specification, see [SYNTAX.md](../../doc/SYNTAX.md) in the repository root.

