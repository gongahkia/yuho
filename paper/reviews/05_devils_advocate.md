# Devil's Advocate Report

**Reviewer**: Adversarial / Devil's Advocate
**Manuscript**: Yuho: A DSL for the Singapore Penal Code as Executable Statute

## 1. Strongest Counter-Argument (200-300 words)

The paper's headline finding — "524/524 at L1+L2 + 524/524 at L3" (abstract; §sec:intro; §sec:conclusion) — is a coverage statistic produced by a closed loop in which the author is simultaneously the grammar designer, the encoder, the L3 reviewer dispatcher, the checklist author, and the agent operator. §sec:limitations concedes this directly: "the same author wrote both the encodings and the dispatcher, and runs the checklist via agent sessions trained on encoding conventions the author defined" and the L3 stamp "should be read as 'the encoder believes the encoding is faithful, and the mechanical checklist did not flag a fidelity issue', not as a legal opinion." Yet the abstract, intro contributions, and conclusion all foreground 524/524 as if it were external validation, and the paper's central thesis — that "the gap between drafted penal section and executable encoding is mostly a grammar gap" — is supported by no evidence other than the author's own encoding pass.

Three additional structural problems compound this. First, the 14-gap catalogue has been retroactively trimmed: G2 and G7 are reclassified as not-a-gap and G10 deferred (§subsec:gaps), so the catalogue presented as a "research contribution" (§sec:intro) is in fact an engineering punch-list curated post-hoc. Second, the verification stack (§subsec:verify) checks well-formedness of the *encoding*, not legal correctness — a mismatch between the abstract's "machine-checkable artefacts" framing and §sec:limitations's "for checking the encoding is well-formed, not for adjudicating the law." Third, the comparison matrix (§subsec:matrix) selects eight columns on which Yuho is alone — but omits columns (proven semantics, soundness theorem, deployed users, peer-reviewed publication, multi-jurisdiction coverage) on which Catala, Akoma Ntoso, or LegalRuleML would dominate. The thesis is plausible; the evidence is self-certified.

## 2. Issue List

### CRITICAL Issues (block Accept)

- **[C-1] Circular validation of the L3 figure** — Dimension: confirmation-bias / circular-reasoning
  - Location: §sec:limitations: "the same author wrote both the encodings and the dispatcher, and runs the checklist via agent sessions trained on encoding conventions the author defined… The L3 stamp should be read as 'the encoder believes the encoding is faithful'". Abstract: "\statLThreePass{} human-stamped at the highest fidelity tier." §sec:conclusion: "\statLThreePass{} carrying a structured human-fidelity stamp at the strictest L3 tier."
  - Challenge: The paper's headline number is presented in the abstract, intro, evaluation, and conclusion without the disclaimer; the disclaimer is quarantined to §sec:limitations. This is rhetorical asymmetry — the marketing text trades on a number whose epistemic content is disclaimed elsewhere. The L3 stamp is "encoder believes encoder is faithful" — a tautology dressed as evaluation.
  - What would resolve: Either (a) demote 524/524 L3 from headline status to a footnoted statistic and re-state the abstract around L1+L2 only; (b) commission ≥30-section external Singapore-qualified-lawyer review and report disagreement rate; (c) blind a non-author reviewer through the same 11-point checklist and report inter-rater agreement.

- **[C-2] Frame mismatch: "machine-checkable" vs. encoding-well-formedness** — Dimension: scope-overreach
  - Location: Abstract: "executable, machine-checkable artefacts." §sec:limitations: "the verification stack is for checking that the *encoding* is well-formed, not for adjudicating the *law*."
  - Challenge: The abstract and intro frame Yuho as machine-checkable in a sense readers will interpret as "legally checkable" — checking statutes, not checking the encoding of statutes. Z3/Alloy verify exception-priority well-formedness, bounded element enumeration, and pairwise inter-section conflict. None of these is a *legal* property; they are syntactic/semantic well-formedness over the encoding. Calling this "machine-checkable" without immediate qualification is misleading.
  - What would resolve: Reword abstract to "machine-checkable encoding (not legal checking)" or equivalent. Move the §sec:limitations disclaimer up into §sec:intro.

- **[C-3] Diagnostic precision unestablished but central** — Dimension: missing-evidence
  - Location: §subsec:fidelity_eval: "98 sections flagged… 48 sections flagged… 208 sections flagged… true-positive rates not yet measured… A hand-rated spot-check of 30 warnings per check is on the punch list before submission." §subsec:threats: "Diagnostic precision unestablished."
  - Challenge: The fidelity hit-rate is one of the paper's two empirical pillars (the other is the gap catalogue). The paper concedes that the precision of the 360 surface warnings is unmeasured, the largest bucket (G11 at 208 hits) is "the lowest-precision," and the spot-check is "on the punch list before submission" — meaning, not done. A "before submission" punch-list item that survives into the submitted draft is not submission-ready.
  - What would resolve: Complete the 30-warning hand-rate before the paper goes out. Report per-diagnostic precision. Rewrite §subsec:fidelity_eval around precision rather than raw hit count.

### MAJOR Issues

- **[M-1] Post-hoc trimming of the gap catalogue** — Dimension: no-true-scotsman
  - Location: §subsec:gaps and Table tab:gaps: "Two gaps initially classified as grammar limitations turned out, on closer inspection, not to be gaps at all (G2, G7); one (G10) is a not-a-gap on the grammar side but does require a separate semantic-resolver pass that remains future work." §sec:intro contribution #4: "ten genuine grammar limitations… and four diagnostic-layer issues."
  - Challenge: The 14-gap claim is doing rhetorical work in the intro and abstract, but the table reveals that 3/14 (G2, G7, G10) have been reclassified or deferred. The original 14-gap formulation came from an earlier mass-encoding pass; reclassifying gaps as "not-a-gap" or "deferred" after the fact, then presenting the trimmed taxonomy as a clean 10/4 split, is a no-true-Scotsman move. G10 in particular is the cross-section semantic resolver — arguably the hardest gap, and it is "deferred." That should be visible in the headline, not buried.
  - What would resolve: Preserve the original 14 in the table with their initial classification, and report the post-hoc reclassifications as a separate column. State explicitly in §sec:intro that 3/14 were trimmed/deferred.

- **[M-2] Selection bias in worked example (s415)** — Dimension: cherry-picking
  - Location: §subsec:s415: "Section 415 of the Penal Code defines the offence of cheating." §sec:conclusion: "the G10 cross-section semantic resolver… abetment-style sections (s107–s120) wrap arbitrary base offences."
  - Challenge: s415 is a clean offence-defining section: typed elements, simple penalty (imprisonment + fine, no caning, no nested combinator), three illustrations, no exceptions in the encoded fragment shown. It does not exercise G10 (cross-section reference), G12 (nested penalty), G13 (exception priority), or the abetment chapter (s107–s120) which is conceded as future work. The worked example is the *easy case* dressed as the representative case. A statute paper that leads with the easy case and defers the abetment chapter is choosing its evidence.
  - What would resolve: Either add a second worked example over a hard case (e.g., s107 abetment, or s302 with nested combinator, or a Chapter IV exception with priority), or explicitly flag s415 as a deliberately simple introductory example and walk through where the harder cases break.

- **[M-3] Cherry-picked comparison matrix columns** — Dimension: cherry-picking
  - Location: §subsec:matrix Table tab:expressivity. Yuho is the only system with checkmarks across all eight columns: statute-shaped top-level, deontic types, burden qualifiers, penalty algebra, Catala-style priority, causal/temporal edges, illustrations, amendment lineage.
  - Challenge: The columns are exactly the features Yuho was designed to support. A column set chosen by Catala's authors would feature: proven soundness of rewriting semantics, formalised type system, multi-language compilation targets with semantic preservation, peer-reviewed publication track, real users in production tax administration. A column set chosen by Akoma Ntoso's authors would feature: jurisdictional breadth, multilingual support, OASIS standardisation, gazette-cycle integration, debate-history pointers. Yuho is on zero-of-five against either. The matrix is not a comparison; it is an opportunity-list.
  - What would resolve: Add columns the competitors care about (formal semantics, soundness theorem, peer-reviewed publication, deployed user base, jurisdictional variety, multilingual). Acknowledge the inversion explicitly.

- **[M-4] Appeal-to-effort fallacy: 38,700 SLOC framed as substance** — Dimension: logical-fallacy
  - Location: §subsec:engineering-numbers Table tab:sloc; §subsec:engineering-numbers narrative: "the surface area is unevenly distributed… the encoded library is roughly 40% the size of the implementation. This ratio is a fair quick check on the DSL's density."
  - Challenge: SLOC is not a research finding. The paper's casual claim that an encoding-to-tooling ratio "below 1:1" indicates over-engineering and "above 2:1" indicates under-expressive language is unsourced and reads like motivated reasoning to land Yuho's 0.42 ratio in the "productive" zone. The 38,700 figure is engineering effort. Effort is not evidence.
  - What would resolve: Remove the density-ratio heuristic or cite a source. Drop the "productive end of this range" claim. Move the SLOC table to an appendix.

- **[M-5] "Statute-as-source-of-truth is viable" — viable for whom?** — Dimension: missing-evidence
  - Location: §sec:conclusion: "The longer-term thesis is that *statute-as-source-of-truth* is a viable posture for legal infrastructure."
  - Challenge: The only user reported in the paper is the author. The MCP server has been used end-to-end "for one exercise" (§subsec:tooling_eval). The VS Code extension is at v0.2 with no installation count. There are no Singapore-qualified lawyers reported as users. No law-school adoption. No government adoption. "Viable" is unsupported beyond "the author built it and uses it." The thesis is therefore empirically untested.
  - What would resolve: Either qualify "viable" to "we built and self-use" or report at least one external user with task-completion data.

- **[M-6] Throughput numbers conflate calendar and compute time misleadingly** — Dimension: misleading-statistic
  - Location: §subsec:throughput: "median wall-clock between first commit on a statute.yh and its first L3 stamp is 1 day; the 95th percentile is comparably tight." Throughput JSON: 499 of 524 sections were encoded on a single day (2026-04-24).
  - Challenge: A median of 1 day is a *calendar* artefact of a single-day mass-encoding sprint. The throughput.json shows 499/524 sections encoded on one day. The "1 day median" reflects "we ran the dispatcher in parallel for one day"; it does not reflect cost, effort, or sustainable rate. The honest number is 40 agent-hours / 524 sections ≈ 4.6 agent-min/section, but that is not the foregrounded number. The paper itself half-acknowledges this ("artefact of the dispatcher-driven workflow rather than evidence of bottleneck-free encoding") yet still leads with the meaningless calendar number.
  - What would resolve: Lead with agent-min/section. Drop the 1-day median or footnote it as an artefact. Report cost: dollar-cost of the agent-hours.

- **[M-7] Holdings-are-strings inconsistency** — Dimension: internal-contradiction
  - Location: §sec:design lists case-law anchors as a structural primitive; §sec:limitations: "Case law is referenced by name, citation, and holding string. The holding is treated as opaque text, not parsed into structured elements." §sec:related Tables: case-law anchors are a Yuho expressivity feature.
  - Challenge: A "structural primitive" that contains opaque text is not a structural primitive — it is a comment field with a schema wrapper. Yet the comparison matrix and §sec:design treat case-law anchors as a meaningful feature on which Yuho is differentiated. The hover output surfaces a holding string. None of this is structural; it is bookkeeping. This is feature-stretching.
  - What would resolve: Demote case-law anchors from "structural primitive" to "metadata field" in §sec:design and the comparison matrix. Be explicit that they carry no semantic content the verification stack uses.

- **[M-8] No generalizable lesson — case study masquerading as research** — Dimension: scope-overreach
  - Location: Whole paper. §sec:intro contribution #4: "Empirical findings: A catalogue of fourteen distinct grammar gaps surfaced during mass-encoding."
  - Challenge: What survives translation to a different jurisdiction or DSL? The paper concedes (§sec:limitations) that cross-jurisdiction portability is unverified — even on the Indian Penal Code, which is the closest possible neighbour. The 14-gap catalogue is specific to the Singapore Penal Code's drafting conventions; nothing in the paper argues these gaps generalise. The result is a case study of one author encoding one statute family with extensive tooling. That can be a fine engineering paper but should not be presented as a research contribution.
  - What would resolve: Either land the 50-section Indian Penal Code pilot promised in §sec:limitations and report grammar-fit, or rephrase the contributions as "case study with engineering artefact" rather than "research findings."

- **[M-9] Alternative framing of the gap catalogue not addressed** — Dimension: missing-alternative-explanation
  - Location: §sec:intro: "every section that the grammar could not natively express is documented as a numbered grammar gap (G1–G14)." gap_frequency.json shows G1=280, G6=243, G8=249 hits.
  - Challenge: The paper frames G1–G14 as gaps "discovered" through principled mass-encoding. An equally plausible framing: the author shipped a deliberately thin grammar and patched it as encoder needs arose. Under the latter framing, "grammar gap" is a euphemism for "feature missing from initial scope." The two framings are epistemically different — discovery implies a stable referent against which gaps are measured; iterative patching implies the grammar shape is whatever the encoder happened to converge on. Nothing in the paper argues for the discovery framing over the iteration framing.
  - What would resolve: Disclose the chronological order in which gaps surfaced and were patched. State whether the grammar was specified ex ante or grew through encoding pressure. The latter is honest and fine; the former is what the paper currently implies.

- **[M-10] Verification stack does not verify legal properties** — Dimension: scope-overreach
  - Location: §subsec:verify; §sec:limitations.
  - Challenge: The Z3 hookup checks "exception-priority well-formedness… deterministic for every reachable element configuration… searches for an element-binding that satisfies both [s299 and s300]." This is consistency-of-encoding. It is not legal verification. The paper acknowledges the calibration in §sec:limitations but the abstract and §sec:intro and §subsec:verify itself talk about Z3 as if it were doing legal work. Inter-section conflict detection between s299 and s300 sounds legally significant; it is in fact a search for a model in which both sets of encoded predicates hold. That a model exists tells you nothing about whether the law has been violated — only about whether the encoder wrote consistent predicates.
  - What would resolve: Reframe §subsec:verify as "encoding consistency" not "verification." Drop the implication that conflict detection between s299/s300 is legally meaningful.

### MINOR Issues

- **[m-1] G11 hit count (208) anchored on a low-precision heuristic** — Dimension: weak-evidence
  - Location: §subsec:fidelity_eval: "G11 (the disjunctive-connective check) to carry a notably lower precision because it ignores the syntactic role of every 'or'."
  - Challenge: 208/360 fidelity warnings come from the lowest-precision check. Removing G11, the headline 360 collapses to 152.
  - What would resolve: Report fidelity hits with G11 separated out, or hand-rate G11 first.

- **[m-2] "Comparable" L3 throughput claims unsupported** — Dimension: missing-evidence
  - Location: §subsec:throughput: hand-encoding "8–12 per hour with the encoder also acting as reviewer; the L3-equivalent stamp rate was effectively 100% on the encoded subset, but only ~25% of the corpus was hand-encoded."
  - Challenge: 25% hand-encoded with 100% self-stamp is the same circular validation as C-1 at smaller scale. Reporting it as a comparison baseline obscures the issue.
  - What would resolve: Drop the hand-encoding-100% comparison or qualify it as self-stamped.

- **[m-3] "Plausibly portable" used twice without evidence** — Dimension: hedge-overuse
  - Location: §sec:intro and §sec:limitations: "plausibly portable across the wider Penal Code family."
  - Challenge: "Plausibly" is doing real load-bearing work in two places. Cross-jurisdiction portability is the paper's main extensibility claim and is unverified.
  - What would resolve: State explicitly "we have not encoded any non-Singapore statute and have no evidence of portability."

- **[m-4] Editor surfaces uneven, but presented as full toolchain** — Dimension: scope-overstating
  - Location: §sec:limitations: "the VS Code extension is at v0.2… the Microsoft Word add-in is in flight but not yet shipped."
  - Challenge: Abstract claims "a Language Server, a Model Context Protocol server, and a Z3/Alloy verification hookup turn an encoded statute into a queryable, diffable, formally-checkable object." Three of the surfaces are partial.
  - What would resolve: Footnote the abstract or qualify "fully-implemented" to "Language Server" only.

- **[m-5] DOCX rendering tested on one machine** — Dimension: weak-tooling-validation
  - Location: §subsec:tooling_eval: "opened in Word for Mac 2024 and Word for Web."
  - Challenge: Two clients on the author's setup is not interop validation.
  - What would resolve: Either drop the DOCX validation paragraph or test more clients.

- **[m-6] "Sub-millisecond" parse claim from one configuration** — Dimension: weak-evidence
  - Location: §subsec:parser: "the runtime overhead of parsing a typical statute file (200 SLOC of Yuho) is sub-millisecond."
  - Challenge: No hardware spec, no benchmark methodology, no distribution.
  - What would resolve: Drop or properly benchmark.

## 3. Ignored Alternative Explanations / Paths

1. **Iterative-grammar hypothesis.** Alternative: Yuho's grammar was not specified ex ante and "discovered" through encoding; it was specified thinly and grown through encoding pressure. The 14 gaps are then patches, not discoveries. The paper would need to disclose the chronological order: which grammar feature existed before which gap surfaced, and which gap was triggered by which section. The git log of `grammar.js` would settle this. Plausibility: high — `paper/methodology/gap_frequency.json` and the "one-shot migration script" for G12 (§subsec:gaps_eval) are consistent with patching, not discovery.

2. **Drafting-fragility hypothesis.** Alternative: Yuho fits the Singapore Penal Code because the SPC is unusually regular among penal codes (Macaulay's drafting tradition, IPC-derived). A statute family further from this tradition (e.g., the U.S. Model Penal Code, the German StGB, or Japanese Keihō) would not yield the same gap catalogue. The paper would need to encode a 50-section sample from at least one non-Anglo-Indian penal code to rule this out. Plausibility: high — the paper itself flags this as a threat (§subsec:threats) but does not run the experiment.

3. **Agent-induced uniformity hypothesis.** Alternative: 524/524 L3 stamp coverage was achievable not because the encoding is faithful but because the L3 reviewer is the same agent class as the encoder, configured by the same author against the same checklist. A reviewer trained on different conventions, or a human reviewer cold to the project, would produce a substantially lower stamp rate. The paper would need a small inter-rater study with a non-author reviewer. Plausibility: high — admitted in §sec:limitations but not acted on.

4. **Statute-as-comment hypothesis.** Alternative: The case-law block, the holding strings, and the verbatim illustrations are not structurally meaningful — they are comments-with-schemas. If true, Yuho's expressivity advantage in the comparison matrix collapses to penalty algebra and Catala-style priority, both of which Catala already has. Plausibility: medium — §sec:limitations admits opaqueness of holdings but not of illustrations.

## 4. Missing Stakeholder Perspectives

1. **Singapore-qualified criminal-defence lawyer.** No reported review by anyone with Bar standing in Singapore. The encoded library makes claims about the SPC that a defence practitioner would have direct interest in checking. Their absence is the most consequential gap in the validation chain.

2. **Public-prosecutor / Attorney-General's Chambers perspective.** Statutes are drafted by AGC; AGC's drafters know the conventions Yuho is purporting to model. No engagement with AGC drafters is reported. The "amendment lineage" claim in particular hangs on what AGC does with `effective` clauses.

3. **Judicial perspective.** Judges interpret statutes against case-law gloss the paper concedes (§sec:limitations) is not modelled. A judge's view on whether an encoded statute is even a useful artefact for adjudication is absent. The paper does not cite Singapore Court of Appeal practice on s415, s299/s300, or general exceptions — yet treats these as canonical examples.

4. **Defendant / accused perspective.** Statute-as-executable framing privileges the system that runs the executable. Defendants' interests in textual ambiguity, contra-proferentem-style strict construction, and the rule of lenity are not engaged. A statute that can be "executed" against a defendant by a system whose author wrote both the encoding and the dispatcher is structurally adversarial to defendant interests.

5. **Legal-education / law-school perspective.** Yuho is plausibly useful as a teaching tool, but no instructor or curriculum lead has tested it. The Mermaid output is described as "useful for teaching" without evidence of pedagogical use.

6. **Comparative-law / pluralist-legal-systems scholar.** The "Anglo-Indian penal-code family" framing collapses substantial doctrinal divergence between SPC, IPC, PPC, and the Malaysian Penal Code. A comparative-law scholar would push back on treating these as a single grammar surface.

## 5. Observations (Non-Defects)

- §sec:limitations is unusually thorough and does flag the C-1 circularity, the cross-jurisdiction unverified portability, the verification-scope calibration, and the diagnostic-precision gap. The hedging is consistent and honest within that section. The defect is that the disclaimers do not propagate up into the abstract, intro, and conclusion where the same numbers are foregrounded without qualification.
- The paper commits to artefact availability (§sec:conclusion) and embeds the build pipeline that injects coverage statistics — a good open-science posture.
- The borrowings from Catala (priority semantics), lam4 (IS_INFRINGED), LexScript (Tarjan-SCC) are credited explicitly; novelty claims are scoped to the structural primitives Yuho-alone offers.
- The "What this paper is not" paragraph in §sec:intro is honest about the L3 stamp not being legal advice. This is a constructive epistemic move.
- gap_frequency.json being committed alongside the paper is good practice; it is what makes the [M-9] iterative-grammar challenge checkable.

## 6. Recommendation

- **Decision**: Major Revision
- **Confidence**: 4
- **Critical-issue count**: 3 (C-1, C-2, C-3)
- **Rationale**: The paper documents a substantial engineering artefact and is unusually honest in §sec:limitations about its own circularity and scope. The defect is rhetorical asymmetry: the disclaimers in §sec:limitations directly undercut the headline numbers in the abstract, intro, and conclusion, and the paper trades on the undisclosed-strength reading of those numbers. The three critical issues — circular L3 validation, frame-mismatch on "machine-checkable," and unmeasured fidelity-diagnostic precision — each block Accept individually. C-3 in particular ("punch list before submission") is fixable in a week and should be fixed before any resubmission. The major issues (post-hoc gap trimming, cherry-picked worked example, cherry-picked comparison matrix, conflated throughput numbers, scope-overreach on verification) are individually tractable but collectively shift the paper from "research finding" to "engineering case study," which is the honest framing. With those rewrites, the paper has a real contribution; without them, it overclaims.
