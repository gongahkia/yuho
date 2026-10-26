SHELL := bash
.SHELLFLAGS := -euo pipefail -c
.DELETE_ON_ERROR:

GHC ?= ghc-9.8.4
CABAL ?= cabal
PYTHON ?= python3
YUHO := $(shell $(CABAL) list-bin exe:yuho --offline --with-compiler=$(GHC) 2>/dev/null)
KERNEL := $(shell $(CABAL) list-bin exe:yuho-kernel --offline --with-compiler=$(GHC) 2>/dev/null)
BUNDLE := $(shell $(CABAL) list-bin exe:yuho-model-bundle --offline --with-compiler=$(GHC) 2>/dev/null)

.PHONY: build test protocols conformance lean corpus docs release-verify verify

build:
	$(CABAL) v2-build all --offline -j1 --with-compiler=$(GHC)

test: build
	$(CABAL) v2-test yuho-test yuho-sdk-test --offline -j1 --with-compiler=$(GHC) --test-show-details=direct
	$(PYTHON) test/compiler_inspection.py $(YUHO)
	$(PYTHON) test/compiler_integrity.py $(YUHO)
	$(PYTHON) test/source_composition.py $(YUHO)
	$(PYTHON) test/machine_workbench.py $(YUHO)
	$(PYTHON) test/tranche04.py $(YUHO)
	$(PYTHON) test/typed_case_identity.py $(YUHO)
	$(PYTHON) test/checked_dependencies.py $(YUHO)
	$(PYTHON) test/dependency_native.py $(YUHO)
	$(PYTHON) test/dependency_integrity.py $(YUHO)
	$(PYTHON) test/dependency_generated_identity.py $(YUHO)
	$(PYTHON) test/dependency_condition_admission.py $(YUHO)
	$(PYTHON) test/scoped_definitions.py $(YUHO)
	$(PYTHON) test/import_diagnostics.py $(YUHO)
	$(PYTHON) test/import_duplicates.py $(YUHO)
	$(PYTHON) test/quantitative.py $(YUHO)
	$(PYTHON) test/provenance.py $(YUHO)

protocols: build
	$(PYTHON) test/protocol.py $(KERNEL)
	$(PYTHON) test/exception_protocol.py $(KERNEL)
	$(PYTHON) test/typed_protocol.py $(KERNEL)
	$(PYTHON) test/penalty_protocol.py $(KERNEL)
	$(PYTHON) test/terms_protocol.py $(KERNEL)
	$(PYTHON) test/proof_protocol.py $(KERNEL)
	$(PYTHON) test/presumption_protocol.py $(KERNEL)
	$(PYTHON) test/typed_finite_protocol.py $(YUHO) $(KERNEL)

conformance: build
	$(PYTHON) scripts/verify_core_yuho_conformance.py
	$(PYTHON) scripts/verify_core_yuho_typed_finite_conformance.py
	$(PYTHON) scripts/verify_core_yuho_v03_conformance.py
	$(PYTHON) scripts/verify_dependency_conformance.py
	$(PYTHON) scripts/verify_scoped_definition_conformance.py
	$(PYTHON) scripts/verify_quantitative_conformance.py
	$(PYTHON) scripts/verify_provenance_conformance.py

lean:
	cd mechanisation && lake build
	$(PYTHON) scripts/verify_core_yuho_theorems.py

corpus: build
	$(PYTHON) scripts/generate_singapore_corpus_v03.py --check
	$(YUHO) corpus check --corpus-root .

docs:
	$(PYTHON) test/docs.py
	$(PYTHON) scripts/verify_capability_claims.py

release-verify: build
	$(PYTHON) scripts/generate_yuho_release_manifest.py --check
	$(YUHO) release verify --root .

verify: test protocols conformance lean corpus docs release-verify
	$(PYTHON) test/prior_bytes.py
	$(PYTHON) test/release_distribution.py
	$(PYTHON) test/release_notices.py
	$(PYTHON) test/rights_inventory.py
	$(PYTHON) test/reduced_sdk.py
