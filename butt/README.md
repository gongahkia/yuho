# Lexer and token-tree reader (T1)

Design documents are in `docs/`. This tree implements tranche T1: the fixed
lexer and token-tree reader of `docs/architecture.md` §2.1, plus a
diagnostic CLI. Implementation decisions are recorded in
`docs/design-decisions.md` §6.

## Build and test

Requires opam. The toolchain (OCaml 5.5.2, Dune) lives in a
repository-local switch:

```sh
opam switch create . ocaml-base-compiler.5.5.2 --no-install
opam install . --deps-only --with-test
opam exec -- dune build
opam exec -- dune test           # unit (reduced stack), stack-safety and CLI tests
opam exec -- dune build @stress  # exhaustive and large-input checks, several minutes
```

## CLI

```sh
opam exec -- dune exec lexdump -- tokens [--trivia] FILE
opam exec -- dune exec lexdump -- trees FILE
opam exec -- dune exec lexdump -- check FILE
```

Dumps go to stdout and diagnostics to stderr. Exit codes: 0 success
(warnings allowed), 1 lexical or delimiter error, 2 usage error, 3 input
could not be read.

## Layout

- `src/` library `front`: `Span`, `Source`, `Escape`, `Diagnostic`, `Token`,
  `Lexer`, `Grammar_env`, `Reader`, `Dump`
- `bin/lexdump.ml` CLI
- `test/unit/` unit, regression, oracle and fixed-seed generated tests
  (`test_front`), and stack-safety tests (`test_stack`)
- `test/cli.t/` CLI tests (Dune cram)
- `test/stress/` the `@stress` target
