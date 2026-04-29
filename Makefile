# Top-level reproducibility Make targets. The paper has its own
# Makefile under `paper/` that handles the LaTeX build; this file
# orchestrates the empirical-claim verification.
#
# Targets:
#
#   make paper-reproduce
#       Run every load-bearing claim in the paper end-to-end:
#       parser smoke check, AKN OASIS-XSD round-trip, contrast bulk
#       run, evals fake-run, case-law differential testing. Writes
#       a one-page summary at logs/paper-reproduce-summary.txt.
#
#   make verify-coverage
#       Re-run the per-section L1+L2 sanity check against the entire
#       library (524 sections).
#
#   make verify-akn-xsd
#       Re-run AKN round-trip against the vendored OASIS XSD.
#       Requires xmllint (`apt-get install libxml2-utils` on Debian).
#
#   make verify-evals
#       Run the LLM benchmark with the deterministic FakeClient
#       (no API calls); confirms the runner + 205 fixtures work
#       end-to-end.
#
#   make verify-case-law
#       Re-run the §7.8 case-law scorers (recommend / contrast /
#       constrained). Updates the JSON results files.
#
#   make verify-bulk-contrast
#       Re-run the §7.5 Z3 bulk-contrast driver across every
#       doctrinally-related section pair.
#
# Heavy targets (paper rebuild, full corpus build, SVG rendering)
# live under paper/Makefile and scripts/.

# PYTHON defaults to `python3` (works on a clean install / Docker
# image). Override on hosts where `python3` is broken (e.g. Homebrew
# Python 3.14 with a stale pyexpat ABI):
#   make paper-reproduce PYTHON=.venv-test/bin/python
PYTHON ?= python3
# `yuho` console-script lives on PATH after `pip install -e .[dev]`;
# fall back to it when `python -m yuho` doesn't expose __main__.
YUHO ?= yuho
LOGS = logs

.PHONY: paper-reproduce \
        verify-coverage verify-akn-xsd verify-evals \
        verify-case-law verify-bulk-contrast verify-mechanisation \
        verify-structural-diff verify-runtime-tests \
        clean-reproduce

paper-reproduce: $(LOGS)
	@echo "=== paper reproducibility — verifying every empirical claim ==="
	@echo ""
	$(MAKE) verify-coverage
	$(MAKE) verify-akn-xsd
	$(MAKE) verify-runtime-tests
	$(MAKE) verify-evals
	$(MAKE) verify-case-law
	$(MAKE) verify-mechanisation
	@echo ""
	@echo "=== summary ==="
	@printf "Coverage         : %s\n" "$$(tail -n 1 $(LOGS)/coverage.log)" \
		| tee $(LOGS)/paper-reproduce-summary.txt
	@printf "AKN XSD          : %s\n" "$$(grep -E 'AKN round-trip:' $(LOGS)/akn-xsd.log | tail -n 1)" \
		| tee -a $(LOGS)/paper-reproduce-summary.txt
	@printf "Runtime tests    : %s\n" "$$(grep -E 'runtime sweep:' $(LOGS)/runtime-tests.log | tail -n 1)" \
		| tee -a $(LOGS)/paper-reproduce-summary.txt
	@printf "Evals (fake)     : %s\n" "$$(grep -E 'mean F1' $(LOGS)/evals.log | tail -n 1)" \
		| tee -a $(LOGS)/paper-reproduce-summary.txt
	@printf "Case-law (recommend) : %s\n" "$$(grep -E 'Top-1 accuracy' $(LOGS)/case-law-recommend.log | tail -n 1)" \
		| tee -a $(LOGS)/paper-reproduce-summary.txt
	@printf "Case-law (constrained): %s\n" "$$(grep -E 'consistency-rate' $(LOGS)/case-law-constrained.log | tail -n 1)" \
		| tee -a $(LOGS)/paper-reproduce-summary.txt
	@printf "Mechanisation    : %s\n" "$$(tail -n 1 $(LOGS)/mechanisation.log)" \
		| tee -a $(LOGS)/paper-reproduce-summary.txt
	@echo ""
	@echo "Wrote: $(LOGS)/paper-reproduce-summary.txt"

verify-coverage: $(LOGS)
	@echo ">>> verifying L1+L2 coverage on 524 SG PC statute.yh files…"
	@n=0; ok=0; fail=0; \
	for f in library/penal_code/*/statute.yh; do \
		n=$$((n+1)); \
		if $(YUHO) check "$$f" >/dev/null 2>&1; then \
			ok=$$((ok+1)); \
		else \
			fail=$$((fail+1)); \
			echo "  FAIL: $$f"; \
		fi; \
	done; \
	echo "$${ok}/$${n} sections pass yuho check (failures: $${fail})" \
		| tee $(LOGS)/coverage.log

verify-akn-xsd: $(LOGS)
	@echo ">>> verifying AKN OASIS-XSD round-trip (524/524)…"
	$(PYTHON) scripts/akn_roundtrip.py --xsd 2>&1 | tee $(LOGS)/akn-xsd.log

verify-evals: $(LOGS)
	@echo ">>> verifying eval-runner end-to-end (FakeClient, no API)…"
	$(PYTHON) evals/run.py --fake --no-per-fixture 2>&1 | tee $(LOGS)/evals.log

verify-case-law: $(LOGS)
	@echo ">>> verifying §7.8 case-law differential testing…"
	$(PYTHON) evals/case_law/score_recommend.py 2>&1 | tee $(LOGS)/case-law-recommend.log
	$(PYTHON) evals/case_law/score_contrast.py 2>&1 | tee $(LOGS)/case-law-contrast.log
	$(PYTHON) evals/case_law/score_contrast_constrained.py 2>&1 | tee $(LOGS)/case-law-constrained.log

verify-bulk-contrast: $(LOGS)
	@echo ">>> running §7.5 Z3 bulk-contrast across SG PC pairs…"
	$(PYTHON) scripts/bulk_contrast.py 2>&1 | tee $(LOGS)/bulk-contrast.log

verify-structural-diff: $(LOGS)
	@echo ">>> running §6.6 Lean spec ↔ Python Z3Generator structural diff (smoke fixtures, --strict)…"
	@if command -v lake >/dev/null 2>&1; then \
		$(PYTHON) scripts/verify_structural_diff.py --strict 2>&1 \
			| tee $(LOGS)/structural-diff.log; \
	else \
		echo "Structural diff: SKIPPED (Lean toolchain not on PATH)" \
			| tee $(LOGS)/structural-diff.log; \
	fi

# Full-corpus structural diff: regenerates the Lean fixture file
# from the live `library/penal_code/*/statute.yh` corpus, then runs
# the structural diff against all 524 sections. Slow (~30s including
# fixture rebuild) — keep `verify-structural-diff` as the smoke gate
# and run this on demand pre-arXiv.
verify-structural-diff-full: $(LOGS)
	@echo ">>> regenerating Lean corpus fixtures…"
	@$(PYTHON) mechanisation/scripts/generate_fixtures.py 2>&1 \
		| tee $(LOGS)/fixtures-gen.log
	@echo ">>> running full-corpus Lean spec ↔ Python Z3Generator structural diff (--strict)…"
	@if command -v lake >/dev/null 2>&1; then \
		$(PYTHON) scripts/verify_structural_diff.py --full --strict --summary-only 2>&1 \
			| tee $(LOGS)/structural-diff-full.log; \
	else \
		echo "Full structural diff: SKIPPED (Lean toolchain not on PATH)" \
			| tee $(LOGS)/structural-diff-full.log; \
	fi

verify-runtime-tests: $(LOGS)
	@echo ">>> verifying runtime-eval sweep across 90 rich test fixtures…"
	$(PYTHON) scripts/verify_runtime_tests.py 2>&1 | tee $(LOGS)/runtime-tests.log

verify-mechanisation: $(LOGS)
	@echo ">>> verifying §6.6 Lean 4 mechanisation kernel-checks…"
	@if command -v lake >/dev/null 2>&1; then \
		(cd mechanisation && lake build 2>&1 && lake build Tests 2>&1) \
			| tee $(LOGS)/mechanisation.log; \
		grep -qE 'Build completed successfully|✔' $(LOGS)/mechanisation.log \
			&& echo "Mechanisation: lake build OK (Lemmas 6.2 + 6.4 kernel-checked)" \
			   | tee -a $(LOGS)/mechanisation.log \
			|| (echo "Mechanisation: lake build FAILED — see $(LOGS)/mechanisation.log" \
			    | tee -a $(LOGS)/mechanisation.log; exit 1); \
	else \
		echo "Mechanisation: SKIPPED (Lean toolchain not on PATH; install elan to verify)" \
			| tee $(LOGS)/mechanisation.log; \
	fi

$(LOGS):
	mkdir -p $(LOGS)

clean-reproduce:
	rm -rf $(LOGS)
