# Type Aliases in Yuho

## Overview

Type aliases provide semantic naming for types, improving code readability and maintainability.

## Syntax

```yuho
type AliasName := TargetType
```

## Simple Type Aliases

Create aliases for primitive types:

```yuho
type UserId := int
type Email := string
type Timestamp := date
```

## Type Aliases with Dependent Types

Alias complex dependent types:

```yuho
type Age := BoundedInt<0, 150>
type Percentage := BoundedInt<0, 100>
type PositiveAmount := Positive<money<SGD>>
type PersonID := BoundedInt<1, 999999>
```

## Using Type Aliases

Type aliases can be used anywhere a type is expected:

```yuho
struct User {
    UserId id,
    Email email,
    string name,
    Age age,
}

struct Transaction {
    PersonID person_id,
    PositiveAmount amount,
    Timestamp created_at,
}
```

## Generic Type Aliases

Type aliases support type parameters:

```yuho
type Result<T> := T | string

// NOTE: Full generic type alias support is planned for future releases
```

## Transpilation

### TypeScript

Type aliases transpile to TypeScript type declarations:

```typescript
export type UserId = number;
export type Email = string;
export type Age = number;

export interface User {
  id: UserId;
  email: Email;
  name: string;
  age: Age;
}
```

### JSON

Type alias information is preserved in JSON output:

```json
{
  "kind": "type_alias",
  "name": "UserId",
  "type_params": [],
  "target": "Int"
}
```

## Benefits

1. **Semantic Clarity**: Names convey meaning
   - `PersonID` is clearer than `BoundedInt<1, 999999>`
   - `Email` is clearer than `string`

2. **Centralized Changes**: Update type definition in one place
   ```yuho
   type UserId := int  // Change to BoundedInt later if needed
   ```

3. **Domain Modeling**: Express business concepts
   ```yuho
   type Currency := money<SGD> | money<USD> | money<EUR>
   type Status := string  // Could be enum later
   ```

4. **Documentation**: Self-documenting code
   ```yuho
   type Age := BoundedInt<0, 150>  // Clearly represents human age
   ```

## Best Practices

1. **Use meaningful names** that reflect the domain concept
2. **Prefer type aliases** over repeating complex types
3. **Document constraints** with comments when not obvious
4. **Keep aliases focused** on single concepts

## Examples

### Legal Domain

```yuho
type CaseNumber := BoundedInt<1, 999999>
type ContractValue := Positive<money<SGD>>
type LegalDate := date

struct LegalCase {
    CaseNumber id,
    string description,
    LegalDate filed_date,
}
```

### Financial Domain

```yuho
type AccountNumber := BoundedInt<100000, 999999>
type Balance := money<SGD>
type TransactionID := string

struct BankAccount {
    AccountNumber account,
    Balance balance,
    date opened,
}
```

## See Also

- [Type System](https://github.com/gongahkia/yuho-2/wiki/Type-System)
- [Dependent Types](https://github.com/gongahkia/yuho-2/wiki/Dependent-Types)
- [Generic Types](./GENERIC_TYPES.md)
