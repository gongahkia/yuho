Expected outputs below were written by hand from docs/architecture.md §2.1
and the dump formats in src/dump.mli.

Maximal operator runs (LEX-02):

  $ printf 'a+-b x|>f a<=>b\n' > ops.src
  $ lexdump tokens ops.src
  format tokens/2 file=ops.src
  1:1 [0,1) ident "a"
  1:2 [1,3) op "+-"
  1:4 [3,4) ident "b"
  1:6 [5,6) ident "x" space
  1:7 [6,8) op "|>"
  1:9 [8,9) ident "f"
  1:11 [10,11) ident "a" space
  1:12 [11,14) op "<=>"
  1:15 [14,15) ident "b"
  2:1 [16,16) eof "" space newline

Comment priority, the lint, and trivia (LEX-10):

  $ printf 'x--y\nz\n' > comment.src
  $ lexdump tokens --trivia comment.src
  comment.src:1:2 [1,3): warning[W-LEX-COMMENT-AFTER-OPERAND]: `--` directly after an operand starts a comment; separate the characters with spaces if operators were intended
  format tokens/2 file=comment.src
  1:1 [0,1) ident "x"
    trivia line-comment [1,4) "--y"
    trivia whitespace [4,5) "\n"
  2:1 [5,6) ident "z" space newline
    trivia whitespace [6,7) "\n"
  3:1 [7,7) eof "" space newline

Literals, raw identifiers and raw regions (LEX-05, LEX-06, LEX-07):

  $ printf '3.0m 10ms 0x1Fu8 `k` #t[[ ]] ]]\n' > lits.src
  $ lexdump tokens lits.src
  format tokens/2 file=lits.src
  1:1 [0,4) float "3.0m" suffix=[3,4)
  1:6 [5,9) int "10ms" suffix=[7,9) space
  1:11 [10,16) int "0x1Fu8" hex suffix=[14,16) space
  1:18 [17,20) raw-ident "`k`" name=[18,19) space
  1:22 [21,28) raw-region "#t[[ ]]" tag=[22,23) form=long/0 content=[25,26) space
  1:30 [29,30) close "]" space
  1:31 [30,31) close "]"
  2:1 [32,32) eof "" space newline

Token trees (LEX-08):

  $ printf 'f(a, [b {c}])\n' > nest.src
  $ lexdump trees nest.src
  format trees/2 file=nest.src env=source
  1:1 [0,1) ident "f"
  group env=source 1:2 [1,2) open "("
    1:3 [2,3) ident "a"
    1:4 [3,4) punct ","
    group env=source 1:6 [5,6) open "[" space
      1:7 [6,7) ident "b"
      group env=source 1:9 [8,9) open "{" space
        1:10 [9,10) ident "c"
      end 1:11 [10,11) close "}"
    end 1:12 [11,12) close "]"
  end 1:13 [12,13) close ")"
  2:1 [14,14) eof "" space newline
  $ lexdump check nest.src
  ok: 12 tokens, 2 top-level trees

Delimiter errors report both spans:

  $ printf '(a]\n' > mismatch.src
  $ lexdump trees mismatch.src
  mismatch.src:1:3 [2,3): error[E-LEX-UNBALANCED]: mismatched closing delimiter `]`: expected `)` to close `(`
  mismatch.src:1:1 [0,1): note: `(` opened here
  [1]
  $ printf '{ x\n' > unclosed.src
  $ lexdump check unclosed.src
  unclosed.src:1:1 [0,1): error[E-LEX-UNBALANCED]: unclosed delimiter `{`
  unclosed.src:2:1 [4,4): note: end of input reached here
  [1]

A brace-form raw region closes at a brace inside a string (LEX-11). The
token dump succeeds; reading trees then finds the stray brace:

  $ printf '#json{ {"a": "}"} }\n' > raw.src
  $ lexdump tokens raw.src
  format tokens/2 file=raw.src
  1:1 [0,17) raw-region "#json{ {\"a\": \"}\"}" tag=[1,5) form=brace content=[6,16)
  1:19 [18,19) close "}" space
  2:1 [20,20) eof "" space newline
  $ lexdump check raw.src
  raw.src:1:19 [18,19): error[E-LEX-UNBALANCED]: unmatched closing delimiter `}`
  [1]

Lexical errors (LEX-01, LEX-12):

  $ printf 'a\377\n' > bad.src
  $ lexdump tokens bad.src
  bad.src:1:2 [1,2): error[E-LEX-UTF8]: invalid UTF-8: byte 0xFF does not start a well-formed sequence
  [1]
  $ printf 'x = "abc\n' > string.src
  $ lexdump tokens string.src
  string.src:1:9 [8,9): error[E-LEX-STRING]: line ending (LF) inside string literal
  string.src:1:5 [4,5): note: string starts here
  [1]
  $ printf 'x \316\273\n' > char.src
  $ lexdump check char.src
  char.src:1:3 [2,4): error[E-LEX-CHAR]: non-ASCII character outside a string, comment, or raw region
  [1]

Lone CR and control bytes are string bytes and are escaped in dumps; line
endings and control bytes outside bodies are errors (I-01, I-17):

  $ printf '"a\rb" "\000\033" "\342\200\256"\n' > ctl.src
  $ lexdump tokens ctl.src
  format tokens/2 file=ctl.src
  1:1 [0,5) string "\"a\rb\""
  1:7 [6,10) string "\"\x00\x1B\"" space
  1:12 [11,16) string "\"\u{202E}\"" space
  2:1 [17,17) eof "" space newline
  $ printf '"a\r\nb"\n' > crlf.src
  $ lexdump tokens crlf.src
  crlf.src:1:3 [2,4): error[E-LEX-STRING]: line ending (CRLF) inside string literal
  crlf.src:1:1 [0,1): note: string starts here
  [1]
  $ printf 'x\033y\n' > esc.src
  $ lexdump check esc.src
  esc.src:1:2 [1,2): error[E-LEX-CHAR]: control character U+001B is not allowed here
  [1]

Usage and input errors:

  $ lexdump
  usage: lexdump (tokens [--trivia] | trees | check) FILE
    tokens   dump the token stream (format tokens/2)
    trees    dump the token trees (format trees/2)
    check    report diagnostics only
  [2]
  $ lexdump tokens missing.src
  lexdump: cannot read input: missing.src: No such file or directory
  [3]

Host error messages are escaped, so a file name holding an ANSI sequence
cannot reach the terminal as control bytes:

  $ lexdump tokens "$(printf 'no\033[31mfile.src')"
  lexdump: cannot read input: no\x1B[31mfile.src: No such file or directory
  [3]
  $ lexdump tokens "$(printf 'no\033[31mfile.src')" 2>&1 | grep -c "$(printf '\033')"
  0
  [1]
  $ lexdump tokens "$(printf 'bidi\342\200\256.src')"
  lexdump: cannot read input: bidi\u{202E}.src: No such file or directory
  [3]

Repeated runs are byte-identical:

  $ printf -- '-- header\nlocal t = #sql{ select {x} }\nf(a+-b)  --[[ c\n]] [1.5e3]\n' > mixed.src
  $ lexdump tokens --trivia mixed.src > one.txt
  $ lexdump tokens --trivia mixed.src > two.txt
  $ cmp one.txt two.txt && echo identical
  identical
  $ lexdump trees mixed.src > one.txt
  $ lexdump trees mixed.src > two.txt
  $ cmp one.txt two.txt && echo identical
  identical
