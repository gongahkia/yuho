# Yuho Makefile
# Usage: make install

.PHONY: install install-dev grammar clean test help venv

PYTHON ?= python3
VENV_DIR ?= .venv
PIP = $(VENV_DIR)/bin/pip
PYTHON_VENV = $(VENV_DIR)/bin/python

# Default target
help:
	@echo "Yuho - Legal Statute DSL"
	@echo ""
	@echo "Usage:"
	@echo "  make install      Install yuho (creates venv, builds grammar)"
	@echo "  make install-dev  Install with development dependencies"
	@echo "  make grammar      Build tree-sitter grammar only"
	@echo "  make test         Run tests"
	@echo "  make clean        Remove build artifacts and venv"
	@echo "  make venv         Create virtual environment only"
	@echo ""
	@echo "Quick start:"
	@echo "  make install"
	@echo "  source .venv/bin/activate"
	@echo "  yuho --help"

# Create virtual environment
venv:
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "Creating virtual environment..."; \
		$(PYTHON) -m venv $(VENV_DIR); \
		$(PIP) install --upgrade pip; \
	fi

# Build tree-sitter grammar
grammar: venv
	@echo "Building tree-sitter-yuho grammar..."
	@if command -v tree-sitter >/dev/null 2>&1; then \
		cd src/tree-sitter-yuho && tree-sitter generate && tree-sitter build; \
		if [ -f src/tree-sitter-yuho/libtree-sitter-yuho.dylib ]; then \
			cp src/tree-sitter-yuho/libtree-sitter-yuho.dylib src/tree-sitter-yuho/bindings/python/tree_sitter_yuho/; \
		elif [ -f src/tree-sitter-yuho/libtree-sitter-yuho.so ]; then \
			cp src/tree-sitter-yuho/libtree-sitter-yuho.so src/tree-sitter-yuho/bindings/python/tree_sitter_yuho/; \
		fi; \
	else \
		echo "tree-sitter CLI not found. Installing..."; \
		$(PYTHON_VENV) scripts/build_grammar.py; \
	fi
	@echo "Grammar built successfully"

# Install yuho
install: venv grammar
	@echo "Installing yuho..."
	$(PIP) install -e src/
	@echo ""
	@echo "Installation complete!"
	@echo "Run: source .venv/bin/activate && yuho --help"

# Install with dev dependencies
install-dev: venv grammar
	@echo "Installing yuho with dev dependencies..."
	$(PIP) install -e "src/[all]"
	@echo ""
	@echo "Installation complete!"
	@echo "Run: source .venv/bin/activate && yuho --help"

# Run tests
test: venv
	$(PYTHON_VENV) -m pytest tests/ -v

# Clean build artifacts
clean:
	rm -rf $(VENV_DIR)
	rm -rf src/tree-sitter-yuho/build
	rm -rf src/tree-sitter-yuho/src/parser.c
	rm -rf src/tree-sitter-yuho/src/tree_sitter
	rm -f src/tree-sitter-yuho/*.so src/tree-sitter-yuho/*.dylib
	rm -f src/tree-sitter-yuho/bindings/python/tree_sitter_yuho/*.so
	rm -f src/tree-sitter-yuho/bindings/python/tree_sitter_yuho/*.dylib
	rm -rf src/yuho.egg-info
	rm -rf src/yuho/__pycache__
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "Cleaned build artifacts"
