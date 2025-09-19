# [Lexer](./lexer), [parser](./parser), [transpiler](./transpiler) and [CLI tool](./cli)

## Yuho default implementation v3.0

| Yuho tool | Implementation | Status |
| :--- | :--- | :--- |
| Lexer | Python (Lark) | ![](https://img.shields.io/badge/status-up-brightgreen) |
| Parser | Python (Lark) | ![](https://img.shields.io/badge/status-up-brightgreen) |
| REPL | Python | ![](https://img.shields.io/badge/status-up-brightgreen) |
| CLI tool | Python (Click) | ![](https://img.shields.io/badge/status-up-brightgreen) |
| Semantic Analyzer | Python | ![](https://img.shields.io/badge/status-up-brightgreen) |
| Mermaid Transpiler | Python | ![](https://img.shields.io/badge/status-up-brightgreen) |
| Alloy Transpiler | Python | ![](https://img.shields.io/badge/status-up-brightgreen) |

## Yuho v2.0 (Legacy - Racket)

| Yuho tool | Implementation | Status |
| :--- | :--- | :--- |
| Lexer | Racket | ![](https://img.shields.io/badge/status-needs--racket-red) |
| Parser | Racket | ![](https://img.shields.io/badge/status-needs--racket-red) |
| REPL | Racket | ![](https://img.shields.io/badge/status-needs--racket-red) |
| CLI tool | Racket | ![](https://img.shields.io/badge/status-needs--racket-red) | 

## Generate the lexer and parser *(and optionally, IDE)* yourself

1. Navigate to [./grammer/main](../../grammer/main/)
2. Pick an implementation

### [YACC](https://silcnitc.github.io/yacc.html) and [Lex](https://wycwiki.readthedocs.io/en/latest/_static/compilers/lex.html)

```console
$ flex Yuho.l
$ bison -d Yuho.y
```

### [ANTLR](https://www.antlr.org/)

```console
$ antlr4 Yuho.g4
$ javac Yuho*.java
```

### [Xtext](https://eclipse.dev/Xtext/)

1. Install [Elicpse IDE](https://www.eclipse.org/downloads/)
2. Install the Xtext Plugin from Eclipse Marketplace
3. Create a new Xtext project and move `Yuho.xtext` inside
4. Generate artifacts, run the project

### [Coco/R](https://ssw.jku.at/Research/Projects/Coco/)

```console
$ CocoR Yuho.cocor
```

### [JavaCC](https://javacc.github.io/javacc/)

```console
$ javacc Yuho.jj
```

### [PEG.js](https://github.com/pegjs/pegjs)

```console
$ pegjs Yuho.pegjs
```

### [Ragel](http://www.colm.net/open-source/ragel/)

```console
$ ragel -C -G2 Yuho.rl
```

### [Lark](https://github.com/lark-parser/lark)

1. Create a simple Python script with the following as a base template

```py
from lark import Lark, Transformer, v_args

class MyParser:

    def __init__(self):
        self.parser = Lark(open('Yuho.lark').read(), parser='lalr', start='start_rule')

    def parse(self, text):
        return self.parser.parse(text)

class MyTransformer(Transformer):
    def start_rule(self, items):
        return items

if __name__ == "__main__":
    parser = MyParser()
    text = "example input"
    parse_tree = parser.parse(text)
    print(parse_tree)
```

2. Run the following commands

```console
$ pip3 install lark-parser
$ lark -o output_file.py Yuho.lark
```

### [Tcllib](https://core.tcl-lang.org/tcllib/doc/tcllib-1-18/embedded/www/tcllib/files/apps/pt.html)

```console
$ teacup install tcllib
$ tclsh script_name.tcl
```
