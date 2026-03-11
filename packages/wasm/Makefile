GRAMMAR_DIR := ../../src/tree-sitter-yuho
WASM_OUT := tree-sitter-yuho.wasm

.PHONY: build clean check-deps

check-deps:
	@command -v tree-sitter >/dev/null 2>&1 || { echo "error: tree-sitter CLI required"; exit 1; }
	@command -v emcc >/dev/null 2>&1 || { echo "error: emscripten (emcc) required for WASM build"; exit 1; }

build: check-deps
	tree-sitter build --wasm $(GRAMMAR_DIR)
	@echo "Built $(WASM_OUT)"

clean:
	rm -f $(WASM_OUT)
