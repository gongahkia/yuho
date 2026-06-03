# Euclid Syntax Reference

This document describes the syntax and runtime behavior implemented by the current Haskell codebase. It does not describe planned or aspirational features.

For examples, see [`examples/`](../examples/).

## Lexical Rules

### Comments

```euclid
// line comment

/* block
   comment */
```

### Identifiers

Identifiers start with a letter or underscore, followed by letters, digits, or underscores.

```euclid
main
timeline_1
_private
warPhase2
```

### Literals

Supported literals:

- integers
- double-quoted strings
- booleans
- ISO dates in `YYYY-MM-DD` form

```euclid
42
"hello"
true
1945-05-08
```

Not currently supported:

- floating-point literals
- fuzzy dates such as `~1945-05-08`
- relative temporal phrases such as `5years after x`
- era references such as `main::era::start`

## Top-Level Statements

A Euclid file is a sequence of statements. The current parser accepts these top-level forms:

- `type`
- `timeline`
- `entity`
- `rel`
- `import`
- `let`
- `fn`
- `if`
- `match`
- `for`
- `repeat`
- `while`
- assignment statements
- expression statements
- `return` inside function bodies

`rel` and `import` require trailing semicolons. `let`, assignment, expression, and `return` statements accept an optional trailing semicolon.

## Timelines

Timelines define named temporal spans.

```euclid
timeline main {
    kind: linear,
    start: 1939-09-01,
    end: 1945-09-02,
}
```

Supported fields:

| Field | Type | Notes |
|---|---|---|
| `kind` | identifier | `linear`, `branch`, `parallel`, or `loop` |
| `start` | expr | date or integer at runtime |
| `end` | expr | date or integer at runtime |
| `parent` | identifier | validated after evaluation |
| `fork_from` | `timeline @ expr` | validated after evaluation |
| `merge_into` | `timeline @ expr` | validated after evaluation |
| `loop_count` | expr | must evaluate to an integer if present |

Defaults:

- omitted `kind` defaults to `linear`
- omitted `start` defaults to `0`
- omitted `end` defaults to `100`

Examples:

```euclid
timeline main {
    start: 1,
    end: 10,
}

timeline alternate {
    kind: branch,
    start: 3,
    end: 8,
    fork_from: main @ 3,
    merge_into: main @ 7,
}
```

Semantic rules:

- invalid explicit `kind` values are errors
- timeline bounds with `start > end` are errors
- missing `parent`, `fork_from`, and `merge_into` timeline references are errors

## Entities

Entities belong to zero or more timelines through `appears_on`.

```euclid
entity churchill : leader {
    nation: "United Kingdom",
    appears_on: main @ 1939-09-03..1945-05-08,
}
```

General form:

```text
entity <name> : <type>? {
    <field>: <expr>,
    appears_on: <timeline> @ <start>..<end>,
}
```

Notes:

- the type annotation is optional; omitted types become `entity`
- `appears_on` may appear multiple times
- non-`appears_on` fields are stored as evaluated values

Built-in entity type labels:

- `entity`
- `event`
- `person`
- `place`
- `object`
- `group`
- `character`
- `artifact`
- `location`
- `faction`
- `evidence`
- `witness`
- `claim`
- `fact`
- `exhibit`
- `deposition`

Built-in legal/litigation entity schemas:

| Type | Required fields | Optional fields | Intended use |
|---|---|---|---|
| `evidence` | `citation: string`, `source: string` | `bates: string`, `admissibility: string` | Source-backed support for a claim or fact |
| `witness` | none | `affiliation: string`, `credibility: int` | Person or source whose statements matter to the narrative |
| `claim` | none | user-defined fields | Contested assertion |
| `fact` | none | user-defined fields | Uncontested assertion or procedural fact |
| `exhibit` | `number: string`, `description: string` | user-defined fields | Filing-style exhibit record |
| `deposition` | `deponent: string`, `date: date` | user-defined fields | Deposition event or transcript record |

`source` is also an entity annotation field. For `evidence`, `source: "..."` satisfies the built-in `source` field requirement.

Legal type examples:

```euclid
timeline case_file {
    start: 2024-01-01,
    end: 2024-12-31,
}

entity email_record : evidence {
    citation: "Ex. 12",
    source: "Discovery production",
    bates: "ACME_000012",
    admissibility: "business record",
    appears_on: case_file @ 2024-03-04..2024-03-04,
}

entity jane_smith : witness {
    name: "Jane Smith",
    affiliation: "Acme Corp",
    credibility: 80,
    appears_on: case_file @ 2024-04-01..2024-04-01,
}

entity notice_was_sent : claim {
    position: "Notice was sent before the deadline.",
    appears_on: case_file @ 2024-03-04..2024-03-04,
}

entity contract_signed : fact {
    summary: "The contract was signed.",
    appears_on: case_file @ 2024-01-15..2024-01-15,
}

entity exhibit_12 : exhibit {
    number: "Ex. 12",
    description: "Email notice record",
    appears_on: case_file @ 2024-03-04..2024-03-04,
}

entity jane_deposition : deposition {
    deponent: "Jane Smith",
    date: 2024-04-01,
    appears_on: case_file @ 2024-04-01..2024-04-01,
}

rel email_record -["cites"]-> notice_was_sent;
```

Semantic rules:

- references to missing timelines are errors
- appearance ranges with `start > end` are errors
- appearances outside timeline bounds are errors
- unknown custom entity types are warnings, not errors
- `claim` entities with no inbound `cites` relationship are warnings
- `witness` entities with no matching `deposition` are warnings; `deposition.deponent` matches the witness entity id or string `name` field
- entities marked `continuous: true` warn when their `appears_on` ranges have gaps on the same timeline

## Relationships

Relationships are directed in the current parser.

Supported arrow forms:

- labeled: `-["label"]->`
- unlabeled: `-->`

Examples:

```euclid
rel churchill -["allied_with"]-> roosevelt;
rel cause --> effect;
rel traveler -["meets"]-> guide @ 2001-01-01..2001-01-31;
```

Semantic rules:

- relationship source and target entities must exist
- temporal scopes with `start > end` are errors
- built-in legal relationship labels add direction warnings when their endpoint types or temporal order are malformed
- `contradicts` edges warn when source and target appear on the same timeline

Not currently supported:

- undirected arrows such as `--` or `-["label"]-`

Built-in legal relationship labels:

| Label | Validator semantics |
| --- | --- |
| `contradicts` | Recognized as an explicit contradiction edge. No automatic truth inference is performed. |
| `corroborates` | Recognized as an explicit support edge. No automatic truth inference is performed. |
| `supersedes` | Source should appear after the target it replaces. |
| `caused` | Source should appear before the target result. |
| `enabled` | Source should appear before the target it made possible. |
| `preceded` | Source should appear before the target. |
| `cites` | Source should be `evidence`; target should be `claim` or `fact`. |
| `impeaches` | Source should be `evidence`; target should be `witness`. |

The causal keyword forms `source causes target;` and `source enables target;` keep their existing temporal-order warnings. Custom labels remain allowed.

Legal examples:

```euclid
timeline case_file {
    start: 2024-03-01,
    end: 2024-03-31,
}

entity record : evidence {
    citation: "Record A",
    source: "Archive",
    appears_on: case_file @ 2024-03-01..2024-03-01,
}

entity disputed_claim : claim {
    appears_on: case_file @ 2024-03-02..2024-03-02,
}

entity hearing_fact : fact {
    appears_on: case_file @ 2024-03-04..2024-03-04,
}

entity witness_jane : witness {
    appears_on: case_file @ 2024-03-05..2024-03-05,
}

entity witness_jane_deposition : deposition {
    deponent: "witness_jane",
    date: 2024-03-06,
    appears_on: case_file @ 2024-03-06..2024-03-06,
}

rel record -["cites"]-> disputed_claim;
rel record -["cites"]-> hearing_fact;
rel record -["impeaches"]-> witness_jane;
rel hearing_fact -["corroborates"]-> disputed_claim;
```

## Custom Types

Custom types declare reusable entity field schemas and optional metadata.

```euclid
type leader {
    nation: string,
    rank: string,
    @icon: "crown",
}
```

Inheritance is supported:

```euclid
type battle : event {
    theater: string,
}
```

Field syntax:

```text
field_name: type_name,
optional_field: type_name?,
@meta_name: <expr>,
```

Supported scalar/runtime type names in validation:

- `int`
- `string`
- `bool`
- `date`
- `list`
- `entity`
- `timeline`
- `closure`

Declared custom types may also be used as field types for entity references.

Semantic rules:

- inherited fields are included when validating entities
- non-optional declared fields are required
- declared field values are checked against their declared types
- type metadata is available through entity field access fallback

## Variables And Assignment

`let` supports optional `mut` and optional type annotations.

```euclid
let answer = 42;
let mut counter = 0;
let name: string = "Frodo";
counter = counter + 1;
```

Semantic rules:

- unresolved identifiers are errors
- assignment to an undefined name is an error
- assignment to a non-`mut` binding is an error
- type annotations on `let` bindings are enforced at evaluation time

## Functions And Closures

Functions use typed parameters and an optional return type.

```euclid
fn summarize(count: int) -> string {
    if count > 1 {
        return "multiple";
    }
    return "single";
}
```

Closures are expression-bodied:

```euclid
let labeler = |name: string| name;
```

Built-in callable names:

- `len`
- `before`
- `after`
- `type_of`

Current call semantics:

- named functions are callable
- closure values are callable
- other values are not callable
- `return` is only valid inside function bodies

## Control Flow

### Conditionals

```euclid
if false {
    let branch = 0;
} else if true {
    let branch = 1;
} else {
    let branch = 2;
}
```

Conditions must evaluate to booleans.

### Match

Supported match patterns:

- literal values
- identifier bindings
- `_`

```euclid
match status {
    "active" => { let running = true; },
    state => { let seen = state; },
    _ => { let running = false; },
}
```

### For

`for` accepts:

- ranges
- list literals
- general expressions

```euclid
for i in 1..3 {
    let phase = i;
}

for label in ["one", "two"] {
    let current = label;
}
```

If the iterable expression evaluates to a list, the loop iterates that list. Otherwise the current evaluator treats the value as a single-item iteration.

### Repeat

```euclid
repeat 3 {
    let tick = true;
}
```

Repeat counts must evaluate to non-negative integers.

### While

```euclid
let mut counter = 0;

while counter < 3 {
    counter = counter + 1;
}
```

While conditions must evaluate to booleans. The evaluator also enforces a maximum iteration limit.

## Expressions

Supported expression forms:

- literals
- identifiers
- list literals
- ranges
- indexing
- field access
- function and closure calls
- closures
- binary expressions

Operator support:

| Category | Operators |
|---|---|
| arithmetic | `+`, `-` |
| comparison | `>`, `<`, `>=`, `<=`, `==`, `!=` |
| boolean | `&&`, `||` |
| range | `..` |

Precedence, highest to lowest:

1. postfix access and calls
2. `+`, `-`
3. comparisons
4. `&&`
5. `||`
6. `..`

Not currently supported:

- `*`
- `/`
- unary `!`

## Field Access And Indexing

Examples:

```euclid
let first = ["frodo", "sam"][0];
let kind_name = main.kind;
let nation = churchill.nation;
```

Timeline field access supports:

- `name`
- `kind`
- `start`
- `end`
- `parent`
- `loop_count`

Entity field access supports:

- `name`
- `type`
- declared entity fields
- inherited type metadata fallback

## Imports

Imports are string paths:

```euclid
import "shared/common.euclid";
```

The current CLI loader expands imports before parsing.

## Audit-Driven Semantics

The current implementation now enforces these rules explicitly:

- unresolved names fail instead of silently becoming strings
- `let mut` is enforced for reassignment
- explicit invalid timeline kinds fail instead of defaulting
- declared entity type requirements are validated
- diagnostics carry source locations through the parser, evaluator, validation, and LSP layers
