# Reviewer 1 Report — Methodology

**Reviewer**: Empirical SE measurement methodologist
**Manuscript**: Yuho: A DSL for the Singapore Penal Code as Executable Statute

## 1. Summary

The paper is a system-artefact contribution centred on three measurement claims: (a) 524/524 sections covered at L1+L2+L3, (b) a 14-item grammar-gap catalogue with crisp resolution status, and (c) a fidelity-diagnostic warning surface (98 / 48 / 2 / 208 hits) plus a 1-day median encoding-to-L3 throughput. The measurement infrastructure is partially reproducible (`scripts/paper_methodology.py`, `scripts/coverage_report.py`, `make stats`) and the JSON drops in `paper/methodology/` are commendably present. However the empirical claims rest on a measurement design with three first-order weaknesses: (i) the L3 stamp is self-administered (encoder = reviewer = stamper), (ii) diagnostic precision is explicitly unmeasured by the authors' own admission, and (iii) the headline throughput number measures git-commit calendar lag, not encoding effort. None of these are fatal in isolation, but together they materially weaken the strongest empirical-looking claims (the 100/100/100% coverage table). The paper acknowledges all three to varying degrees; the question for review is whether the acknowledgement is sufficient or whether the headline numbers should be retracted/qualified before submission.

## 2. Methodological Strengths

1. **Stat pipeline is automated and deterministic.** `Makefile` target `make stats` regenerates `stats.tex` from `library/penal_code/_coverage/coverage.json` via `scripts/gen_stats.py`, and `scripts/paper_methodology.py` regenerates `methodology/methodology.tex` plus three JSON drops. The numbers in the paper trace mechanically to source data — this is rare and good.
2. **Raw JSON artefacts are committed.** `paper/methodology/{fidelity_hits,throughput,gap_frequency}.json` are in-repo, with sample evidence (10 sections per check), enabling independent spot-audit without re-running the pipeline. The `fidelity_hits.json` keeps per-section evidence (canonical vs encoded illustration counts, or-vs-and counts) which an external reviewer can immediately sanity-check against SSO.
3. **Tier ladder is operationally well-defined.** L1 (parse), L2 (build + lint + fidelity diagnostics), L3 (11-point checklist + stamp in `metadata.toml [verification].last_verified`) — each tier has a mechanical check or a stamp file. The stamp is locatable in source.
4. **Gap catalogue is granular and post-mortem-classified.** 14 gaps cross-cut by resolution type (fixed / lint / not-a-gap / deferred) with linked artefacts; the distinction between grammar-bug and fidelity-issue-masquerading-as-grammar (G4, G11) is methodologically the right framing.
5. **Threats-to-validity section exists and self-flags the worst issues.** §subsec:threats names the encoder=reviewer problem, the diagnostic-precision gap, and the encoding-to-stamp lag distortion. Authors are not hiding these.

## 3. Methodological Weaknesses

1. **Self-administered L3 stamp + 100% pass rate is a worst-case combination.** The stamp criterion is "the encoder believes the encoding is faithful, and the mechanical checklist did not flag a fidelity issue" (limitations.tex L63-65). When the rater is the encoder, the rater's tooling is built by the encoder, the rater's checklist is authored by the encoder, and 524/524 stamps pass — the 100% figure carries near-zero independent signal about fidelity. This needs to be either (a) backed by an external-reviewer sample or (b) rebadged so the headline is not "100% L3" but "100% self-stamped".
2. **Diagnostic hit counts reported without precision/recall.** evaluation.tex L122 explicitly states the 30-warning-per-check spot-rating is "on the punch list before submission". The 98/48/2/208 numbers in §subsec:fidelity_eval are warning surface counts, not fidelity-error counts. With G11 precision admittedly unknown ("notably lower precision because it ignores syntactic role of every 'or'"), the 208 figure could be 80% noise or 80% signal — the paper does not let the reader distinguish.
3. **Throughput median is git-timestamp lag, not work.** `throughput.json` shows daily encoding counts of `[2026-04-24, 499]` — i.e., 95% of encodings were committed on a single day, the day before "today" in the artefact. Median 1 day / p95 1 day is a property of the dispatcher run, not of the DSL's encoding ergonomics. The threats paragraph (evaluation.tex L252-259) acknowledges this but the headline number still appears in the abstract-equivalent prose; it should not.
4. **Internal inconsistency: 23% vs 100% L3 coverage.** limitations.tex L69 says "The 23% L3 coverage figure is honest in this respect" — but stats.tex / coverage_report.py emit `\statLThreePass{524}` and the prose in §subsec:coverage_eval claims `\statLThreePass/\statRawSections{} (100%)`. Either the limitations text is stale or the stats pipeline is. This is a hard correctness bug for the paper, not a stylistic one.
5. **No statistical reporting at all.** No confidence intervals, no sample-size justification for the 30-warning planned spot-check, no precision/recall, no inter-rater agreement (because there is only one rater), no kappa, no bootstrap on the 1.67-day mean throughput. The paper reads as a pure descriptive statistics report, which is acceptable for an arXiv preprint of a system-artefact paper, but only if the descriptive numbers are not over-claimed (and several are — see §3.1, §3.3 above).

## 4. Specific Methodological Concerns

1. **L3 stamp validity (limitations.tex L59-72; evaluation.tex L235-241).** Claim challenged: "\statLThreePass/\statRawSections (100%) carry an L3 human-verified fidelity audit". Issue: when encoder, dispatcher author, and reviewer-agent prompt author are the same person, the stamp is closer to a self-test than an audit; the "agent acting as a structured reviewer" (implementation.tex L113) is itself prompted by the same author. **Fix**: (a) sample 30 stamped sections, have a Singapore-qualified lawyer not affiliated with the project re-run the 11-point checklist blind, and report agreement rate; or (b) demote "L3 = human-stamped" to "L3 = author-stamped" with a clear caveat in §subsec:coverage_eval and the abstract.

2. **Diagnostic precision is unmeasured (evaluation.tex L121-125, L243-250).** Claim challenged: "we expect G4 and the fabricated-cap checks to carry true-positive rate ≥ 90%, and G11 (the disjunctive-connective check) to carry a notably lower precision". Issue: this is the authors' prior, not data; reporting 98/48/2/208 as raw warning counts without an estimate of how many are true positives gives the reader no way to weight them. **Fix**: complete the spot-check before submission. With 30 warnings/check and a reasonable mix of TP/FP, a Wilson 95% CI on a binomial proportion is computable in a one-liner; report it. If precision is e.g. 0.5 for G11, the 208 number should be reported as "208 warnings, ≈104 ± 28 estimated true positives".

3. **Throughput is dispatcher-run lag, not encoding effort (evaluation.tex L176-181, L252-259; throughput.json daily_encoding_counts).** Claim challenged: "median wall-clock between first commit on a statute.yh and its first L3 stamp is 1 day; the 95th percentile is comparably tight". Issue: 499/524 (95%) of statute.yh first-commits are on a single day (2026-04-24). The 1-day median is a measurement artefact of a parallel dispatcher run. **Fix**: either drop the throughput claim entirely, or reframe it as "agent-hours per section" using the per-section codex run-time the authors already have (60-120s, evaluation.tex L257). A boxplot of per-section agent run-times across 524 sections would be a defensible empirical statement; the current 1-day median is not.

4. **Gap catalogue construction is not reproducible (design.tex §subsec:gaps; methodology.tex N/A).** Claim challenged: "Mass-encoding the Penal Code surfaced fourteen distinct grammar shortcomings". Issue: the discovery procedure is not documented — by whom were gaps named, when in the encoding timeline, with what triage protocol distinguishing "gap" from "encoder error"? The classification (genuine / not-a-gap / lint / deferred) is post-hoc, and at least three reclassifications happened (G2, G7, G10 moved categories). **Fix**: cite `docs/researcher/phase-c-gaps.md` (referenced by `paper_methodology.py:303`) in the paper, include the discovery dates in Table~\ref{tab:gaps}, and document the rule used to decide "this is the parser's job" vs "this is a linter's job". As stands the catalogue reads like a curated taxonomy rather than a discovery log.

5. **Coverage gate at L2 is circular re fidelity diagnostics (implementation.tex L202-204, evaluation.tex L107-110).** Claim challenged: "a section that triggers any of [the diagnostics] does not pass L2". Issue: this means the 524/524 L2 figure is a tautological consequence of the diagnostics having been tuned to not trigger on the corpus. Combined with the unmeasured FP rate, it is unclear whether L2=100% reflects faithful encodings or under-sensitive diagnostics. **Fix**: report both pre-tuning and post-tuning L2 numbers, or include the diagnostic thresholds and a sensitivity analysis (e.g., what happens to L2 pass-rate if the G4 check counts sub-items, which the authors say they will tighten in evaluation.tex L147-148).

6. **`min: -1` in encoding_to_stamp_days indicates a measurement bug (throughput.json L9).** A negative encoding-to-stamp delta means at least one section was L3-stamped before the statute.yh was first committed. **Fix**: investigate and document. Either timestamp ordering (rebases, cherry-picks) is corrupting the measurement, or `last_verified` is being written by hand independent of git history. Both possibilities undermine the throughput series; the paper does not flag this.

7. **SLOC table uses `wc -l`, not logical LOC (implementation.tex L221-223).** Claim challenged: "engineering counts per layer appear in Table~\ref{tab:sloc}. The numbers are wc-line counts as of the paper's writing". Issue: wc-line conflates blank lines, comments, docstrings, and code; the encoded-library `wc` figure (16,400) inflates the encoding-to-tooling ratio used as a "fair quick check on the DSL's density" (implementation.tex L253-258). Comparison across layers (CLI vs grammar vs Alloy transpiler) is not apples-to-apples because comment density varies. **Fix**: use a logical-LOC counter (e.g., `cloc` or `scc`); or explicitly disclaim that the ratio argument in L253-258 is qualitative, not quantitative.

8. **Sample-size justifications absent.** The planned 30-warning spot-check (evaluation.tex L122, L249-250) has no power calculation. For binomial precision estimation at expected 0.9 with ±0.1 width and 95% confidence, n=35 is the rule-of-thumb minimum (Wilson interval); 30 is borderline and gives wider CIs for G11 where the prior is 0.5-ish. **Fix**: justify n=30 or raise to n=50 per check; report Wilson CIs; do this *before* submission as the authors promise.

9. **Inter-rater reliability not designed in.** Even if external review is added (per concern 1), there is no plan to compute Cohen's kappa or simple agreement rate. **Fix**: pre-register the agreement metric. For an 11-point checklist, item-level kappa per checklist item is more informative than overall stamp/no-stamp agreement.

10. **No baseline / control.** The paper claims the gap-driven design produces a grammar that fits the Penal Code, but there is no comparison against a naive baseline (e.g., what fraction of sections does an unextended grammar — pre-G1 through pre-G14 — encode at L1+L2?). The pre-fix vs post-fix comparison would be a real empirical contribution. **Fix**: tag the grammar at the pre-Phase-C commit, run the L1+L2 pipeline, and report the delta. The infrastructure exists; the experiment does not.

11. **Internal inconsistency on L3 coverage figure (limitations.tex L69 vs §subsec:coverage_eval).** "23% L3 coverage" appears in limitations.tex and is contradicted by 524/524 = 100% in coverage_eval and stats.tex. **Fix**: pick a number; if the 23% is stale, delete it; if the 100% is over-claim because of self-stamping, demote it. The current state is an internal-validity defect that any careful reader will catch.

## 5. Reproducibility Assessment

A third party can re-run most numbers, but with caveats.

**What works**:
- `make stats` from `paper/Makefile` regenerates `stats.tex` deterministically from `library/penal_code/_coverage/coverage.json` via the 36-line `scripts/gen_stats.py`. Fully reproducible.
- `scripts/paper_methodology.py` (363 LOC) regenerates `methodology.tex` and the three JSON drops. Self-contained except for git history (needed for throughput) and the `_raw/act.json` SSO scrape. Reproducible by anyone with the repo at the same git revision.
- The fidelity-diagnostic re-runs in `paper_methodology.py:run_fidelity_diagnostics` are pure functions of (corpus, scrape) — no agents, no nondeterminism.

**What does not work**:
- `coverage.json` itself is generated by `scripts/coverage_report.py` (212 LOC) which I did not audit, but more importantly L3 stamps in `coverage.json` come from `metadata.toml [verification].last_verified` — these are *human-written* dates (or agent-written via the L3 dispatcher). A third party cannot re-stamp without (a) running the L3 dispatcher with the same `gpt-5.4` agent and prompt, and (b) accepting whatever the agent produces. So L3=100% is not reproducible by a third party without rerunning the agent dispatcher and trusting it.
- The 1-day throughput median depends on git timestamps. A fresh clone preserves them; a re-encoding does not. The number is reproducible as a measurement of the existing repo, not as a measurement of encoding effort.
- The 30-warning spot-check (evaluation.tex L122) has no harness committed; it does not exist yet.

**What's missing**:
- The `coverage.json` schema is undocumented in the paper. `gen_stats.py` reads `totals.{raw_sections, encoded, L1_pass, L2_pass, L3_pass}` without documenting how each is computed.
- The 11-point L3 checklist itself is referenced (`scripts/phase_d_l3_review.py`, prompt template `doc/PHASE_D_REENCODING_PROMPT.md`) but not reproduced in the paper. A reader cannot evaluate the rigor of the audit without seeing the items.
- The methodology section is one file, `methodology/methodology.tex`, that contains seven `\newcommand` definitions and no prose. The "methodology" section is effectively distributed across `paper_methodology.py` source and the inline paragraphs in `evaluation.tex`. A standalone methodology section (or appendix) consolidating discovery procedure, diagnostic definitions, stamp protocol, and sample-size plan would significantly improve reproducibility.

**Bottom line**: numerical reproducibility is unusually high for this kind of paper (B+); methodological reproducibility (could a stranger re-run *the experiment*, not just *the script*) is low (C-) because the L3 stamp depends on agent and author-defined prompts not in the paper.

## 6. Threats to Validity — Independent Take

Authors flag (in §subsec:threats and §sec:limitations): single jurisdiction; encoder=reviewer; diagnostic precision unmeasured; encoding-to-stamp lag understates real cost; common-law doctrines unmodelled; no completeness theorem.

**Additional threats not flagged**:

1. **Selection bias in the gap catalogue.** Gaps are exactly those that "mass-encoding surfaced". A gap that the encoder consistently failed to recognise as a gap (e.g., consistently mis-encoded a drafting pattern without the parser objecting) would not appear in the catalogue. There is no procedure for finding *unknown unknowns* — e.g., random-sample re-encodings by a second encoder against the same library, looking for systematic divergences.

2. **Coverage-gate moving target.** The L2 gate includes the fidelity diagnostics (implementation.tex L202). If the diagnostics had been written more aggressively, L2 pass-rate would be lower. The 524/524 L2 figure is therefore a function of diagnostic sensitivity choices, not of encoding quality alone. Authors do not separate "structurally valid" from "fidelity-clean".

3. **Tooling-confound on encoder behaviour.** §subsec:tooling_eval reports that LSP completions for `fine := unlimited` "dropped the rate of the corresponding fabricated-cap diagnostic substantially". This is plausible but unmeasured — there is no before/after comparison of the same encoder with and without the completion. The qualitative claim is consistent with a placebo.

4. **Tooling-encoding co-evolution.** The diagnostics, the grammar, the linter, and the corpus were all co-developed by the same author over the same time window. There is no held-out corpus. The 524/524 L2 figure is in-sample by construction. A 50-section Indian Penal Code holdout (mooted in §subsec:threats and §sec:limitations as future work) would be the cleanest fix, but it is not done.

5. **Agent reviewer drift.** The L3 dispatcher uses a specific agent (`gpt-5.4` at `high`, evaluation.tex L188-191). If the model is updated, deprecated, or changes behaviour, the L3 stamps cannot be re-derived even from the same prompts. The artefact is implicitly bound to a model snapshot the authors do not pin.

6. **Negative encoding-to-stamp delta (throughput.json `min: -1`).** This data point indicates a measurement-pipeline bug; a careful threats section should either explain or repair it.

7. **acmart `nonacm` template choice for arXiv.** Methodologically irrelevant, but it constrains the paper to ACM page conventions while not being submitted to ACM. This affects how much room the authors have for an appendix containing the L3 checklist, the 30-warning spot-rating, and a CI table. Worth noting because the most-needed evidence is appendix-shaped.

## 7. Statistical Reporting Audit

**Reported numerical claims**:
- Counts: 524, 524, 524, 524, 524 (raw / encoded / L1 / L2 / L3); 98 / 48 / 2 / 208 (fidelity hits); 14 (gaps); 19 (G12 migrations); 254, 650, 66, 2179 (structural counts in Table 2); 38,700 SLOC + 16,400 library; ~40 agent-hours; ~3.5 hours wall time; ~36 minutes for flag-fix sweep.
- Rates: 100% / 100% / 100% (coverage); 0.187 / 0.0916 / 0.0038 / 0.3969 (fidelity-hit rates from `fidelity_hits.json` — but these are not surfaced in the prose).
- Distribution stats: throughput median=1 day, p95=1 day, mean=1.67 days, min=-1, max=82 (only median+p95 reported in prose; the rest are in `throughput.json` only).

**What's missing or under-reported**:
- No confidence intervals on any rate. The 0.187 G4 rate over n=524 has Wilson 95% CI ≈ [0.156, 0.222]; nowhere reported.
- No standard errors or IQRs on throughput. With min=-1, max=82, mean=1.67, median=1, p95=1, the distribution is hugely right-skewed; reporting only median+p95 conceals a long tail of slow-encoded sections that may correlate with section complexity.
- No precision, recall, or F1 for any diagnostic.
- No inter-rater agreement (n_raters=1).
- No bootstrap, no permutation test, no significance claim of any kind.
- The throughput `mean=1.67` and `max=82` are in the JSON but absent from the paper. A reader sees "median 1 day, p95 1 day" and forms a wrong picture.

**What rigor an arXiv preprint actually requires**: an arXiv preprint is not held to peer-reviewed inferential standards, but the paper makes definitive claims ("100% L3", "1-day median throughput") that go beyond descriptive statistics by virtue of being singular numbers without uncertainty. The fix is small and disproportionately valuable: report Wilson CIs on the four fidelity rates, report median (IQR) on throughput, complete the n=30 spot-check with binomial CIs on precision per check. None requires new infrastructure.

## 8. Recommendation

- **Decision**: Major revision
- **Confidence**: 4 / 5
- **Per-dimension scores (0-100)**:
  - Methodological Rigor: 38
  - Reproducibility: 62
  - Internal Validity: 35
  - Statistical Reporting: 25
  - Sample Adequacy: 45

**Rationale**: The artefact is substantial and the measurement infrastructure is unusually well-engineered for a system paper — `make stats` and `paper_methodology.py` set a higher reproducibility floor than most. But the paper's headline empirical claims (100% L3, 1-day throughput, fidelity-hit counts as fidelity signal) over-promise relative to the underlying measurement design: the L3 stamp is self-administered, the throughput number measures dispatcher run-shape rather than encoding effort, the diagnostic counts have no precision estimate, and there is at least one internal-consistency defect (23% vs 100% L3) plus one data anomaly (negative throughput min) the authors do not address. None of these are fatal — the system is real, the gap catalogue is genuinely informative, and the reproducible JSON drops show good-faith effort — but the empirical framing needs to be rebuilt around what the measurement actually supports. Concretely: complete the 30-warning spot-check with Wilson CIs; recruit at least one external rater for a 30-section L3 audit and report agreement; replace the throughput claim with per-section agent run-time distribution; reconcile the 23% / 100% inconsistency; investigate the `min=-1` data point. With these in hand the paper would be a clear accept; without them the headline numbers cannot stand.
