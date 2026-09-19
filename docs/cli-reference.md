# CLI reference

Build at the repository root with GHC 9.8.4, then obtain the executable path with `cabal list-bin exe:yuho --offline --with-compiler=ghc-9.8.4`.

| Command | Purpose |
|---|---|
| `yuho check MODEL [--scenario SCENARIO]` | Parse, resolve and statically check a model, scenario, presumption program or case. |
| `yuho compile MODEL [--scenario SCENARIO] [--output FILE]` | Emit canonical KernelInput or case input. Output publication is atomic and refuses an existing file. |
| `yuho run MODEL [--scenario SCENARIO]` | Compile and evaluate with the in-process Haskell kernel. |
| `yuho explain MODEL [--scenario SCENARIO]` | Render a structured technical derivation and limitations. |
| `yuho diagram INPUT --view VIEW --format FORMAT --output FILE [--scenario SCENARIO]` | Emit native `svg` or semantic-graph `json`; views are `rule`, `modules`, `case`, and `trace`. |
| `yuho corpus summary|list|show|check|coverage|graph` | Query or validate the saved Singapore coverage artifact. Use `--corpus-root DIR` outside the checkout. |
| `yuho doctor [--root DIR]` | Report release, compiler, schema, corpus/module, and optional Lean availability. |
| `yuho init DIRECTORY` | Atomically create a relocatable starter project; refuses an existing destination. |
| `yuho version` | Print the research release identity. |
| `yuho release verify [--root DIR]` | Verify the offline release manifest. |

`yuho fmt` intentionally returns diagnostic `SFRL001`: the lexer does not preserve comments, so a safe complete formatter is not provided. Diagnostics go to standard error and failures return a non-zero exit status. `yuho --help` prints the compact grammar.

No production command requires a network connection, an external renderer, or a non-Haskell runtime.
