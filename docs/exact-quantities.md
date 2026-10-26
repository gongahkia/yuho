# Exact quantities (experimental)

The opt-in `yuho.quantitative/v0.1-experimental` source layer derives exact
quantities above the existing typed-finite evaluator. Calculations are technical
results from selected inputs, not independent facts or legal conclusions.

```yuho
typed-rules-model Total {
  quantitative version "yuho.quantitative/v0.1-experimental";
  scalar v:first type money SGD;
  scalar v:second type money SGD;
  scalar v:threshold type money SGD;
  derive v:subtotal type money SGD =
    sum(item first value ref(v:first), item second value ref(v:second));
  derive v:total type money SGD = scale(3,ref(v:subtotal));
  requirement q:threshold = compare(v:total,gte,v:threshold);
  proposition p:threshold;
  rule r:threshold establishes proposition p:threshold when q:threshold;
  limitation "Fictional exact calculation; no sentence determination";
}
```

```yuho
typed-rules-scenario Boundary for Total {
  value v:first = money SGD 125 reason "first supplied amount";
  value v:second = money SGD 275 reason "second supplied amount";
  value v:threshold = money SGD 1200 reason "authored comparison boundary";
}
```

Run `yuho check model.yh --scenario scenario.yh` for a checked plan without
arithmetic evaluation; `yuho run model.yh --scenario scenario.yh` reports exact
intermediate values and the authoritative typed backend result. `yuho diagram`
supports rule/modules/trace JSON, XML and SVG views. Parsed inspection retains
the expression AST. Checked/lowered inspection and frozen kernel-only `compile`
refuse quantitative source because those records omit calculation authority;
use the checked-project workflow for complete exports and immutable replay.

## Types and expressions

* `integer`: signed, dimensionless exact integers.
* `money SGD` (or another uppercase three-letter currency): nonnegative integer
  minor units. Every operand must have the same currency.
* `count occasions`: nonnegative integers with an explicit nominal count domain.
  Different domains and dimensionless integers are incompatible.
* Dates and enums retain their supplied comparison/filter semantics. They have
  no arithmetic interpretation.

Expressions are `ref(v:name)`, `integer(N)`, `money(SGD,N)`,
`count-value(occasions,N)`, `scale(N,EXPR)`,
`sum(item ID value EXPR [when REQUIREMENT], ...)`, and
`count(item ID when REQUIREMENT, ...)`. Item identities must be unique within
an aggregate. Empty sums/counts are zero of their declared type. Scaling uses
an explicit dimensionless integer constant; money/count factors cannot be
negative. Signed integer adjustments can use a sum with negative supplied or
constant integers. Subtraction syntax, division, fractional quantities,
physical measurements, unit conversions and exchange rates are unsupported.

Inclusion conditions name existing typed requirements. The existing evaluator
produces their T/F/U values and actual read records. False excludes a member;
true includes it; unresolved inclusion makes the aggregate unresolved, even
when the member value is zero. Included unknown values propagate their original
reasons. False inclusion can exclude an explicitly unknown amount, but every
required supplied input must still be present and well typed. Missing is an
error, never zero or an invented unresolved assessment. A zero factor does not
erase an unresolved operand. Operands and inclusion reads are retained even
when a member does not contribute to the numeric sum.

## Checking and bounds

Derived outputs have one writer and cannot receive scenario values. References
may point forward; lexical topological ordering determines evaluation, including
scalar dependencies reached through inclusion requirements. Self-reference and
cycles spanning calculations and filters reject before evaluation. Every
arithmetic operand and comparison must have exactly compatible types/domains.

Per component: at most 64 derived outputs, 256 identified members per aggregate,
depth 16, 2,048 AST nodes and 16,384 expanded quantitative/filter read work.
Supplied numeric values, literals, factors and every AST result have magnitude
less than 2^4096. Money/count values are nonnegative. Literal parsing is bounded
before conversion. A sum may use an internal accumulator of up to 4,104 bits;
a product may use up to 8,192 bits before its result bound is checked. These
finite workspaces permit exact cancellation without truncation. Reasons are
nonblank and at most 4,096 characters. Existing source/plan bounds also apply.
Complete export is limited to 32 MiB, and its saved artifact to the decoder's
8 MiB limit. Oversized results fail before publication.

## Shared source and scoped execution

Exact-version modules can export scalar inputs and derivations. Explicitly
select each original scalar input and each original requirement used by an
imported calculation/filter. A same-named host scalar or requirement is not a
substitute for the selected module declaration. The checker retains original
file/token/snapshot ownership and refuses such substitution.

A checked project can select the same authored quantitative body into separate
components/scenarios or selected typed allegations. The body retains one
qualified authored identity; each scoped use, input selection and evaluation
remains distinct. Ordinary requirements can combine scoped-definition uses with
comparisons of these values. Scalar parameters or captures inside closed
`requirement-template` bodies are not introduced. Matching names or results do
not share input authority.

## Dependencies, SDK and persistence

The existing typed-expression/proposition observation ports can carry an actual
comparison result to a checked condition slot or candidate guard. They do not
transport an arbitrary scalar. Direct cross-component scalar ports are deferred.
Conflict ancestry follows actual typed scalar/filter reads through the existing
dependency conversion, with no string-key inference.

The public `Yuho.Authoring.Quantitative` module provides typed expression/value
constructors, checked source builders, exact mathematical SDK evaluation and
quantitative execution inspection. Source-backed execution, source recovery,
projection and publication use the public `Yuho.Authoring.Dependency` facade.
The pure SDK helper takes explicit caller filter values; it creates no source
file, legal observation or assessment-authority claim.

Use existing `yuho compose check/run/replay` and machine v0.2
`dependency-yh` / `dependency-artifact-json` operations. New quantitative
sources produce `yuho.dependency-artifact/v0.2-quantitative-experimental` with
the embedded source document and saved complete report. Static artifact check
validates retained source authority, plan, format and report attachment without
re-evaluating numbers. Replay recomputes from embedded sources and compares both
execution digest and complete report. Live changes, including same-result reason
changes, invalidate live attachment; they do not change immutable replay.
Publication retains atomic, no-overwrite behavior.

Old sources, frozen kernel protocols, computed-input v0.1, dependency artifacts
v0.1 and machine versions retain their existing meanings. Quantitative report
records use exact decimal strings; no floating-point conversion occurs.

The focused graphs distinguish supplied values, shared authored expressions,
scoped uses and actual arithmetic steps. Full structured records retain operation
order, values, source sites, input reasons, inclusion reads, scope and snapshots.
A skipped component has a checked plan but no fabricated calculation observation.
The Lean model specifies bounded abstract exact operations and unknown/type
behavior. It does not prove parser, lowering, serialization or projection
refinement. Independent SDK/Lean vectors and source tests provide executable
conformance evidence.
