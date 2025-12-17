# Constraint Inheritance in Yuho

This document explains the **Constraint Inheritance** system in Yuho for modeling legal hierarchies and concept extension.

## Overview

Legal concepts often form hierarchical relationships where specialized offenses inherit properties from general categories. Yuho supports this through struct inheritance with the `extends` keyword.

## Inheritance Syntax

### Basic Inheritance

```yuho
struct DishonestAct {
    bool dishonest_intent,
    bool property_involved,
}

struct Theft extends DishonestAct {
    bool permanent_deprivation,
    bool without_consent,
}
```

The `Theft` struct inherits all fields from `DishonestAct`, plus adds its own fields.

### Field Resolution

When a struct extends another:

1. **Parent fields are inherited** - All fields from the parent become part of the child
2. **Child fields are added** - New fields specific to the child are appended
3. **No name conflicts** - Child fields cannot have the same name as parent fields

## Constraint Propagation

Constraints on parent fields are inherited:

```yuho
struct LegalPerson {
    BoundedInt<18, 150> age where age >= 21,  // Must be adult
}

struct CorporateOfficer extends LegalPerson {
    string company_name,
    date appointment_date,
}
```

The `age >= 21` constraint from `LegalPerson` automatically applies to `CorporateOfficer`.

## Legal Hierarchies

### Criminal Law Hierarchies

```yuho
// Base property offense
struct PropertyOffense {
    bool property_involved,
    Citation<"", "", "Penal Code"> statute,
}

// Dishonest property offenses
struct DishonestPropertyOffense extends PropertyOffense {
    bool dishonest_intent,
}

// Specific offenses
struct Theft extends DishonestPropertyOffense {
    bool permanent_deprivation,
    bool without_consent,
}

struct CriminalBreachOfTrust extends DishonestPropertyOffense {
    bool entrusted_property,
    bool breach_of_fiduciary_duty,
}
```

### Contract Hierarchies

```yuho
struct Contract {
    string parties,
    bool mutual_consent,
    string consideration,
}

struct EmploymentContract extends Contract {
    string employer,
    string employee,
    money<SGD> salary,
}

struct SaleOfGoodsContract extends Contract {
    string seller,
    string buyer,
    string goods,
    money<SGD> price,
}
```

## Type Checking

The semantic checker validates:

1. **Parent exists** - The parent struct must be defined before the child
2. **No circular inheritance** - Structs cannot extend themselves directly or indirectly
3. **Field uniqueness** - Child fields must have unique names
4. **Constraint compatibility** - Inherited constraints must be satisfiable

## Transpilation

### TypeScript

```typescript
interface DishonestAct {
  dishonest_intent: boolean;
  property_involved: boolean;
}

interface Theft extends DishonestAct {
  permanent_deprivation: boolean;
  without_consent: boolean;
}
```

### JSON

```json
{
  "Theft": {
    "extends": "DishonestAct",
    "fields": {
      "permanent_deprivation": "boolean",
      "without_consent": "boolean"
    }
  }
}
```

### English

```
Theft (extends DishonestAct) with:
- permanent_deprivation (boolean)
- without_consent (boolean)
- [inherited] dishonest_intent (boolean)
- [inherited] property_involved (boolean)
```

## Multiple Inheritance

Yuho currently supports single inheritance only. For multiple characteristics, use composition:

```yuho
struct Aggravated {
    bool uses_weapon,
    bool causes_injury,
}

struct AggravatedTheft extends Theft {
    bool uses_weapon,
    bool causes_injury,
}
```

## Best Practices

1. **Model legal taxonomies** - Use inheritance for "is-a" relationships
2. **Shallow hierarchies** - Keep inheritance depth to 2-3 levels max
3. **Document relationships** - Explain why inheritance is used
4. **Constraint inheritance** - Place shared constraints on parent structs
5. **Avoid over-abstraction** - Don't force inheritance where composition fits better

## Related Features

- **Type Aliases** - Name common types without inheritance
- **Generic Types** - Parameterize structs for reusability
- **Constraints** - Add refinement types to fields
- **Legal Citations** - Reference statutes in struct definitions

## Examples

See `examples/inheritance.yh` for comprehensive examples of:
- Criminal law offense hierarchies
- Contract type hierarchies
- Constraint propagation through inheritance
- Field resolution with parent types
