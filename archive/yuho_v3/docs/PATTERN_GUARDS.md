# Pattern Matching Guards

## Overview

Guards allow conditional matching in pattern matching expressions, enabling more expressive and precise case discrimination.

## Syntax

```yuho
match value {
    case pattern where condition := consequence
    case _ := default
}
```

## Basic Usage

### Age Categorization

```yuho
string func categorize_age(int age) {
    match age {
        case n where n < 0 := "invalid"
        case n where n < 18 := "minor"
        case n where n >= 18 && n < 65 := "adult"
        case n where n >= 65 := "senior"
        case _ := "unknown"
    }
}
```

### Grade Classification

```yuho
string func classify_grade(int score) {
    match score {
        case s where s >= 90 := "A"
        case s where s >= 80 && s < 90 := "B"
        case s where s >= 70 && s < 80 := "C"
        case s where s >= 60 && s < 70 := "D"
        case s where s < 60 := "F"
        case _ := "invalid"
    }
}
```

## Guard Expressions

Guards are boolean expressions evaluated after pattern matching:

```yuho
match value {
    case n where n > 0 && n < 100 := "in range"
    case n where n == 0 := "zero"
    case _ := "out of range"
}
```

### Complex Guards

Guards can contain any boolean expression:

```yuho
match transaction {
    case t where t.amount > 1000 && t.verified := "high value verified"
    case t where t.amount > 1000 := "high value unverified"
    case t where t.verified := "verified"
    case _ := "standard"
}
```

## Pattern Variable Binding

Pattern variables are available in guard expressions:

```yuho
match person {
    case p where p.age >= 18 && p.has_license := "can drive"
    case p where p.age >= 18 := "adult without license"
    case p where p.age < 18 := "minor"
    case _ := "unknown"
}
```

## Benefits

1. **Precise Conditions**: Express complex matching logic clearly
2. **Reduced Nesting**: Avoid nested if statements in consequences
3. **Pattern + Logic**: Combine structural and logical matching
4. **Exhaustiveness**: Maintain match exhaustiveness with guards

## Comparison with If-Else

### Without Guards (nested ifs)
```yuho
string func categorize(int value) {
    if value < 0 {
        pass := "negative"
    } else {
        if value == 0 {
            pass := "zero"
        } else {
            pass := "positive"
        }
    }
}
```

### With Guards (cleaner)
```yuho
string func categorize(int value) {
    match value {
        case n where n < 0 := "negative"
        case n where n == 0 := "zero"
        case n where n > 0 := "positive"
        case _ := "unknown"
    }
}
```

## Transpilation

### TypeScript

Guards transpile to conditional expressions:

```typescript
function categorize_age(value: number): string {
  if (value < 0) {
    return "invalid";
  } else if (value < 18) {
    return "minor";
  } else if (value >= 18 && value < 65) {
    return "adult";
  } else if (value >= 65) {
    return "senior";
  } else {
    return "unknown";
  }
}
```

### JSON

Guard information is preserved:

```json
{
  "pattern": {"identifier": "n"},
  "guard": {
    "binary": {
      "op": "Lt",
      "left": {"identifier": "n"},
      "right": {"int": 18}
    }
  },
  "consequence": {"string": "minor"}
}
```

## Best Practices

1. **Order Matters**: Place more specific guards before general ones
   ```yuho
   case n where n == 0 := "zero"      // Specific first
   case n where n < 10 := "small"     // Then less specific
   case _ := "other"                   // Finally, catch-all
   ```

2. **Always Include Wildcard**: Ensure exhaustiveness
   ```yuho
   match value {
       case n where n > 0 := "positive"
       case n where n < 0 := "negative"
       case _ := "zero or invalid"  // Don't forget this!
   }
   ```

3. **Keep Guards Simple**: Complex guards reduce readability
   ```yuho
   // Good
   case n where n >= 18 := "adult"
   
   // Consider refactoring if too complex
   case n where n >= 18 && n < 65 && n % 2 == 0 && has_license(n) := "complex"
   ```

4. **Use Pattern Variables**: Bind once, use in guard and consequence
   ```yuho
   case person where person.age >= 18 := format("Adult: {}", person.name)
   ```

## See Also

- [Pattern Matching](https://github.com/gongahkia/yuho-2/wiki/Pattern-Matching)
- [Match Expressions](https://github.com/gongahkia/yuho-2/wiki/Match-Expressions)
- [Type System](https://github.com/gongahkia/yuho-2/wiki/Type-System)
