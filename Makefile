# Top-level verification targets for the Yuho corpus and toolchain.
#
# Targets:
#
#   make verify-core
#       Run the retained project checks end-to-end:
#       parser smoke check, AKN OASIS-XSD round-trip, runtime tests,
#       structural diff, and mechanisation.
#       Writes a one-page summary at logs/verify-core-summary.txt.
#
#   make verify-coverage
#       Re-run the per-section L1+L2 sanity check against the entire
#       library (524 sections).
#
#   make verify-akn-xsd
#       Re-run AKN round-trip against the vendored OASIS XSD.
#       Requires xmllint (`apt-get install libxml2-utils` on Debian).
#
# Heavy targets (full corpus build, SVG rendering) live under scripts/.

# PYTHON defaults to `python3` (works on a clean install / Docker
# image). Override on hosts where `python3` is broken (e.g. Homebrew
# Python 3.14 with a stale pyexpat ABI):
#   make verify-all PYTHON=.venv-test/bin/python
PYTHON ?= python3
# `yuho` console-script lives on PATH after `pip install -e .[dev]`;
# fall back to it when `python -m yuho` doesn't expose __main__.
YUHO ?= yuho
LOGS = logs

.PHONY: install doctor smoke verify-all verify-core \
        verify-coverage verify-akn-xsd verify-mechanisation \
        verify-structural-diff verify-runtime-tests \
        verify-source-maps verify-mermaid-verbose \
        clean-reproduce

install:
	./install.sh --dev

doctor:
	$(YUHO) doctor

smoke: doctor
	$(YUHO) --version
	$(YUHO) init /tmp/yuho-starter --force
	$(YUHO) check library/penal_code/s415_cheating/statute.yh
	$(YUHO) lint library/penal_code/s415_cheating/statute.yh
	$(YUHO) transpile -t english library/penal_code/s415_cheating/statute.yh \
		-o /tmp/yuho-smoke-s415.txt
	$(YUHO) verify --capabilities

verify-all: verify-core

verify-core: $(LOGS)
	@echo "=== Yuho verification ==="
	@echo ""
	$(MAKE) verify-coverage
	$(MAKE) verify-akn-xsd
	$(MAKE) verify-runtime-tests
	$(MAKE) verify-source-maps
	$(MAKE) verify-structural-diff
	$(MAKE) verify-mechanisation
	@echo ""
	@echo "=== summary ==="
	@printf "Coverage         : %s\n" "$$(tail -n 1 $(LOGS)/coverage.log)" \
		| tee $(LOGS)/verify-core-summary.txt
	@printf "AKN XSD          : %s\n" "$$(grep -E 'AKN round-trip:' $(LOGS)/akn-xsd.log | tail -n 1)" \
		| tee -a $(LOGS)/verify-core-summary.txt
	@printf "Runtime tests    : %s\n" "$$(grep -E 'runtime sweep:' $(LOGS)/runtime-tests.log | tail -n 1)" \
		| tee -a $(LOGS)/verify-core-summary.txt
	@printf "Source maps      : %s\n" "$$(grep -E '^  [a-z]+:' $(LOGS)/source-maps.log | tr '\n' '; ' | sed 's/; $$//')" \
		| tee -a $(LOGS)/verify-core-summary.txt
	@printf "Structural diff  : %s\n" "$$(tail -n 1 $(LOGS)/structural-diff.log)" \
		| tee -a $(LOGS)/verify-core-summary.txt
	@printf "Mechanisation    : %s\n" "$$(tail -n 1 $(LOGS)/mechanisation.log)" \
		| tee -a $(LOGS)/verify-core-summary.txt
	@echo ""
	@echo "Wrote: $(LOGS)/verify-core-summary.txt"

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

verify-structural-diff: $(LOGS)
	@echo ">>> running Lean spec ↔ Python Z3Generator structural diff (smoke fixtures, --strict)…"
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
# and run this on demand before releases.
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

verify-source-maps: $(LOGS)
	@echo ">>> verifying source-map coverage for legal export targets…"
	$(PYTHON) scripts/verify_source_maps.py 2>&1 | tee $(LOGS)/source-maps.log

verify-mermaid-verbose: $(LOGS)
	@echo ">>> verifying verbose-shape Mermaid render across 524 sections…"
	$(PYTHON) scripts/verify_mermaid_verbose.py 2>&1 | tee $(LOGS)/mermaid-verbose.log

verify-mechanisation: $(LOGS)
	@echo ">>> verifying Lean 4 mechanisation kernel-checks…"
	@if command -v lake >/dev/null 2>&1; then \
		(cd mechanisation && lake build 2>&1 && lake build Tests 2>&1) \
			| tee $(LOGS)/mechanisation.log; \
		grep -qE 'Build completed successfully|✔' $(LOGS)/mechanisation.log \
			&& echo "Mechanisation: lake build OK" \
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
