# Grammer specification

## Generate the lexer and parser yourself

Pick any of the below implementations.

* [YACC](https://silcnitc.github.io/yacc.html)
* [Lex](https://wycwiki.readthedocs.io/en/latest/_static/compilers/lex.html)

```sh
$ flex Yuho.l
$ bison -d Yuho.y
```

* [ANTLR](https://www.antlr.org/)

```sh
$ antlr4 Yuho.g4
$ javac Yuho*.java
```

* [Coco/R](https://ssw.jku.at/Research/Projects/Coco/)

```sh
$ CocoR Yuho.cocor
```

* [JavaCC](https://javacc.github.io/javacc/)

``` sh
$ javacc Yuho.jj
```

* [PEG.js](https://github.com/pegjs/pegjs)

``` sh
$ pegjs Yuho.pegjs
```

* [Ragel](http://www.colm.net/open-source/ragel/)

``` sh
$ ragel -C -G2 Yuho.rl
```

* [Lark](https://github.com/lark-parser/lark)
* [Tcllib](https://core.tcl-lang.org/tcllib/doc/tcllib-1-18/embedded/www/tcllib/files/apps/pt.html)

## References

* [A Guide To Lex & YACC](https://arcb.csc.ncsu.edu/~mueller/codeopt/codeopt00/y_man.pdf) by Thomas Niemann
* [EBNF: A Notation to Describe Syntax](https://ics.uci.edu/~pattis/ICS-33/lectures/ebnf.pdf) by UC Irvine Donald Bren School of Information & Computer Sciences
* [Crafting Interpreters](https://craftinginterpreters.com/) by Robert Nystrom
