# Yuho and L4

Yuho and L4 are complementary rules-as-code projects. L4 is a broad legal
specification language for contracts, legislation, regulation, business rules,
decision services, IDE workflows, REST APIs, MCP tooling, schemas, traces, and
GraphViz visualizations. Yuho is narrower: a local compiler and corpus toolchain
for encoding criminal statutes as `.yh` files, checking their structure, and
emitting reviewable artefacts for legal-engineering work.

## Shared Ground

Both projects treat legal text as something that benefits from formal structure.
The L4 documentation frames contracts and legislation as specifications whose
rules describe state transitions, decision rules, first-order logic, and
meta-rules such as priority ordering. Yuho makes a similar bet for criminal law:
statute sections become typed AST nodes with elements, penalties, exceptions,
case-law treatments, jurisdiction tags, and transpilations to JSON, English,
Mermaid, Alloy, DOCX, and Akoma Ntoso.

The overlap is strongest around defeasibility. CCLAW's 2023 paper on defeasible
semantics for L4 argues that legal norms usually state prima facie applicability
conditions, then exceptions, exclusions, and conflicts that may prevent a norm
from applying or taking effect. Yuho's criminal-law encoding model uses that
same problem shape, but specializes it into statutory offences, general
defences, priority-ordered exceptions, and cross-section references.

## Different Center Of Gravity

L4 is application-platform oriented. Its current public repository describes a
compiler, VS Code extension, LSP, REPL, web editor, REST decision service,
MCP/WebMCP integration, OpenAPI/JSON schema generation, evaluation traces, and
GraphViz diagrams. That makes L4 a good fit when the target is an operational
decision system or a contract/regulation workflow that needs to become an API.

Yuho is corpus-and-review oriented. Its core value is not hosting a decision
service. It is the ability to keep a jurisdictional criminal-law corpus in git,
parse and lint every statute file, diff comparable sections across Singapore,
Malaysia, Pakistan, India, and BNS material, and generate artefacts that make
doctrinal structure inspectable by lawyers, researchers, and compiler engineers.

## Why Yuho Exists Beside L4

Yuho should not try to be a second general-purpose L4. That would duplicate a
larger platform with a broader language and deployment story. Yuho's defensible
lane is criminal-law depth:

- section-granular corpus layout under `library/`;
- offence-element vocabulary such as `actus_reus`, `mens_rea`, `circumstance`;
- penalties, exceptions, illustrations, and case-law treatment graphs;
- jurisdiction-aware references and comparative section diffing;
- local-first verification/transpilation surfaces for audit and research.

In practice, Yuho can feed L4-style work rather than replace it. Yuho can produce
structured criminal-law datasets, diagrams, Akoma Ntoso, English summaries, and
test fixtures that a broader L4 environment could consume. L4 can remain the
larger specification and service platform, while Yuho remains the criminal-code
workbench optimized for statutory corpus maintenance and doctrinal review.

## Positioning Rule

When the question is "how do we expose legal rules as a general executable
decision service?", start with L4. When the question is "how do we encode,
audit, compare, and maintain criminal statutes section by section?", use Yuho.

## Sources

- L4 repository README: <https://github.com/smucclaw/l4-ide>
- L4 documentation, "How L4 Approaches Law": <https://l4-documentation.readthedocs.io/en/latest/docs/returning-L4-and-law.html>
- Governatori and Wong, "Defeasible semantics for L4" (2023): <https://ink.library.smu.edu.sg/cclaw/5/>
- [Yuho formal semantics](../researcher/formal-semantics.md)
