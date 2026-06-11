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
- durations with `year`/`years`, `month`/`months`, and `day`/`days` components

```euclid
42
"hello"
true
1945-05-08
2 years 3 months 10 days
```

Not currently supported:

- floating-point literals
- fuzzy dates such as `~1945-05-08`
- relative temporal phrases such as `5 years after x`
- era references such as `main::era::start`

## Top-Level Statements

A Euclid file is a sequence of statements. The current parser accepts these top-level forms:

- `type`
- `source`
- `source_bundle`
- `locator`
- `ruleset`
- `deadline_rule`
- `issue`
- `element`
- `timeline`
- `entity`
- `reltype`
- `rel`
- `import`
- `constraint`
- `view`
- `scenario`
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
| `jurisdiction` | string or identifier | Legal ruleset/jurisdiction label such as `US-FRCP` or `UK-CPR`. |
| `court` | string or identifier | Court or forum label for reports and exports. |
| `procedure` | string or identifier | Procedure/ruleset label such as `civil-procedure`; a jurisdiction without a procedure warns. |
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

timeline federal_case {
    jurisdiction: "US-FRCP",
    court: "Example U.S. District Court",
    procedure: "civil-procedure",
    start: 2024-01-01,
    end: 2024-12-31,
}
```

Semantic rules:

- invalid explicit `kind` values are errors
- timeline bounds with `start > end` are errors
- missing `parent`, `fork_from`, and `merge_into` timeline references are errors
- timelines with `jurisdiction` but no `procedure`, or `procedure` but no `jurisdiction`, produce warnings

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
- a string `narrative` field can be used by `euclid run --narrative <name>` and `euclid export --narrative <name>`
- annotation fields `note`, `source`, `confidence`, and `tags` are stored separately from ordinary entity fields
- `recurrence` accepts a duration value and `skip` accepts a list of dates

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
- `expert_opinion`
- `deadline`
- `exhibit`
- `deposition`

Built-in legal/litigation entity schemas:

| Type | Required fields | Optional fields | Intended use |
|---|---|---|---|
| `evidence` | `citation: string`, `source: string` | `source_ref: source`, `locator_ref: locator`, `bates: string`, `admissibility: string` | Source-backed support for a claim or fact |
| `witness` | none | `affiliation: string`, `credibility: int` | Person or source whose statements matter to the narrative |
| `claim` | none | user-defined fields | Contested assertion |
| `fact` | none | user-defined fields | Uncontested assertion or procedural fact |
| `expert_opinion` | `opinion: string` | `source_ref: source`, `locator_ref: locator` | Expert conclusion tied to a record source |
| `deadline` | `rule: string`, `jurisdiction: string`, `trigger: string`, `due: date` | `source_ref: source`, `rule_ref: deadline_rule` | Procedural deadline backed by an authority or docket source |
| `exhibit` | `number: string`, `description: string` | `source_ref: source`, `locator_ref: locator` | Filing-style exhibit record |
| `deposition` | `deponent: string`, `date: date` | user-defined fields | Deposition event or transcript record |

`source` is also an entity annotation field. For `evidence`, `source: "..."` satisfies the built-in string source field requirement. Use `source_ref: <source_id>` when the evidence should point at a first-class source declaration.

## Sources

Sources are first-class provenance records. They are addressable by identifier and can be stored in entity fields typed as `source`.

```euclid
source brown_opinion : legal_case {
    title: "Brown v. Board of Education",
    citation: "347 U.S. 483",
    url: "https://www.archives.gov/milestone-documents/brown-v-board-of-education",
    retrieved: 2026-06-11,
}

entity opinion_record : evidence {
    citation: "347 U.S. 483",
    source: "National Archives",
    source_ref: brown_opinion,
    appears_on: case_file @ 1954-05-17..1954-05-17,
}
```

Source field access supports `name`, `kind`, and declared source fields such as `url` or `citation`. Validation warns when a source lacks all of `citation`, `title`, and `url`, and warns when a declared `url` is not an HTTP(S) URL.

Validation also normalizes `citation` and `canonical_id` fields by lowercasing text and removing punctuation for duplicate checks. This catches sources such as `24-cv-100` and `24 CV 100` as the same source identity without preventing the file from evaluating.

Source bundles group related source records for a pleading, docket packet, transcript set, or authority bundle:

```euclid
source_bundle pleadings {
    sources: [brown_opinion],
    jurisdiction: "US-FRCP",
    court: "Example U.S. District Court",
}
```

`sources` entries must point to declared `source` records. Missing source references are errors, and repeated bundle members are warnings.

Source locators are first-class pins into a source. They keep the citation identity separate from the exact place used by an entity, issue, or deadline rule:

```euclid
locator complaint_para_12 {
    source_ref: complaint,
    bates: "ACME_000012",
    page: 4,
    paragraph: "12",
}
```

`source_ref` is required and must point to a declared source. Validation warns when a locator has no concrete locator field such as `bates`, `page`, `paragraph`, `line`, `transcript_page`, `transcript_line`, `docket_entry`, or `url_fragment`.

## Rulesets And Deadline Rules

Jurisdiction coverage is modeled through source-backed rulesets and deadline-rule declarations. These declarations are inspectable authority records; they do not compute a docketing answer.

```euclid
ruleset us_frcp {
    jurisdiction: "US-FRCP",
    court: "U.S. district courts",
    procedure: "civil-procedure",
    effective: 2024-12-01..2026-12-31,
    source_ref: frcp_2024,
}

deadline_rule us_frcp_answer_21 {
    ruleset: us_frcp,
    rule: "FRCP 12(a)(1)(A)(i)",
    trigger: "service of summons and complaint",
    actor: "defendant",
    action: "serve an answer",
    offset: days(21),
    direction: after,
    counting: calendar_days_with_last_day_rollover,
    source_ref: frcp_2024,
}
```

Ruleset fields:

| Field | Type | Notes |
|---|---|---|
| `jurisdiction` | string or identifier | Coverage label such as `US-FRCP`, `UK-CPR`, `SG-ROC-2021`, `EU-2020-1784`, `CA-CIVIL`, or `NY-CPLR`. |
| `court` | string or identifier | Court/forum scope. |
| `procedure` | string or identifier | Rules/procedure family. |
| `effective` | range | Effective-date range for this encoded pack. |
| `source_ref` | source | Required by validation for legal authority traceability. |

Deadline-rule fields:

| Field | Type | Notes |
|---|---|---|
| `ruleset` | ruleset | Required. |
| `rule` | string or identifier | Human-readable rule citation. |
| `trigger` | string or identifier | Event that starts the clock. |
| `actor` | string or identifier | Optional responsible actor. |
| `action` | string or identifier | Optional required act. |
| `offset` | duration | Required positive duration, usually `days(n)`, `months(n)`, or `years(n)`. |
| `direction` | identifier | `after` or `before`; defaults to `after`. |
| `counting` | identifier | `calendar_days`, `calendar_days_with_last_day_rollover`, `clear_days`, `business_days`, or `court_days`; defaults to `calendar_days_with_last_day_rollover`. |
| `source_ref` | source | Required by validation. |

Use `rule_ref` on a `deadline` entity when a concrete case date is tied to a declared authority:

```euclid
entity answer_due : deadline {
    rule: "FRCP 12(a)(1)(A)(i)",
    jurisdiction: "US-FRCP",
    trigger: "service of summons and complaint",
    due: 2026-02-02,
    source_ref: frcp_2024,
    rule_ref: us_frcp_answer_21,
    appears_on: case_file @ 2026-02-02..2026-02-02,
}
```

`euclid deadlines <file>` lists rulesets, deadline rules, and concrete `deadline` entities.

## Issues And Elements

Issue maps separate legal questions from timeline events:

```euclid
issue service_response_deadlines {
    title: "Service-response deadline coverage",
    question: "Which sourced rule controls the first response deadline?",
    burden: "user-selected jurisdiction pack",
    standard: "source-backed chronology",
    source_ref: frcp_2024,
}

element response_trigger_identified {
    issue: service_response_deadlines,
    text: "The triggering event must be identified before selecting a deadline rule.",
    burden: "drafter",
    source_ref: frcp_2024,
}
```

`element.issue` must point to a declared `issue`; `source_ref` fields must point to declared sources. `euclid issues <file>` renders the issue map, and `euclid review <file>` combines issues with diagnostics, source audits, deadline rules, and scenario reports for human review of a legal draft.

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

Declared relationship types add validator semantics for custom labels:

```euclid
reltype cites {
    source: evidence,
    target: claim | fact,
    temporal: source_before_target,
    required: true,
}
```

Supported `reltype` fields:

| Field | Type | Notes |
| --- | --- | --- |
| `source` | type list | Allowed source entity types separated by `|`; omitted means any source type. |
| `target` | type list | Allowed target entity types separated by `|`; omitted means any target type. |
| `temporal` | identifier | `source_before_target`, `before`, `source_after_target`, `after`, or `none`. |
| `required` | bool | If `true`, each matching target entity must have an inbound relationship with that label. |
| `min_inbound` | int | Minimum number of inbound relationships required for each matching target entity. |
| `max_inbound` | int | Maximum number of inbound relationships allowed for each matching target entity. |
| `min_outbound` | int | Minimum number of outbound relationships required for each matching source entity. |
| `max_outbound` | int | Maximum number of outbound relationships allowed for each matching source entity. |

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
- declared and built-in legal relationship labels add direction warnings when their endpoint types or temporal order are malformed
- declared `required: true` relationship types are equivalent to `min_inbound: 1` for matching target entities
- declared cardinality bounds produce errors when matching source/target entities have too few or too many legal support edges
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
- `duration`
- `list`
- `range`
- `entity`
- `timeline`
- `source`
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
- type annotations on `let` bindings are checked statically when possible and enforced at evaluation time

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
- `abs`
- `min`
- `max`
- `clamp`
- `contains`
- `starts_with`
- `ends_with`
- `to_upper`
- `to_lower`
- `trim`
- `split`
- `replace`
- `substring`
- `to_string`
- `head`
- `tail`
- `last`
- `reverse`
- `flatten`
- `range`
- `sort`
- `unique`
- `years`
- `months`
- `days`
- `duration_days`
- `duration_months`
- `duration_years`
- `overlaps`
- `overlapped_by`
- `during`
- `contains_range`
- `meets`
- `met_by`
- `starts`
- `started_by`
- `finishes`
- `finished_by`
- `equals`
- `midpoint`
- `duration_between`
- `alive_at`
- `active_on`
- `entities_where`
- `causes_of`
- `effects_of`
- `related_to`
- `inbound`
- `outbound`
- `has_inbound`
- `has_outbound`

Current call semantics:

- named functions are callable
- closure values are callable
- other values are not callable
- `return` is only valid inside function bodies
- known builtins report arity/type errors instead of falling through as undefined functions

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

If the iterable expression evaluates to a list, the loop iterates that list. If it evaluates to an ordinal range, the loop iterates each integer point in the range. Date ranges are interval values and are not implicitly expanded into daily loops. Other values are treated as single-item iterations.

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
- quantifiers
- unary expressions
- binary expressions
- temporal field access

Operator support:

| Category | Operators |
|---|---|
| arithmetic | unary `-`, `+`, `-`, `*`, `/`, `%` |
| concatenation | `++` for strings and lists |
| comparison | `>`, `<`, `>=`, `<=`, `==`, `!=` |
| boolean | unary `!`, `&&`, `||` |
| range | `..` |

Precedence, highest to lowest:

1. postfix access and calls
2. unary `-`, `!`
3. `*`, `/`, `%`
4. `+`, `-`, `++`
5. comparisons
6. `&&`
7. `||`
8. `..`

Range expressions such as `1..3` and `2024-01-01..2024-01-31` evaluate to first-class `range` values. Ordinal ranges can be iterated by `for`; date ranges remain interval values and are intended for interval predicates such as `contains`, `overlaps`, `during`, `starts`, `finishes`, and `equals`.

Quantifiers evaluate a boolean expression over an iterable:

```euclid
constraint "claims are cited" {
    forall c in entities_where("claim") {
        has_inbound(c, "cites")
    };

    exists e in inbound(central_claim, "cites") {
        type_of(e) == "evidence"
    };
}
```

`forall` over an empty iterable evaluates to `true`; `exists` over an empty iterable evaluates to `false`. Quantifier bodies must evaluate to booleans.

Duration arithmetic supports date-plus-duration, date-minus-duration, date-minus-date, and duration-plus/minus-duration. Division and modulo by zero are evaluator errors.

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
- `note`
- `source`
- `confidence`
- `tags`
- declared entity fields
- inherited type metadata fallback

Temporal entity field access uses `entity.field @ time` and returns the field value active at that time, considering `state` changes when present.

Source field access supports `name`, `kind`, and declared source fields. Range field access supports `start`, `end`, and `duration`.

Timeline field access supports `jurisdiction`, `court`, and `procedure` in addition to `name`, `kind`, `start`, `end`, `parent`, and `loop_count`.

## Views, Scenarios, And Constraints

The parser and evaluator accept lightweight view, scenario, and constraint declarations:

```euclid
view "case focus" {
    timelines: [case_file],
    filter: claim,
    time_range: 1..10,
    highlight: [central_claim],
}

scenario "what if" from case_file {
    entity alternate_fact : fact {
        appears_on: case_file @ 2..2,
    }
}

constraint "sanity check" {
    let ok = true;
    ok;
}
```

Views are stored in the evaluated world. Scenarios evaluate their body against the current world and store the resulting alternate world. `scenario "..." from <timeline>` records the fork anchor and fails evaluation if the referenced timeline does not exist.

Constraints evaluate their body against the current world and are recorded as named constraints when they pass. Expression statements inside a constraint are assertions: they must evaluate to `true`. A `false` expression fails evaluation, and a non-boolean expression is a type error. Helper bindings and functions declared inside a constraint are local to that constraint body and do not leak into the surrounding file.

## Imports

Imports are string paths:

```euclid
import "shared/common.euclid";
```

The shared loader parses imported files as Euclid programs, expands nested imports, preserves source spans from imported files, and reports import cycles as loader diagnostics.

## Audit-Driven Semantics

The current implementation now enforces these rules explicitly:

- unresolved names fail instead of silently becoming strings
- `let mut` is enforced for reassignment
- explicit invalid timeline kinds fail instead of defaulting
- known builtin calls are statically checked where argument types are known
- declared entity type requirements are validated
- declared source records and source-typed fields are validated
- source bundles and normalized source identities are validated
- declared relationship types can enforce endpoint types, temporal order, and inbound/outbound legal support cardinality
- jurisdiction-tagged deadline entities warn when they appear on timelines with a different jurisdiction
- diagnostics carry source locations through the parser, evaluator, validation, and LSP layers
