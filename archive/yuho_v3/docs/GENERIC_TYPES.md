# Generic Types in Yuho

## Overview

Yuho supports parametric polymorphism through generic types, enabling code reuse and type-safe containers.

## Generic Structs

Define structs with type parameters:

```yuho
struct Container<T> {
    T value,
    string label,
}

struct Pair<A, B> {
    A first,
    B second,
}

struct Result<T, E> {
    bool is_success,
    T value,
    E error_message,
}
```

### Type Parameters

- Type parameters use uppercase identifiers: `T`, `U`, `A`, `B`, etc.
- Multiple type parameters are comma-separated
- Type parameters can be used in field types

## Generic Functions

Define functions with type parameters:

```yuho
pass func identity<T>(T value) {
    // Returns the value unchanged
    pass
}

int func length<T>(Array<T> items) {
    // Returns array length
    pass
}
```

### Function Type Parameters

- Declared between function name and parameter list: `func<T, U>`
- Can be used in parameter types and return type
- Enables polymorphic function behavior

## Type Constraints

Generic types work with Yuho's dependent types:

```yuho
struct ValidatedContainer<T> {
    T value,
    BoundedInt<0, 100> confidence,
}

struct MoneyPair<C> {
    money<C> first,
    money<C> second,
}
```

## Transpilation

### TypeScript

Generic structs transpile to TypeScript interfaces:

```typescript
export interface Container<T> {
  value: T;
  label: string;
}

export interface Pair<A, B> {
  first: A;
  second: B;
}
```

### JSON

Generic type information is preserved:

```json
{
  "kind": "struct",
  "name": "Container",
  "type_params": ["T"],
  "fields": [
    {
      "name": "value",
      "type": {"type_variable": "T"}
    }
  ]
}
```

## Type Checking

The type checker validates:

- Type parameter scope (must be declared)
- Arity matching (correct number of type arguments)
- Type variable usage within declared parameters

```yuho
// ✓ Valid: T is declared in type_params
struct Box<T> {
    T value,
}

// ✗ Invalid: U is not declared
struct Box<T> {
    U value,  // Error: Unbound type variable 'U'
}

// ✗ Invalid: Wrong number of type arguments
Container<int, string>  // Error: Container expects 1 type parameter, got 2
```

## Best Practices

1. **Use meaningful type parameter names**
   - Single letters for simple cases: `T`, `U`, `V`
   - Descriptive names for complex cases: `TValue`, `TError`

2. **Keep type parameters minimal**
   - Only use as many as needed
   - Prefer concrete types when possible

3. **Document type parameter constraints**
   - Use comments to explain expected types
   - Specify any semantic requirements

## Examples

### Option/Maybe Type

```yuho
struct Option<T> {
    bool has_value,
    T value,
}
```

### Generic Pair for Different Types

```yuho
struct KeyValue<K, V> {
    K key,
    V value,
}
```

### Validated Generic Container

```yuho
struct Validated<T> {
    T data,
    bool is_valid,
    string validation_message,
}
```

## Future Enhancements

Planned improvements to the generic type system:

1. **Type constraints**: `T where T: Numeric`
2. **Higher-kinded types**: `Container<Container<T>>`
3. **Generic enums**: `enum Option<T> { Some(T), None }`
4. **Type inference**: Automatic type parameter deduction
5. **Generic methods**: Methods on generic structs

## See Also

- [Type System Documentation](https://github.com/gongahkia/yuho-2/wiki/Type-System)
- [Dependent Types](https://github.com/gongahkia/yuho-2/wiki/Dependent-Types)
- [Structs](https://github.com/gongahkia/yuho-2/wiki/Structs)
