# Browser WASM Playground Backend

Euclid's browser backend is a small JSON-over-stdin executable intended to be built with GHC's `wasm32-wasi` backend. The browser host runs the compiled module with a WASI preview1 shim, writes one JSON request to stdin, and reads one JSON response from stdout.

This keeps the playground backend close to the existing CLI implementation without requiring a server-side Euclid process.

## Toolchain Choice

Use `wasm32-wasi` through the current GHC wasm backend and `ghc-wasm-meta`.

The GHC user guide describes the wasm backend as a cross compiler targeting `wasm32-wasi`, with generated modules using WASI as the system-call layer. The same guide documents `wasm32-wasi-cabal` as the wrapper for Cabal projects and notes that browser execution is supported when JavaScript supplies the WASI layer:

- GHC user guide: <https://ghc.gitlab.haskell.org/ghc/doc/users_guide/wasm.html>
- `ghc-wasm-meta`: <https://gitlab.haskell.org/haskell-wasm/ghc-wasm-meta>
- Read-only GitHub mirror: <https://github.com/haskell-wasm/ghc-wasm-meta>

Alternatives were checked and not selected for this backend:

- [Asterius](https://github.com/tweag/asterius) is no longer the current route for new Euclid work; its GitHub repository is archived and read-only.
- [GHCJS and the GHC JavaScript backend](https://engineering.iog.io/2022-12-13-ghc-js-backend-merged/) target JavaScript output rather than a browser-ready WASI module. They remain possible future experiments, but they are not the shortest path to reuse `euclid check` and `euclid export` logic in a browser.

## Build Requirements

Install the GHC wasm backend from `ghc-wasm-meta`.

With Nix:

```console
$ nix shell 'gitlab:haskell-wasm/ghc-wasm-meta?host=gitlab.haskell.org'
```

Without Nix:

```console
$ curl https://gitlab.haskell.org/haskell-wasm/ghc-wasm-meta/-/raw/master/bootstrap.sh | sh
$ source ~/.ghc-wasm/env
```

Then build from a clean Euclid checkout:

```console
$ wasm32-wasi-cabal update
$ ./scripts/build-wasm-playground.sh
dist/playground/euclid-playground-wasi.wasm
```

The script runs `wasm32-wasi-cabal build exe:euclid-playground-wasi`, locates the generated module with `wasm32-wasi-cabal list-bin`, and copies it to `dist/playground/euclid-playground-wasi.wasm`.

## Host Contract

The browser host should instantiate `dist/playground/euclid-playground-wasi.wasm` with a WASI preview1 implementation such as `browser_wasi_shim`, then:

1. write a single UTF-8 JSON request to stdin
2. run the module
3. parse the UTF-8 JSON response from stdout

The helper at [`playground/browser-host.mjs`](../playground/browser-host.mjs) wraps those steps for landing-page code:

```console
$ npm install @bjorn3/browser_wasi_shim --save
```

```javascript
import { checkSource, exportSource } from "./playground/browser-host.mjs";

const wasmUrl = "/dist/playground/euclid-playground-wasi.wasm";
const source = "timeline main { start: 1, end: 2, }\nentity a : event { appears_on: main @ 1..1, }\n";

const checkResult = await checkSource(wasmUrl, source, {
  fileName: "example.euclid",
});
const svgResult = await exportSource(wasmUrl, source, {
  fileName: "example.euclid",
  format: "svg",
});
```

Check request:

```json
{
  "command": "check",
  "fileName": "example.euclid",
  "source": "timeline main { start: 1, end: 2, }\nentity a : event { appears_on: main @ 1..1, }\n"
}
```

Export request:

```json
{
  "command": "export",
  "format": "svg",
  "source": "timeline main { start: 1, end: 2, }\nentity a : event { appears_on: main @ 1..1, }\n"
}
```

Response shape:

```json
{
  "ok": true,
  "diagnostics": [],
  "output": "<svg ...>"
}
```

For `check`, `output` is `null`. For `export`, `format` defaults to `svg` and accepts `svg`, `html`, `json`, `markdown`, `md`, or `mermaid`.

## Current Limitations

- The playground API accepts one source string. It does not expand Euclid `import` statements from browser storage yet.
- The endpoint does not apply `--config`, `--theme`, or `--narrative`; it renders the whole evaluated world with default renderer options.
- The module is a WASI command-style program, so the host must provide stdin/stdout. Direct JavaScript FFI exports can be revisited if the landing page needs lower per-call overhead.
- Large HTML or SVG exports are returned as one JSON string.
