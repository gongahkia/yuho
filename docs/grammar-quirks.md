# Grammar quirks

Tree-sitter parser limitations surfaced by the encoded corpus.
Documented here so authors of new `.yh` fixtures know which patterns
to avoid until the underlying grammar is restructured.

## Comment-before-struct-instantiation truncation

**Symptom.** A variable declaration of the form
`<TypeName> <var> := <TypeName> { … }` parses incorrectly when ANY
non-doc comment (`// …` or `/* … */`) appears earlier in the file
between two top-level declarations. The parser truncates the value
expression at the bare `<TypeName>` identifier and re-parses
`{ … }` as a separate anonymous-struct `expression_statement`.

**Repro.**
```yh
struct Foo { bool a, bool b }

fn check(bool x, bool y) : bool {
    match { case _ := consequence FALSE; }
}

// any inline comment here          <- triggers the bug
Foo p := Foo { a := TRUE, b := FALSE }
assert check(p.a, p.b) == TRUE      <- evaluates FALSE under the bug
```

Removing the comment (or replacing it with a blank line) recovers the
correct parse.

**Diagnosis.** The bug lives in `src/tree-sitter-yuho/grammar.js`
(the LR conflict between `struct_literal` and `variable_declaration`),
not in `src/yuho/eval/interpreter.py`. Tree-sitter's LR state machine
treats extras-bearing transitions differently from extras-free ones,
so the lookahead that would normally extend `variable_declaration`'s
optional `:= <expression>` into the trailing `struct_literal` mis-fires
when an extras token (comment) appears between declarations earlier
in the file. `prec(2, …)` and `prec.dynamic(2, …)` workarounds were
attempted on `struct_literal` but did not hold; a real fix needs
either grammar restructuring (terminator on `variable_declaration`,
or hoisting the `<TypeName> {` shape into a single token) or a
tree-sitter parser upgrade.

**Mitigation today (option (a) of TODO.md).** All non-doc `// …`
comments were stripped from
`library/penal_code/*/test_statute.yh` on 2026-04-29 (commit
`ccca70dd`); the runtime sweep
`scripts/verify_runtime_tests.py` (wired into
`make verify-runtime-tests` and `make paper-reproduce`) gates on
all 90 rich tests passing assertion eval. New fixtures should
follow the same convention until the grammar restructure lands.

**Tracked in:** `TODO.md` — *Hardening / Grammar restructure*.

## Authoring guidance

* Do **not** put `// …` or `/* … */` comments between top-level
  declarations in a file that contains struct-literal variable
  declarations of the form `<TypeName> <var> := <TypeName> { … }`.
* Doc comments `/// …` are safe — they attach to declarations as a
  distinct token and don't trip the LR conflict.
* Comments at the very top of the file (line 1) are safe — the parser
  hasn't entered the conflicted state yet.
* Inline mid-line block comments are safe — the breaking case is
  comment-as-its-own-line between two declarations.
* If a comment is unavoidable for human readability, place it
  **inside** the relevant declaration body (e.g. inside a
  `match { … }` block) rather than between declarations.

## CI integration

`make verify-runtime-tests` runs the runtime sweep
(`scripts/verify_runtime_tests.py`) across every rich
`test_statute.yh`. It fails CI on any assertion-eval failure or
interpreter error, so a future regression of the comment pattern
surfaces immediately. The sweep is also part of `make
paper-reproduce`, so the headline reproducibility run reports the
runtime-test result alongside coverage / AKN XSD / mechanisation.
