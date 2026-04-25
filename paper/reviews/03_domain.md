# Reviewer 2 Report — Domain Expertise

**Reviewer**: AI & Law / Legal Informatics
**Manuscript**: Yuho: A DSL for the Singapore Penal Code

## 1. Summary

The paper presents Yuho, a statute-shaped DSL with tree-sitter parser, six transpilers, LSP/MCP surfaces, and Z3/Alloy verification, applied at full coverage to the Singapore Penal Code 1871 (524 sections). The headline claims are: (i) a statute-shaped grammar with first-class fields for elements (with deontic types and burden qualifiers), penalty algebra (cumulative/alternative/or_both/nested), Catala-style prioritised exceptions, and amendment lineage; (ii) a complete public encoding; (iii) end-to-end tooling; (iv) a fourteen-item grammar-gap catalogue separating genuine grammar limitations from diagnostic-layer issues. The engineering is impressive and the empirical posture (mass-encode-and-report-gaps) is genuinely useful. The legal-informatics framing, however, is thin: the field has thirty-plus years of literature on deontic logic, isomorphism, burdens of proof, normative systems, and contract DSLs that the paper substantially ignores. A 14-entry bibliography is too small for a paper that claims to position against "the legal-DSL bracket" (§subsec:rel_wider).

## 2. Domain Strengths

1. **Mass-encoding-as-method.** Reporting which grammar shortcomings actually fired in a 524-section corpus is unusual and valuable — most legal-DSL papers stop at a hand-picked exemplar. The G1–G14 catalogue with classification into grammar-vs-lint is the paper's most original methodological contribution (§subsec:gaps).
2. **Penalty algebra as a first-class primitive.** Treating `or_both`/`cumulative`/`alternative`/`nested` as combinators rather than smuggling them under generic disjunction is a real distinction that the existing literature does not surface (most legal DSLs treat sanctions as a free-text annotation or a single number). This is genuinely under-served prior art (§subsec:penalty).
3. **Statute-shaped top level vs. scope-shaped.** The §subsec:rel_catala argument that scope-call shape (Catala) is mis-fit for penal sections (which bundle illustrations and case-law anchors that are not function arguments) is well-articulated and persuasive on its own terms.
4. **Honest diagnostic separation.** The classification of G2/G7 as not-a-gaps and G10 as a deferred semantic resolver (rather than backing-fill the grammar) is methodologically clean and worth emulating elsewhere in the field.
5. **Source-of-truth posture in version control.** Treating the `.yh` file as canonical with all renderings derived (vs. LDOC's Word-canonical posture) is the right architectural commitment for legal infrastructure that needs to be diffable, reviewable, and machine-checkable.

## 3. Domain Weaknesses

1. **Literature coverage is thin to the point of distortion.** Fourteen citations is implausibly few for a paper claiming to position against "the legal-DSL bracket." Critical omissions include eFLINT, Symboleo, RegelSpraak, DMN, FlintScript, Stipula, ContractLarva, the entire Prakken/Sartor/Governatori/Boella/van der Torre corpus on normative systems, the Bench-Capon & Coenen isomorphism debate, von Wright's foundational deontic logic, and Hohfeldian rights/duties analysis (see §5). Any one omission would be forgivable; the cumulative effect is a paper that reads as if the field began with Sergot and ended with Catala.
2. **Deontic types are named but not theorised.** The paper introduces `obligation`/`prohibition`/`permission` as element kinds (§subsec:elements) but does not engage with Standard Deontic Logic (SDL), the obligation/permission duality, contrary-to-duty obligations, or LegalRuleML's deontic layer beyond a one-line "the mapping is straightforward" (§subsec:rel_akn). For a paper that lists "deontic element types" as a column where Yuho claims first-class support (Table 3), this is a substantive gap.
3. **Catala characterisation is partly inaccurate.** §subsec:rel_catala says "compilation to Z3 follows Catala's prioritised-rewriting algorithm in shape if not in proof." Catala compiles to OCaml and Python (the paper itself notes this in §subsec:rel_catala lines 73–74 of background.tex). The Z3 hookup is the *authors'* contribution, not Catala's. The phrasing risks suggesting Catala has a Z3 backend it does not have.
4. **Isomorphism is the elephant in the room.** §sec:conclusion's "statute-as-source-of-truth" thesis is precisely the isomorphism principle (Bench-Capon & Coenen 1992): the formal representation should mirror the textual structure of the source statute clause-for-clause. The paper does not cite the isomorphism debate and does not engage with the well-known objections (normalisation tensions, incompleteness for open-textured terms). This is a substantive theoretical gap, not a missing footnote.
5. **"Common-law penal code" framing is at minimum tense, possibly wrong.** The Singapore Penal Code descends from Macaulay's 1860 Indian Penal Code, which was deliberately *codified* in the civil-law style precisely *because* common-law judge-made criminal law was viewed as too unsystematic for British-Indian administration. Calling it a "common-law penal code" (§subsec:rel_wider, §sec:intro line 36 implicitly) papers over the codification heritage.

## 4. Comparison Matrix Audit (Tables 3 & 4)

Going cell-by-cell. Citations to lines/columns in §subsec:matrix.

**Table 3 (Expressivity):**

- **Yuho row, all checkmarks.** The "Catala-style priority" checkmark for Yuho is somewhat self-fulfilling: the column is defined as "Catala-style priority" and Yuho declares Catala-style priority. Fine, but the column is not adversarial.
- **Catala / Deontic element types: ---.** Defensible — Catala does not have first-class deontic types — but Catala scopes can encode deontic patterns via boolean output variables; this is at least a `~`. Not a fatal misclassification.
- **Catala / Penalty algebra: ---.** Accurate. Catala has no domain-specific sanction combinator. However, the column is somewhat unfair: Catala's domain is tax, not criminal — penalty algebra was never a target. The matrix should annotate "n/a to declared scope" rather than "---" to be fair.
- **Catala / Burden qualifiers: ---.** Accurate; Catala has no burden-of-proof annotation.
- **Catala / Verbatim illustration blocks: ---.** Catala source files do support comments and rendered annotations, but not as a typed AST node. `~` would be defensible. `---` is harsh.
- **Catala / Amendment lineage: ---.** Accurate.
- **lam4 / Deontic element types: checkmark.** Plausible given lam4's deontic-logic core; cannot fully verify without primary-source review since lam4 is cited as a project repo (§subsec:rel_lam4). Reviewer cannot confirm.
- **lam4 / Penalty algebra / Burden / Causal-temporal / Amendment: ---.** Plausible for a contracts-and-regulations DSL. `n/a` would be fairer than `---` for penalty algebra, since contracts have remedies, not penalties.
- **LexScript row.** Cannot verify without primary-source review; LexScript is cited as project documentation only.
- **LDOC row.** "Statute-shaped top-level: checkmark, Verbatim illustration blocks: checkmark." Defensible. "Deontic element types: ---" — not engaging with whether LDOC has any semantic typing at all; the row reads as "Word document" essentially, which the paper acknowledges (§subsec:rel_ldoc).
- **Akoma Ntoso / Statute-shaped top-level: checkmark.** Yes — `<act>`/`<section>` hierarchy is exactly this.
- **Akoma Ntoso / Deontic element types: ---.** Accurate; AKN is structural, not semantic.
- **Akoma Ntoso / Verbatim illustration blocks: checkmark.** Generously interpreted (AKN can carry any text content); a stricter reading would say `~` because AKN does not type illustrations as a distinct construct.
- **Akoma Ntoso / Amendment lineage: checkmark.** Largely accurate. The `<modifies>`/`<modification>` family (within the Akoma Ntoso `<meta>/<lifecycle>` and `<analysis>` containers, plus the `<active>/<passive>` modification elements) does capture amendment lineage with point-in-time versioning. The §subsec:rel_akn description ("`<modifies>` element family captures every gazetted amendment with its own metadata") is in the right ballpark but slightly imprecise — AKN's modification model is active/passive bidirectional and the element names are `<activeModifications>`/`<passiveModifications>` containing `<textualMod>`, `<meaningMod>`, `<scopeMod>`, etc. Recommend tightening the description with a precise XPath-style citation rather than the generic "<modifies> family" phrasing.
- **LegalRuleML / Statute-shaped top-level: n/a.** Correct — LegalRuleML is rule-shaped, not statute-shaped. Good use of `n/a`.
- **LegalRuleML / Deontic element types: checkmark.** Accurate. LegalRuleML has explicit `<lrml:Obligation>`, `<lrml:Permission>`, `<lrml:Prohibition>` constructs (per the OASIS spec). The paper is correct here.
- **LegalRuleML / Catala-style priority: ~.** Defensible. LegalRuleML has defeasibility (`<lrml:Override>`, `<lrml:Strength>`) which is in the prioritised-default neighbourhood but is not Catala's prioritised rewriting. `~` is fair.
- **LegalRuleML / Burden qualifiers: ---.** Inaccurate — LegalRuleML has `<lrml:hasReversedBurdenOfProof>` and related burden-of-proof constructs. This is a factual error that should be corrected to `~` or `checkmark`.
- **LegalRuleML / Causal/temporal: ---.** LegalRuleML has temporal constructs (`<lrml:hasTemporalCharacteristics>`); should be `~`. Causal as such, fair to mark `---`.

**Table 4 (Tooling):**

- **Catala / Verification: "native rewriting".** Imprecise. Catala formalises its rewriting semantics with a soundness proof but does not ship a verification tool in the Z3/Alloy sense. Recommend "soundness-proven rewriting (no SMT backend)" or similar.
- **lam4 / LSP: ~.** Cannot verify.
- **LegalRuleML / Verification: "via mappings".** Vague. LegalRuleML has been mapped to Defeasible Logic, SPINdle, and Drools by Governatori and others; this should be cited specifically.
- **LegalRuleML / Transpile targets: "Several rule-language exports".** Accurate but vague; specific examples (RuleML, Drools) would strengthen the row.
- **Corpus scale / Catala: "Fragments of FR tax code".** Catala has substantially more than fragments now — by 2024 the team had encoded large portions of the *aide au logement* and *impôt sur le revenu* code sections. Recommend updating with a specific citation.

**Net audit conclusion:** Table 3 has at least one factual error (LegalRuleML / Burden) and several `---` cells that should be `~` (Catala / Verbatim illustration blocks; LegalRuleML / Causal-temporal). The matrix is broadly defensible in shape but reads as if the columns were chosen *after* deciding what Yuho would win on. Adding two columns where Yuho is not first ("formal soundness theorem" and "production deployment in a sovereign tax authority") would help readability and credibility.

## 5. Missing Prior Art (Required)

Top 12 missing references, ordered roughly by criticality. CRITICAL = should not be merged without; SUGGESTED = strongly recommended.

1. **CRITICAL — eFLINT (van Doesburg, van Engers et al.).** *Searls, T. & van Doesburg, R. & van Engers, T. — "eFLINT: a Domain-Specific Language for Executable Norm Specifications." GPCE 2020.* eFLINT is a norm-based DSL with explicit acts, facts, duties, and Hohfeldian frame; it is the closest peer to Yuho's element/deontic-types model and is a glaring omission. Why it matters: eFLINT precedes Yuho on essentially every "deontic element types + executable" axis Table 3 claims as Yuho's strength.

2. **CRITICAL — Bench-Capon & Coenen, isomorphism.** *Bench-Capon, T.J.M. & Coenen, F.P. — "Isomorphism and legal knowledge based systems." AI and Law 1(1), 1992, pp. 65–86.* The "statute-as-source-of-truth" thesis (§sec:conclusion) is exactly the isomorphism principle. Not citing this debate is a serious theoretical gap. Why it matters: the well-known objections (normalisation, open-textured terms, transformation-vs-mirror) directly bear on Yuho's claims and the paper has no answer because it does not engage.

3. **CRITICAL — DMN (Decision Model and Notation).** *OMG, "Decision Model and Notation" v1.4, 2022.* DMN is the OMG standard for decision logic, widely used for benefits/eligibility-style legal reasoning, with FEEL expression language and a defined execution semantics. Several legal-tech vendors (including DSLs in this space) target DMN. Omission means the comparison matrix is missing an actually-deployed competitor.

4. **CRITICAL — Symboleo.** *Soavi, M., Sharifi, S., Amyot, D., Briand, L., Roveri, M., Pastor, A., et al. — "Symboleo: Towards a Specification Language for Legal Contracts." RE 2020 / IEEE 2022.* Contract specification language with formal semantics; closer to lam4 than to Yuho but still a peer in the legal-DSL space.

5. **CRITICAL — Governatori on RuleML / Defeasible Deontic Logic.** *Governatori, G. — "Representing Business Contracts in RuleML." Int. J. Cooperative Info. Sys. 14(2-3), 2005.* And: *Governatori, G., Olivieri, F., Rotolo, A., Scannapieco, S. — "Computing Strong and Weak Permissions in Defeasible Logic." JPL, 2013.* These are the standard references for deontic operators in machine-executable form. The §subsec:rel_akn claim that Yuho's deontic operators map straightforwardly to LegalRuleML's needs to engage with what Governatori et al. have already proved about defeasibility/permission interaction.

6. **CRITICAL — Prakken on burden of proof.** *Prakken, H. & Sartor, G. — "A logical analysis of burdens of proof." Legal Evidence and Proof: Statistics, Stories, Logic, 2009.* Yuho's `burden prosecution` / `burden defence` qualifiers are claimed as a column where Yuho is alone (Table 3). Prakken & Sartor distinguish burden of production vs. persuasion vs. tactical burden; Yuho's two-token taxonomy is a substantial simplification that should at minimum acknowledge the literature.

7. **CRITICAL — von Wright / Standard Deontic Logic.** *von Wright, G. H. — "Deontic Logic." Mind 60(237), 1951, pp. 1–15.* Foundational. Cannot introduce obligation/prohibition/permission as element kinds without at least one citation to the deontic-logic foundations. Even an SDL textbook citation (e.g., *Gabbay, Horty, Parent, van der Meyden, van der Torre — Handbook of Deontic Logic and Normative Systems, 2013*) would suffice.

8. **SUGGESTED — Boella & van der Torre on normative systems.** *Boella, G. & van der Torre, L. — "Regulative and Constitutive Norms in Normative Multiagent Systems." KR 2004.* Constitutive vs. regulative norm distinction directly bears on Yuho's deontic types vs. structural types separation.

9. **SUGGESTED — RegelSpraak.** Dutch tax authority (Belastingdienst) production DSL for tax-rule encoding. Not always in academic publications but well-documented; relevant as a deployed-in-anger comparator to Catala. Citation form likely a Belastingdienst technical report or *de Gier et al.* presentations.

10. **SUGGESTED — Stipula.** *Crafa, S., Laneve, C., Sartor, G., Veschetti, A. — "Pacta sunt servanda: legal contracts in Stipula." Sci. Comput. Program. 225, 2023.* Smart-contract DSL with legal-contract semantics; relevant to the contract end of the spectrum that Yuho disclaims but the comparison table touches.

11. **SUGGESTED — Hohfeld and the rights/duties layer.** *Hohfeld, W. N. — "Some Fundamental Legal Conceptions as Applied in Judicial Reasoning." Yale LJ 23, 1913.* Plus *Sartor, G. — Legal Reasoning: A Cognitive Approach to the Law, 2005* for the modern computational treatment. Relevant because Yuho's `obligation`/`prohibition`/`permission` is a partial Hohfeldian taxonomy that omits power/liability/immunity/disability.

12. **SUGGESTED — Atkinson & Bench-Capon on argumentation post-2003.** *Atkinson, K., Bench-Capon, T. — "Legal Case-based Reasoning as Practical Reasoning." AI and Law 13(1), 2005.* The benchcapon2003legal citation in the bib is the value-based-argumentation paper; the case-based-reasoning extension is more relevant to the §subsec:limitations point about case-law-to-type-system lifting.

**Bonus, less critical but worth a footnote:** Sergot's actual follow-up on BNA in *Sergot, M. — "The Representation of Law in Computer Programs," 1991*; Pace et al. on contract monitoring (ContractLarva); Allen & Saxon on "A-HOHFELD" formalising Hohfeld; Wyner & Bench-Capon on argument schemes for case law.

## 6. Theoretical Framing Concerns

1. **Isomorphism not addressed.** §sec:conclusion's "statute-as-source-of-truth" thesis is the isomorphism principle; the paper neither cites Bench-Capon & Coenen 1992 nor the substantial follow-up (Bourgine, Karpf, etc.). The well-known tension — isomorphism preserves traceability but resists normalisation that the formal representation might require — bears directly on Yuho's design choice (statute-shaped top level rather than scope) and should be discussed.

2. **Catala framing slightly miscasts the contribution.** §subsec:rel_catala "compilation to Z3 follows Catala's prioritised-rewriting algorithm in shape if not in proof" — Catala compiles to OCaml/Python. The Z3 implementation is the authors' own. Recommend rephrasing to "we adopt Catala's prioritised-default *semantics* and re-implement it as a Z3 encoding; we do not inherit Catala's soundness proof and do not provide our own." This is a [Inference] reading of what the authors mean, but the current phrasing risks misleading readers into thinking Catala has a Z3 backend.

3. **Deontic types underspecified.** §subsec:elements introduces obligation/prohibition/permission as element kinds but does not specify: (a) whether they are SDL-style propositional operators or first-order; (b) how prohibition relates to negated permission; (c) whether contrary-to-duty obligations are expressible; (d) what happens when an element is both an obligation and a circumstance (some Penal Code drafting does this — failure-to-report duties). Without a semantic spec the deontic-types claim in Table 3 is essentially syntactic.

4. **Burden qualifiers as labels, not semantics.** §subsec:elements treats `burden prosecution`/`burden defence` plus a named proof standard as element annotations. There is no formal semantics for what these labels do. In Prakken's framework, burden of proof is a procedural notion that interacts with the dialectical state of the proceeding; in Yuho it is a static type-system tag. Either acknowledge the simplification or upgrade the framing.

5. **"Common-law penal code" elides the codification heritage.** The Indian Penal Code (Macaulay 1860) was deliberately codified in the civil-law style. The Singapore Penal Code inherits this codification. Calling it "common-law" is shorthand for "applied within a common-law jurisdiction" but blurs the form-vs-application distinction. Recommend "codified penal statute applied within a common-law jurisdiction" or similar precise phrasing.

6. **"Engineering rather than research" disclaimer too modest in one direction, too immodest in another.** §subsec:rel_wider says Z3/Alloy application to legal reasoning is engineering not research. Bourgine, Boella, Governatori, Bench-Capon and others have been doing precisely this since the 2000s, much of it research-grade. The disclaimer simultaneously (a) ignores that the prior art exists (immodest) and (b) understates that the *integration* of Z3/Alloy with a tree-sitter parser, a fidelity linter, and a structured DSL is itself a non-trivial engineering contribution worth claiming.

7. **"Statute-shaped" is itself an isomorphism commitment.** The paper's most distinctive design choice is exactly the isomorphism choice; framing it as a pragmatic engineering decision rather than a position in a long-running debate undersells the contribution and ducks the standard objections.

8. **Anglo-Indian generalisation argument is correlational, not causal.** §sec:intro line 91–97 argues Yuho should be portable to Indian/Pakistani/Bangladeshi/Bruneian/Malaysian penal codes because they share Anglo-Indian heritage. This is plausible [Inference] but the paper acknowledges (§subsec:threats) that it has not been verified. Recommend explicitly downgrading the claim from "plausibly portable" (which sounds asserted) to "an empirical question we have not yet tested" everywhere it appears.

## 7. Specific Domain-Substance Comments

1. **§subsec:elements, deontic types.** The list `actus_reus | mens_rea | circumstance | obligation | prohibition | permission` mixes two ontological levels: the first three are common-law criminal-doctrine categories; the last three are deontic-logic operators. This is conceptually awkward — what does it mean for an `obligation` element to coexist with an `actus_reus` element in the same `all_of`? The paper should either (a) separate the two layers (criminal-doctrine kind + deontic-modality flag), or (b) explain why mixing them is intentional. Currently neither is done.

2. **§subsec:exceptions, "consent" priority 1 vs "self_defence" priority 2.** In Singapore criminal law, both are general exceptions under Chapter IV (s87 ff for consent; s96-106 for private defence). Their priority interaction in real cases is not literally "lower number fires first" — it is governed by the doctrine that self-defence is available even when consent is not, and consent has narrower scope. The integer-priority encoding may be an oversimplification of the doctrinal reality. Recommend the paper say so explicitly: priority is an encoder choice, not a doctrinal fact.

3. **§subsec:penalty, `or_both`.** The paper rightly identifies `or_both` as a frequent Penal Code idiom and treats it as a primitive. But the verification semantics it claims differ between `or_both` and `alternative` are not specified. What does `imprisonment or_both fine` mean to Z3? Is it `imprisonment ∨ fine ∨ (imprisonment ∧ fine)` (an inclusive-or)? If so, why is `alternative` (the exclusive case) not just a constraint addition? The combinator distinction needs a verification-semantics spec.

4. **§subsec:exceptions, "guard" vs "condition".** §subsec:exceptions describes exception fields as `condition`/`effect`/`priority`/`defeats`, but the code example uses `guard` instead of `condition`. Internal inconsistency — clarify which is the canonical keyword.

5. **§subsec:subsections, repeated `effective` clauses for amendment lineage.** The paper says repeated `effective <date>` clauses encode amendment lineage. But amendment in real legislative practice does not just add a date — it modifies specific text. Akoma Ntoso's `<textualMod>`/`<meaningMod>` distinction captures this; Yuho's `effective` clause does not. The §subsec:rel_akn promise to "match" AKN's amendment-lineage support is therefore overstated. Recommend either deepening the model or qualifying the claim as "first-order temporal versioning, not full textual-modification tracking."

6. **§subsec:rel_lam4, `IS_INFRINGED`.** The lam4 description (§subsec:rel_lam4) of `IS_INFRINGED` as a contract predicate that composes is plausible, but the planned import for §G10 is described in semi-promissory form ("we expect to import the predicate name and semantics, with credit"). The paper should be clearer that this is future work and that the current encoding does not yet have inter-section semantic predicates.

7. **§subsec:rel_akn, characterisation of `<modifies>` family.** The element name in AKN is not literally `<modifies>` but rather `<modification>` (within `<activeModifications>`/`<passiveModifications>` containers) and the related `<textualMod>`, `<meaningMod>`, etc. Recommend tightening to a precise reference (the AKN spec section on lifecycle modifications) rather than the imprecise "<modifies> element family."

8. **§subsec:rel_catala, "Catala has the right defaults but no penalty algebra in the relevant sense."** Accurate, but the framing implies the comparison is well-defined. Catala's domain (tax) does not need penalty algebra; the dimension is one Yuho introduced. Recommend a softer phrasing: "Catala does not need penalty algebra for its declared domain; for penal code we found we did need it, and built it."

9. **§subsec:fidelity, "fabricated fine cap" diagnostic.** The 48-section warning rate is reported but the methodology section itself acknowledges (§subsec:fidelity_eval) that the L3 reviewer signed off pre-sentinel. This means the diagnostic is catching the reviewer's own prior errors — an honest finding, but the paper should foreground this more clearly: the diagnostic is *retroactively* repairing lapses in the reviewer's own pipeline.

10. **§sec:limitations, single-jurisdiction caveat.** The Anglo-Indian heritage claim is invoked twice (§sec:intro and §subsec:threats) as the warrant for cross-jurisdiction generalisation. This is plausible [Speculation] but the paper offers no empirical evidence. The 50-section IPC sample plan is mentioned but unfunded/undated. Recommend the paper either run the IPC sample for the camera-ready or downgrade the cross-jurisdiction claim to a question.

11. **§sec:conclusion, "statute-as-source-of-truth."** This phrase appears once in the conclusion and is doing substantial theoretical work. It deserves a paragraph, a citation to Bench-Capon & Coenen 1992, and a frank acknowledgement that it is the isomorphism position with all the standard objections that come with it.

12. **Hammond 1983 citation looks suspect.** The bib entry for `hammond1983rights` has title "APES: a user-friendly advice-giving system" with a note "cited via secondary literature." This is a placeholder. The §sec:background citation slot ("Subsequent work by Hammond, Bench-Capon, and others") could either be replaced with a verifiable Hammond reference (e.g., Hammond's APES papers in the legal-expert-systems literature of the mid-1980s) or dropped if the author cannot verify. As cited it adds nothing and risks reviewer suspicion.

13. **Lessig 1999 cited but its argument is opposite.** `lessig1999code` (Code and Other Laws of Cyberspace) is in the bib but I cannot find its in-text citation in the sections I read. Either it should be cited and engaged with (Lessig's "code is law" thesis is *that the architecture of code becomes regulation*, which is the inverse of "law as code"), or it should be removed from the bib.

14. **Placeholder bib entries for arXiv preprint.** `lam4`, `lexscript`, `ldoc`, and `hammond1983rights` are flagged as placeholder/secondary. For arXiv submission this is borderline acceptable for the project URLs (lam4, lexscript, ldoc) but not for `hammond1983rights`. Replace `hammond1983rights` with a verifiable citation or drop. The `lam4`/`lexscript`/`ldoc` URL-only citations should at least be augmented with retrieval dates and (where available) commit hashes.

## 8. Recommendation

- **Decision: Major revision.**
- **Confidence: 4/5** (high on the legal-informatics literature and theoretical-framing critique; lower on lam4/LexScript/LDOC primary-source verification, which I cannot independently confirm without access to those projects).
- **Per-dimension scores (0–100):**
  - Literature Coverage: **35** — the 14-entry bibliography is the single biggest defect; eFLINT, isomorphism, Governatori, Prakken, von Wright, DMN, Symboleo, Hohfeld are all missing.
  - Theoretical Framing: **45** — the deontic types, burden qualifiers, and statute-as-source-of-truth thesis are introduced without engaging the substantial existing literature on each.
  - Domain Accuracy: **65** — mostly accurate but with at least one factual error in Table 3 (LegalRuleML burden of proof), one mischaracterisation of Catala's compilation targets, and one slightly imprecise AKN amendment-lineage description.
  - Comparison Fairness: **55** — the matrix columns appear chosen post-hoc; some `---` cells should be `~`; the Catala "Penalty algebra: ---" cell is technically correct but unfair without an n/a-to-scope annotation.
  - Field Contribution: **70** — the mass-encoding-and-gap-cataloguing methodology is genuinely original; the penalty algebra is a real distinction; the engineering is solid. The contribution is real but undersold by thin literature engagement.

**Rationale.** The paper's empirical and engineering contribution is genuine and worth publishing: 524 sections of a real penal code, encoded, version-controlled, machine-checkable, with a fourteen-gap catalogue that is unusually honest about what the grammar can and cannot do. The legal-informatics framing, however, is too thin to land at venue-quality. A revision that (a) expands the bibliography to engage eFLINT, the isomorphism debate, von Wright/SDL, Prakken on burdens, Governatori on RuleML, and DMN; (b) corrects the LegalRuleML burden-of-proof cell and the Catala-compiles-to-Z3 implication; (c) renames "common-law penal code" to acknowledge the codification heritage; and (d) explicitly engages the isomorphism principle as the theoretical home of the "statute-as-source-of-truth" thesis would make this a strong contribution to the legal-DSL literature. Without these revisions the paper will read, to a legal-informatics reviewer, as if the author has built impressive infrastructure without having read the field they are contributing to.
