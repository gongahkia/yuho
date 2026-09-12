# Non-scored native-toolchain risk assessment

The scored result compares only a closed semantic kernel behind a shared JSON subprocess. Both candidates used the same Python legacy projection and parser-diagnostic adapter. A kernel-level winner must not automatically become the whole-toolchain winner: editor incrementality, span fidelity and cross-platform packaging have not been built or measured.

| Route | Haskell risk | OCaml risk |
|---|---|---|
| New-language parser | A native parser could use Megaparsec/Alex or a Tree-sitter bridge. Library selection, error recovery and new-syntax grammar are untested; the spike's Parsec is only a protocol JSON parser. | Menhir/Sedlex is a plausible native route, but no grammar, recovery strategy or generated parser exists. Dune and opam were not needed or validated by the kernel spike. |
| Incremental editor | A batch parser alone does not meet the current Tree-sitter incremental-edit behavior. A retained Tree-sitter front end or explicit incremental syntax tree strategy needs measured invalid-edit recovery. | Menhir batch parsing alone has the same gap. Retaining Tree-sitter initially is safer until a native incremental strategy matches editor fixtures. |
| Formatter and spans | A future formatter must retain comments, stable IDs and UTF-8 byte/display spans across edits. The kernel only transports frozen spans. | Same requirement; Sedlex/Menhir location conversion and comment attachment are separate work. The kernel's JSON spans do not demonstrate formatter fidelity. |
| Native LSP | A Haskell LSP route would need versioned document state, cancellation, diagnostics and source mapping; no such server was prototyped. | An OCaml LSP route has the same obligations. The current Python LSP contract remains migration evidence and the initial bridge. |
| Cross-platform packaging | GHC executable links `libgmp`, `libffi`, `libm` and libc on this Fedora x86_64 host. Other Linux distributions, macOS and Windows are untested. | OCaml executable links `libm` and libc here. Cross-platform compiler/runtime availability and packaging are untested. |
| Tree-sitter coexistence | Both need one versioned subprocess protocol and explicit source-version tagging while current Tree-sitter/Python remain. Duplicate parser diagnostics and mismatched spans are integration risks. | Same; replacing Tree-sitter without meeting the architecture proposal's diagnostic and incremental-edit gates would be premature. |

The most serious whole-toolchain risk is editor incrementality and recovery. Neither kernel prototype provides evidence that its eventual parser or LSP route can replace Tree-sitter and the Python server. Keep those components behind the versioned coexistence protocol until their separate gates pass.
