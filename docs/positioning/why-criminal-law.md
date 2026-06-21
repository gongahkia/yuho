# Why Criminal Law

Yuho focuses on criminal law because it is a high-leverage, bounded domain for
rules-as-code research. Criminal statutes have a repeatable structure: offence
elements, mental-state requirements, circumstances, exceptions, general
defences, penalties, illustrations, amendments, and case-law glosses. That shape
is formal enough for a compiler, but still legally rich enough to test whether a
DSL can preserve doctrine rather than flatten it into a checklist.

The fit is especially strong around defeasibility. Governatori and Wong's CCLAW
paper on defeasible semantics for L4 describes the same pressure point Yuho
faces: legal rules are usually not simple monotonic implications. A norm may be
prima facie satisfied, then defeated by an exception, displaced by a priority
rule, excluded by a special provision, or reshaped by a contrary authority.
Criminal law makes those mechanics visible in everyday statutory form.

Yuho uses that overlap as a specialization, not a claim to own the general
problem. L4 can stay broad: contracts, regulations, business rules, decision
services, APIs, and IDE workflows. Yuho narrows the surface to criminal codes
and makes the corpus itself the product:

- Singapore Penal Code sections encoded as reviewable `.yh` files;
- Malaysia, Pakistan, IPC, and BNS material for comparative coverage;
- offence-element tags such as `actus_reus`, `mens_rea`, and `circumstance`;
- penalties, exceptions, illustrations, references, and case-law treatments;
- cross-jurisdiction diffs that compare the same section number across corpora.

This niche keeps the project technically honest. A criminal-code workbench must
handle provisions that cross-reference each other, exceptions that defeat
otherwise complete offences, penalties that depend on conditions, repeals and
amendments, and doctrinal language that cannot be reduced to a single boolean.
Those constraints are concrete enough to test, but broad enough to exercise the
compiler, AST, linter, transpilers, Z3/Alloy backends, and visualization tools.

The positioning is therefore simple: Yuho is not trying to be the general legal
rules platform. Yuho is the criminal-law corpus compiler. Its output can support
L4-style systems, research prototypes, teaching materials, and audit workflows,
but its center of gravity remains section-by-section criminal statute encoding.

## Sources

- Governatori and Wong, "Defeasible semantics for L4" (2023): <https://ink.library.smu.edu.sg/cclaw/5/>
- [Yuho and L4 positioning](yuho-vs-l4.md)
- [Yuho formal semantics](../researcher/formal-semantics.md)
