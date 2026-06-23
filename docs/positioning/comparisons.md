# Yuho Compared With Adjacent Systems

Yuho is a local, corpus-backed criminal-statute DSL compiler. It is not a
general Rules as Code platform, not a mature public benefits engine, and not a
legal-document interchange standard. The comparisons below are intended to keep
project claims specific.

## Catala

Catala is the closest language-design comparison. It is built for literate
legislative programming: statutory text and executable meaning are kept close,
with prioritized default logic designed for socio-fiscal law.

Yuho is stronger today on checked-in criminal-code corpus work, multi-target
transpilation, reference graphs, and retained local verification gates. Catala
is stronger on lawyer-facing executable-law methodology: line-by-line statute
mapping and a clearer default-logic language center.

Practical takeaway: Yuho should borrow Catala's discipline around one-to-one
source mapping and canonical default semantics before claiming stronger
faithfulness.

Sources:

- <https://github.com/CatalaLang/catala>
- <https://arxiv.org/pdf/2103.03198>

## L4

L4 is broader than Yuho. Public L4 material describes a legal DSL/CNL family
with compiler, IDE, LSP, REPL, web editor, decision-service, API, trace, and
visualization workflows. It is closer to a general legal-specification platform.

Yuho is narrower: section-level criminal-law encoding, corpus maintenance,
local CLI checks, transpilers, reference graphs, Z3/Alloy/Lean evidence, and
comparative Penal Code work. That narrower scope is defensible, but Yuho should
not present itself as a replacement for L4's application-platform direction.

Practical takeaway: use Yuho when the problem is criminal-code corpus audit and
transpilation; use L4-style tooling when the problem is a broader decision
service or contract/regulation workflow.

Sources:

- <https://github.com/smucclaw/l4-ide>
- <https://l4-documentation.readthedocs.io/en/latest/docs/returning-L4-and-law.html>

## OpenFisca

OpenFisca is a mature policy-computation engine: model legislation, provide
situations as input, calculate taxes/benefits/rights, and expose open APIs.

Yuho is more formal/legal-structure oriented and less production policy-engine
or API oriented. Yuho's criminal-law corpus and formal-output breadth are real
advantages for research, but they do not replace OpenFisca's runtime and API
maturity for socio-fiscal policy delivery.

Practical takeaway: Yuho should improve fact models and APIs before comparing
itself favorably to OpenFisca as an executable decision engine.

Sources:

- <https://openfisca.org/en/>
- <https://openfisca.org/doc/index.html>

## Blawx

Blawx is a web-based, user-friendly declarative Rules as Code tool for encoding,
testing, using, and explaining rules. It is designed around non-programmer
accessibility more than compiler/corpus engineering.

Yuho is stronger on git-native corpus structure, multiple legal-document export
targets, and local formal-backend experiments. Blawx is stronger on guided
authoring, explanation UX, and approachable legal-rule interaction.

Practical takeaway: Yuho needs controlled-authoring templates and better
explanation of evidence/proof semantics before it can claim comparable
lawyer-facing usability.

Sources:

- <https://github.com/Lexpedite/blawx>
- <https://law.mit.edu/pub/blawxrulesascodedemonstration>

## Akoma Ntoso

Akoma Ntoso is a legal document XML/interchange standard. Yuho emitting AKN is
a credibility point for legal-document interoperability, especially because the
corpus round-trip is XSD-checked. It is not evidence that Yuho's executable
semantics are correct.

Practical takeaway: treat AKN output as structured legal-document export, not a
semantic verifier.

Source:

- <https://www.oasis-open.org/standard/akn-v1-0/>

## LegalRuleML

LegalRuleML is an OASIS standard for representing legal normative rules. Yuho's
LegalRuleML export is useful for interoperability and review, but the exporter
is still part of Yuho's trusted implementation surface.

Practical takeaway: LegalRuleML output should be tested for source coverage and
semantic preservation where Yuho makes semantic claims.

Source:

- <https://www.oasis-open.org/standard/legalruleml-core-specification-version-1-0-oasis-standard/>

## Z3, Alloy, And Lean

Z3, Alloy, and Lean are serious tools, but they serve different roles. Z3 is an
SMT backend, Alloy is bounded relational analysis/model finding, and Lean is a
proof-assistant/specification route. Using any of them does not automatically
verify Yuho; the encoder and proof boundary remain the key trust boundary.

Practical takeaway: publish unsupported feature sets, keep differential tests,
and avoid saying the law is verified when only a translation layer and selected
fixtures are checked.

Sources:

- <https://microsoft.github.io/z3guide/docs/logic/intro/>
- <https://alloytools.org/alloy6.html>
- <https://lean-lang.org/>
