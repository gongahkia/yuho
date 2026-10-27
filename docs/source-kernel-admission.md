# Typed source admission and frozen kernel bounds

Executable typed source checking validates the emitted request with the closed
`TypedFiniteRules-v1` decoder before reporting success. This structural guard
does not evaluate. Native commands retain their documented evaluation-backed
checks; checked-project checks remain non-evaluating.

Authored model, case and allegation identities admit up to 128 characters.
Model and allegation request IDs preserve the historical `ID-request` bytes
when the authored ID has at most 120 characters. Longer IDs use
`~yh-request:` followed by the lowercase SHA-256 hexadecimal digest of the
original UTF-8 identifier. This yields 76 characters. The reserved `~`
namespace cannot occur in authored source identifiers. The full authored
identity remains authoritative in the program or allegation record. Distinct
allegations in a case are checked for generated-ID collisions and refused if
one occurs; identities are never truncated or merged. The low-level SDK
serializer still accepts an explicit caller-chosen request ID, which must pass
the public kernel decoder before execution.

Ground classification reasons must contain 1 through 128 Unicode code points,
matching the kernel's `Text.length` rule. Whitespace is counted and preserved;
UTF-8 bytes are not the length unit. Invalid reasons point to the original
quoted token in the scenario or shared case classification, including through
checked-project source discovery.

The source estimator and kernel admission share `expandedProgramSize`. Its
cost includes entity types, entities, predicates, scalar declarations,
propositions, ground facts, scalar assignments, priority edges, expanded
requirements and grounded rules. References contribute one plus their named
body cost; quantifiers contribute one plus domain cardinality times body cost;
rules contribute one plus parameter cardinality product times body cost.
An explicit source limit may be stricter than the frozen maximum of 2048.
Exactly-at-limit requests are admitted. Cycles refuse without expanding trees.

Existing target bounds also apply to enum members, rule parameter identifiers,
expression nesting and the combined ordinary/norm/route rule set. Generated
norm and route rule identities retain their historical `r:norm:` and `r:route:`
prefixes: their authored identifiers must fit with those prefixes inside 128
characters (121 and 120 respectively). A generated rule may not collide with
another generated or authored rule. Named references inherit lexical bindings,
so indirect quantifier shadowing is rejected at its defining declaration.

These checks correct source admission of requests the frozen kernel already
refused. They do not change evaluator truth tables or protocol limits.
