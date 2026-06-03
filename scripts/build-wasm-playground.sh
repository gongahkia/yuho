#!/usr/bin/env sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
WASM_CABAL=${WASM_CABAL:-wasm32-wasi-cabal}
OUT_DIR=${OUT_DIR:-"$ROOT_DIR/dist/playground"}
OUT_FILE=${OUT_FILE:-"$OUT_DIR/euclid-playground-wasi.wasm"}

if ! command -v "$WASM_CABAL" >/dev/null 2>&1; then
    cat >&2 <<EOF
error: $WASM_CABAL was not found on PATH.

Install the GHC wasm backend from ghc-wasm-meta, then run:

    source ~/.ghc-wasm/env
    $0
EOF
    exit 127
fi

cd "$ROOT_DIR"
"$WASM_CABAL" build exe:euclid-playground-wasi

BIN_PATH=$("$WASM_CABAL" list-bin exe:euclid-playground-wasi)
if [ ! -f "$BIN_PATH" ]; then
    echo "error: cabal did not produce an executable at $BIN_PATH" >&2
    exit 1
fi

mkdir -p "$OUT_DIR"
cp "$BIN_PATH" "$OUT_FILE"

printf '%s\n' "$OUT_FILE"
