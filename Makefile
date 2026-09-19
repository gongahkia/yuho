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
	$(CABAL) v2-test yuho-test --offline -j1 --with-compiler=$(GHC) --test-show-details=direct

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
