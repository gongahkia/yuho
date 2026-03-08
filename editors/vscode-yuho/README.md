# Yuho for VS Code

Syntax highlighting for `.yh` (Yuho) files.

## Install

### From source (local)

```sh
# symlink into VS Code extensions
ln -s "$(pwd)" ~/.vscode/extensions/yuho

# restart VS Code
```

### Manual copy

```sh
cp -r editors/vscode-yuho ~/.vscode/extensions/yuho
```

Restart VS Code after either method. Open any `.yh` file to see highlighting.

## Features

- Syntax highlighting for all Yuho constructs
- Bracket matching and auto-closing
- Code folding on `{}` blocks
- Comment toggling (`//`, `/* */`, `///`)

## Highlighted constructs

- Keywords: `statute`, `match`, `case`, `fn`, `struct`, `import`, etc.
- Statute blocks: `definitions`, `elements`, `penalty`, `illustration`, `exception`, `caselaw`
- Element kinds: `actus_reus`, `mens_rea`, `circumstance`
- Element groups: `all_of`, `any_of`
- Penalty clauses: `imprisonment`, `fine`, `caning`, `death`, `supplementary`
- Types: `int`, `float`, `bool`, `string`, `money`, `percent`, `date`, `duration`
- Literals: strings, numbers, booleans (`TRUE`/`FALSE`), money (`$100`), dates, durations
- Operators: `:=`, `..`, `==`, `!=`, `&&`, `||`, `->`, arithmetic
