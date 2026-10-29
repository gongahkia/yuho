# Architecture Specification — Phase 0.1

Status: **Phase 0.1 — corrected and partially frozen.** No implementation
exists. §0.4 lists which sections are **frozen** (implementation may begin
against them) and which are **accepted but provisional** (semantics agreed,
details may still change before their tranche).

Companion documents:

- `design-decisions.md` — decision log (confirmed / proposed / unresolved),
  the Phase 0 → 0.1 change table, blocker classification, and the
  implementation-language comparison.
- `technical-risks.md` — contradictions, circular dependencies, soundness,
  grammar-conflict and hygiene risks.
- `conformance-plan.md` — conformance tests and implementation tranches.

---

## 0. Conventions

### 0.1 Placeholder names

The project has **no name and no file extension yet** (`design-decisions.md`
U-01, U-02). This document says "**L**" for the language and writes example
files without extensions. Surface syntax in examples is **illustrative**.
The lexical rules in §2.1 and the core calculus in §4.4 are **not**
illustrative; they are the frozen specification.

### 0.2 Status labels

| Tag | Meaning |
|---|---|
| **[C]** | Confirmed decision from the original brief (C1–C16 in `design-decisions.md`). |
| **[A]** | Accepted correction or refinement (Phase 0.1). Normative. |
| **[P]** | Proposed; not yet accepted. Normative only once accepted. |
| **[O]** | Open question (U-xx). |
| **[v0.1]** | A restriction of the *initial implementation* that the eventual public contract may relax. Code must not rely on it being permanent. |

### 0.3 Public vs private

- **Public semantics (normative):** §2–§7, §12, §13. This is behaviour that
  user programs and extension libraries may rely on, and from which
  conformance tests are derived.
- **Private implementation (informative):** §8. It may change without a
  language-version change.

Anything a parser function, macro, type rule or checker can *observe* is
public. That covers syntax-object structure, scope behaviour, activation
order, the elaboration API, the type representation, and diagnostic codes.
Core **terms** are *not* observable from user code (§4.2.3). Only core
**types** are.

### 0.4 Freeze status

| Area | Section | Status |
|---|---|---|
| Lexical structure and token trees | §2.1 | **Frozen** (T1) |
| Syntax-object and identifier representation | §2.6.1, §13.1 | **Frozen** (data shape); behaviour provisional until T4 |
| Core calculus, typing rules | §4.4 | **Frozen** (T2) |
| Dynamic semantics of core | §4.6 | **Frozen** (T2) |
| Primitive table contract | §13.6 | **Frozen** (T2) |
| Value restriction, phase-1 value rule | §13.5 | **Frozen** (T2) |
| Private-type authorisation | §13.4 | **Frozen** (T2) |
| Resource limits contract | §13.3 | **Frozen** for the evaluator hooks (T2); capability list provisional |
| Dispatch, registry, conflicts | §2.4, §6 | Accepted, provisional (T5) |
| Precedence | §2.5, §6.3 | Accepted, provisional (T6) |
| Hygiene behaviour, grammar environments | §2.6, §13.1–13.2 | Accepted, provisional (T4/T7) |
| Elaboration API, type-directed macros | §4.2 | Accepted, provisional (T9) |
| Module checkers | §4.3 | Accepted, provisional (T12) |

Changing a **frozen** section requires a decision entry in
`design-decisions.md` and a matching conformance-test update.

---

## 1. Scope, goals, and honest limits

### 1.1 What L is

L is a small, statically typed, imperative, expression-oriented language
with a Lua-like surface: keyword-delimited blocks, `local`, first-class
functions, lexical scoping, and a deliberately small core. Its distinctive
goal **[C]** is that users can add new syntax, macros, and type rules from
inside the language, without modifying the compiler.

L is **not** a general compiler-construction framework. It has no
user-defined lexers outside raw regions, no grammar values, no public IR,
and no replaceable core type theory.

### 1.2 What "Lua-like" does and does not mean **[A]**

L keeps the surface aesthetic (keywords, `end`-terminated blocks, `local`,
`--` comments), a small core, a small runtime, first-class closures, and
multiple-statement blocks. It does **not** keep dynamically typed tables,
metatables, implicit globals, pervasive `nil`, or Lua long strings (see
§2.1.6 for the replacement). Records, variants and arrays are typed.

### 1.3 What "extensible syntax" means here **[A]**

L supports **registered extension points** over a **fixed token vocabulary**:

1. **Fixed lexer [A]** (correction 1). Custom grammars operate over the fixed
   tokens of §2.1. Different lexical rules are available **only** inside
   explicitly delimited raw regions (§2.1.6). There is no global lexical
   extensibility.
2. **Fixed core grammar.** Users add productions to **extensible categories**
   (§2.2). Core reserved words and core forms cannot be removed or
   redefined.
3. **Deterministic dispatch, then a free production body.** A production is
   selected by its declared **dispatch pattern** (§2.4). The pattern exists
   only to make selection deterministic and conflict-checkable. After
   dispatch, the production's body may recognise any grammar it can express
   over the token stream, including categories, repetition, optional parts,
   nested groups, and bounded local backtracking (§2.4.4).
4. **Scoped, sequential activation [C][A]** (correction 5). A syntax
   declaration affects only later source in its lexical scope, plus
   importers that explicitly import it. Previously parsed source is never
   re-parsed.

What L **cannot** do:

- re-lex source with different character rules outside raw regions;
- redefine core keywords;
- give two independent libraries overlapping dispatch patterns in one scope;
- add left-recursive productions except as trailing productions (operators,
  statement continuations);
- make a type rule change the core typing judgement.

### 1.4 Originality

Every individual mechanism has precedent:

- Pratt tables per syntax category and sequential command processing: Lean 4.
- Relative precedence and enforestation: Honu and Rhombus.
- Scope sets and phases: Racket.
- Grammar-as-library and per-declaration incremental parsing: SugarJ.
- Type rules as macros, and the trusted-core concern: Turnstile/Turnstile+.
- Kernel re-checking: Lean.
- Lua-family metaprogramming: Metalua and Terra.
- Typed Lua dialects: Teal and Luau.

L's contribution, if any, is the **selection and integration**, sized for one
developer. No originality is claimed for any component.

---

## 2. Public semantics: syntax

### 2.1 Lexical structure — **Frozen** **[C][A]**

The lexer is a pure, total function `bytes → (tokens | lexical error)`. It
depends on no declaration, import, registry, or compile-time computation.

#### 2.1.1 Source text

- UTF-8. Invalid UTF-8 is lexical error `E-LEX-UTF8`.
- Whitespace is space, tab, CR, and LF. Outside strings, comments and raw
  regions, any other control character and any non-ASCII character is
  `E-LEX-CHAR` **[v0.1]**. Inside those bodies every Unicode scalar value is
  permitted, including NUL and other control characters; strings
  additionally exclude line ends (§2.1.3) (R-47). Unicode identifiers are
  deferred (U-21).
- Line ends are LF or CRLF. A lone CR is whitespace, not a line end (R-48).

#### 2.1.2 Comments

- `--` starts a line comment, except inside strings and raw regions. This
  rule takes **priority over operator runs**: an operator run stops before
  `--` (§12).
- `--[` `=`ⁿ `[` … `]` `=`ⁿ `]` is a long comment (Lua style). It does not
  nest. Unterminated is `E-LEX-COMMENT`.

#### 2.1.3 Tokens

Every token carries `kind`, `text` (exact source slice), `span` (file, byte
start, byte end), `space_before: Bool`, and `newline_before: Bool`.

| Kind | Rule |
|---|---|
| `ident` | `[A-Za-z_][A-Za-z0-9_]*` |
| `raw-ident` | `` ` `` ident `` ` `` (backticks); never matches a literal dispatch atom |
| `int` | decimal `[0-9][0-9_]*` or hex `0x[0-9A-Fa-f_]+`, optional **suffix** |
| `float` | `digits . digits [exponent]` or `digits exponent`; exponent `[eE][+-]?digits`; optional **suffix**. A `.` belongs to a number only if a digit follows it. |
| `string` | `"…"` with escapes `\n \t \r \\ \" \0 \u{hex}`; no raw line ends (LF, or CRLF); a lone CR is an ordinary string byte (R-48); optional suffix not allowed |
| `op` | maximal run of operator characters (§2.1.4) |
| `punct` | one of `,` `;` |
| `open` / `close` | `(` `)` `[` `]` `{` `}` |
| `raw-region` | §2.1.6 |
| `eof` | end of input |

**Literal suffix:** an `ident` immediately adjacent (no whitespace) after a
numeric literal is part of the literal token, e.g. `3.0m`, `10ms`. An exponent
takes priority: `1e5` is a float, `3em` is `3` with suffix `em`. Hex digits
take priority: a suffix after a hex literal must start with a non-hex
letter.

There are **no keywords in the lexer**. Reserved words are recognised by the
core parser by text (§2.3.1).

#### 2.1.4 Operator runs

Operator characters: `+ - * / % ^ < > = ~ ! & | ? @ $ # : .`

An `op` token is the **maximal** run of operator characters, with two
exceptions:

1. the run ends before `--` (comment priority);
2. the run ends before a `#` that starts a raw region (§2.1.6).

Declaring an operator never changes tokenization (**stable operator
tokenization [C]**). `a<-b` is always `a` `<-` `b`. `a.b` is `a` `.` `b`.
`1..2` is `1` `..` `2`.

#### 2.1.5 Token trees

The reader groups tokens into trees over the fixed pairs `()`, `[]`, `{}`.
A mismatch or unclosed delimiter is `E-LEX-UNBALANCED`, reported with both
spans. Users cannot add tree delimiters. Keyword-delimited blocks
(`do … end`) are not trees; the core parser handles them.

#### 2.1.6 Raw regions

```
#tag{ … }                 -- brace form
#tag[=ⁿ[ … ]=ⁿ]           -- long-bracket form, n ≥ 0
```

A raw region starts at `#` immediately followed (with no whitespace) by an
`ident` (the tag), immediately followed by `{`, or by `[` `=`ⁿ `[`.

- **Brace form:** contents end at the `}` that balances the opening `{`,
  counting **only** `{` and `}` bytes. Strings, comments and escapes inside
  are **not** recognised. So `#json{ {"a": "}"} }` closes early, by design.
- **Long-bracket form:** contents end at the first `]` `=`ⁿ `]` with the
  same `n`. Nothing inside is interpreted.
- The token carries the tag, the raw content bytes, and a byte-exact span
  for the content, so every interior byte maps to its source position.
- Unterminated is `E-LEX-RAW`.

`#t` not followed by an opener is the operator `#` followed by ident `t`.

### 2.2 Syntax categories **[C][A]**

A **category** is a named nonterminal with a dispatch discipline. Categories
are **declarations, not values** **[A]**. A parser function refers to a
category by a static name. Phase-1 code cannot create, enumerate, or mutate
categories or registries at run time (§8.4).

| Category | Discipline | Leading table | Trailing table |
|---|---|---|---|
| `decl` | sequence item | yes | — |
| `stmt` | sequence item | yes | **statement continuations** (after an expression statement) |
| `expr` | Pratt | yes (atoms, prefix forms) | yes (infix, postfix, mixfix-trailing) |
| `type` | Pratt | yes | yes |
| `pattern` | Pratt | yes | yes |
| `literal-suffix` | keyed by suffix text | — | — |
| `sublanguage` | keyed by raw-region tag | — | — |

Users may declare new categories with the `sequence` or `pratt` discipline.
A new category is reachable only from a production that explicitly parses
it. Each category `K` has a phase-1 type `Syntax[K]`.

### 2.3 Fixed core surface grammar

#### 2.3.1 Reserved words **[A]**

```
def meta import export syntax macro category precedence infix prefix postfix
rule checker boundary trust shadowing requires local fun case of do end
quote tokens true false type record enum opaque
```

Reserved words cannot be claimed (§2.4.6) and cannot be used as identifiers
except via `raw-ident`. **Contextual words** (`at`, `dispatch`, `typed`, `new`,
`core`, `checked`, `assumed`, `array`) have meaning only in specific positions
of core declaration forms. Everywhere else they are ordinary identifiers. `if`, `then`, `else`, `while`, `for`, `return` and
`match` are **not** reserved; the prelude claims them.

#### 2.3.2 Core forms

- `decl`: `def`, `meta def`, `type … = record/enum/new`, `import`,
  `meta import`, `export`, `syntax`, `macro`, `rule`, `infix`/`prefix`/`postfix`,
  `category`, `precedence array`, `checker`, `boundary`.
- `stmt`: `local x [: T] = e`, expression statement, `do … end`.
- `expr`: literals, identifiers, `f(args)`, `fun (params) … end`, `e.field`,
  `N{ f = e, … }`, `case e of … end`, `( e )`, `quote[K]{…}`, `tokens{…}`.
- Macro invocation without declared syntax: `name!(…)`, valid in `expr`,
  `stmt` and `decl` positions.

Blocks are parsed **sequentially**. Each item is parsed with the registry
active at that item (§5). Newlines are insignificant, except that a trailing
call `(` or index `[` is not accepted when `newline_before` is set. This
avoids Lua's `a = b\n(f)(x)` ambiguity.

#### 2.3.3 Statement continuations **[A]**

After the sequence parser parses an expression statement `e`, it consults
the `stmt` **trailing table**. A continuation keyed by `=` (Lua assignment),
`:=`, `+=` and so on receives `e` as its left operand. This gives Lua
assignment `a.b = c` and similar identifier-first statements without
identifier-first dispatch patterns. A token may not be both a `stmt`
continuation key and an `expr` trailing key in the same scope (§6.1).

### 2.4 Syntax declarations and dispatch **[C][A]**

#### 2.4.1 Two forms, one mechanism

**Declarative form:**

```
syntax stmt "unless" cond:expr "do" body:block "end" => Unless
```

**Procedural form**, a phase-1 parser function:

```
meta def parse_unless(p: Parser): Syntax[stmt]
  p:expect("unless")
  local cond = p:parse(expr)
  p:expect("do")
  local body = p:parse_block_until(["end"])
  p:expect("end")
  return p:node(Unless, { cond = cond, body = body })
end
syntax stmt dispatch ["unless"] => parse_unless
```

The declarative form compiles to a procedural parser. Operators are the same
mechanism (§2.5.5).

#### 2.4.2 Dispatch pattern vs. production body **[A]**

A production has two parts:

- **Dispatch pattern:** a finite sequence of **atoms**, matched against
  upcoming tokens *without running user code*. Its only job is to select
  the production deterministically and allow conflict checking (§6).
- **Body:** everything after selection. It is unrestricted by the dispatch
  rules (§2.4.4).

Atoms:

- `"text"` — an `ident` or `op` token with exactly this text (never a `raw-ident`);
- `ident`, `int`, `float`, `string` — a token class (`ident` also matches
  `raw-ident`);
- `raw(tag)` — a raw region with that tag;
- `group("(")`, `group("[")`, `group("{")` — a token tree of that
  delimiter, contents unconstrained.

Category references (`expr`, `block`, …) are **not** atoms. They belong to
the body.

In the declarative form, the dispatch pattern is the **longest leading run
of atoms** before the first category reference. `"for" i:ident "=" …` has
dispatch pattern `["for", ident, "="]`. In the procedural form, it is
written explicitly.

#### 2.4.3 v0.1 restrictions vs. eventual public contract

| Rule | v0.1 | Eventual contract (target) |
|---|---|---|
| First atom of a **leading** pattern | must be a literal | may be a class atom, **if** a specificity rule against the core fallback is accepted (U-14) |
| First atom of a **trailing** pattern | must be a literal | unchanged |
| Pattern length | any finite length ≥ 1 | unchanged |
| Overlap between user entries | rejected (§6.1), including strict-prefix overlap | unchanged; possibly an explicit same-library `refines` relation (U-14) |
| User pattern vs. core fallback (ident/literal/call) | user pattern always wins when its **first** atom matches | eventual class-first patterns win only if the **whole** pattern matches |
| Body grammar | unrestricted (§2.4.4) | unchanged |
| Local backtracking in body | `p:try` within the production, under fuel | unchanged |

Longer patterns are fully supported in v0.1. `["for", ident, "="]` and
`["for", ident, "in"]` coexist because they are disjoint at position 3.

#### 2.4.4 Dispatch algorithm and body freedom

At a dispatch point for category `K` with active registry `R`:

1. Find user entries in the relevant table of `K` whose pattern matches the
   upcoming tokens. At most one can match, which §6 guarantees statically.
   A literal atom matches by text. A class atom matches by kind.
2. If one matches, select it. Otherwise use the core rules for `K`. If those
   fail, report `E-PARSE-NO-PRODUCTION`, listing active entries whose first
   atom has the same token kind.
3. Run the body with the cursor at the first token of the pattern. The body
   must consume at least the pattern (`E-SYN-PATTERN-UNCONSUMED`) and return
   `Syntax[K]`.
4. **No backtracking across productions.** If the body fails, the parse
   fails. No other entry is tried.

The body may use the **Parser API** (§8.4), a small cursor interface:

- `peek(n)`, `next()`, `at(text)`, `expect(text)`;
- `parse(K)` and `parse(K, above = level)` / `parse(K, at_or_above = level)`;
- `parse_group(group, K)`, `parse_block_until(texts)`;
- `try(f)`, which restores the cursor on failure but only *within this
  production's tokens*, charged to fuel;
- `node`, `error`.

Ambiguity *inside* a body is the author's responsibility, the same as for
any hand-written parser. The declarative compiler rejects bodies whose
optional or repeated parts are not LL(1)-distinguishable by literals
(`E-SYN-PATTERN-AMBIGUOUS`) and suggests the procedural form.

#### 2.4.5 Pratt integration

Pratt categories keep leading and trailing tables. A trailing body receives
the left operand. Binding is controlled by **levels** (§2.5) passed to
`parse(K, above = L)`, not by integers.

#### 2.4.6 Keyword claiming **[A]**

A leading pattern whose first atom is an identifier-shaped literal
(`"unless"`) **claims** that text in category `K` within the scope where the
entry is active. At a `K` dispatch point, the identifier `unless` then
selects the production. Elsewhere (e.g. after `.`, or as a `ident` atom
inside another pattern) it is still an identifier. `` `unless` `` is always
the identifier. Claiming a word that is bound as a local in scope is warning
`W-SYN-CLAIM-SHADOWS`.

### 2.5 Operators and precedence **[C][A]**

#### 2.5.1 Model: ordered arrays generating a transitive partial order

Correction 3 and decision C11 are realised with **one mechanism: ordered
precedence arrays**.

- A **level** is a named precedence class with an associativity: `left`,
  `right` or `none`. Its identity is its origin (module, array, name).
- A **precedence array** is an ordered list, loosest first. Each entry is
  either a **new level** declared inline or a **reference** to an existing
  level:
  ```
  precedence array arith = [ additive : left, multiplicative : left, power : right ]
  precedence array cmp   = [ comparison : none ]
  precedence array [ cmp.comparison, arith.additive ]   -- anonymous bridging array
  ```
- Each array contributes edges `entry[i] < entry[i+1]`, read as "looser
  than".
- The **active order** in a scope is the **transitive closure** of all edges
  from arrays active in that scope. Arrays are scoped and imported exactly
  like other syntax declarations (§2.7).
- **Equal precedence** exists only by attaching operators to the **same**
  level. Two distinct levels are never "equal".
- Library defaults are the arrays exported by the prelude and by libraries.
  A **local bridging constraint** is simply an array declared in a nested
  scope. It adds edges for the rest of that scope only.

#### 2.5.2 Comparing levels

Every parse context has a level. A fresh `parse(K)` (statement start,
parenthesised expression, argument, group contents) uses the bottom context
`⊥`, which is looser than every level.

With context level `C`, when the parser has a complete left operand and sees
a trailing entry at level `T`:

| Relation | Action |
|---|---|
| `C = ⊥` | accept `T` |
| `T` tighter than `C` | accept (`T` binds inside the current operand) |
| `T` looser than `C` | stop; return the operand to the enclosing context |
| `T = C`, assoc `left` | stop |
| `T = C`, assoc `right` | accept |
| `T = C`, assoc `none` | `E-PREC-NONASSOC` |
| `T`, `C` incomparable | `E-PREC-UNRELATED`, with a fix-it to parenthesise or declare a bridging array |

- **Infix** at level `L`: the right operand is `parse(K, above = L)` for
  `left`/`none`, and `parse(K, at_or_above = L)` for `right`.
- **Prefix** at level `L`: the operand is parsed with context `L`.
- **Postfix** at level `L`: compared like infix, with no right operand.
- **Mixfix trailing** (e.g. `a ? b : c`): inner holes are parsed at `⊥`
  between their literal delimiters, and the final open hole with context
  `L`.

**Unproven claim U-P1** (§11.2): with this procedure, an expression is
accepted iff every parent–child operator pair in the resulting tree is
related as above, and the accepted tree is unique. This is believed true by
the standard Pratt argument, but it is unproven for partial orders. T6a tests
it against a brute-force reference.

#### 2.5.3 Cycle detection

Each time arrays activate (declaration, import, or bridging array), the
compiler checks that the active edge graph is **acyclic**. A cycle is
`E-PREC-CYCLE`, listing every edge on the cycle with its origin. Edges are
**never removed**. Within nested scopes the order only grows, so acyclicity
is checked incrementally. An array that lists the same level twice is
`E-PREC-DUPLICATE`.

#### 2.5.4 Overrides **[A]**

"Explicit local override" **[C]** means **shadowing an operator entry** in a
nested scope, attaching the same token to a different level:

```
do
  infix "&" at bits.bitand_tight => bitand shadowing
  …
end
```

This reuses the general shadowing rule (§6.2). There is no edge deletion.
The Phase 0 `precedence local override`, which removed edges, is withdrawn:
it made the order non-monotone and its interaction with imports was hard to
specify.

#### 2.5.5 Operators are ordinary productions **[A]**

`infix "+" at arith.additive => f` is sugar for a trailing `expr` entry with
dispatch pattern `["+"]`, level `arith.additive`, and a body that parses
the right operand at that level and builds `f`'s syntax node. Prefix,
postfix and mixfix operators are leading or trailing entries with a level.
Scoping, import, conflicts and shadowing are therefore the general rules.

#### 2.5.6 Imported operator conflicts

These follow from the general rules (§6):

- same token, same table, same category, different origins → `E-SYN-CONFLICT`
  (this includes infix vs. postfix, since both are trailing);
- prefix and infix with the same token → allowed (different tables);
- the same entry imported via two paths → no-op;
- two imports whose arrays together form a cycle → `E-PREC-CYCLE`;
- operators on incomparable levels → allowed to import, `E-PREC-UNRELATED`
  only when actually mixed without parentheses.

#### 2.5.7 Why transitive, not Rhombus-style **[A]**

| | Transitive partial order (chosen) | Rhombus non-transitive pairwise |
|---|---|---|
| User-facing form | ordered arrays (readable, decision C11) | per-operator `~stronger_than` / `~weaker_than` lists |
| Bridging two libraries | one bridging array relates whole chains | each cross pair must be declared |
| Surprise | a bridge may relate more pairs than intended (via closure) | `a<b`, `b<c`, yet `a ? c` is an error |
| Failure mode | cycles, detected at activation | inconsistent pairwise claims, detected at comparison |
| Check cost | incremental cycle check | none until use |
| Spec complexity | low | low |

Both are coherent. The transitive model is recommended because it keeps
**ordered arrays as the user-facing feature** and needs fewer declarations.
Its trade-off is that a bridge has a broader effect than its text suggests.
Diagnostics should be able to explain why two operators are related by
showing the edge path.

### 2.6 Syntax objects, quotation, and hygiene **[C][A]**

#### 2.6.1 Syntax objects — data shape **Frozen**

```
Syntax   ::= Atom(token) | Ident(name, scopes, span) | Group(delim, children, env, span)
           | Node(kind, fields, span)
Span     ::= Original(file, start, end) | Synthetic(expansion_id, parent: Span)
TokenTree ::= sequence of Atom | Ident | Group, with a root env
```

- `scopes` is a finite set of opaque scope IDs (§13.1).
- `env` is a **grammar-environment stamp** (§13.2). It is present on token
  trees created or captured at phase 1, and `Source` for user-written source.
- Spans never affect identity or resolution.

#### 2.6.2 Hygiene

Hygiene uses Racket's scope-set model (Flatt 2016), as specified in §13.1.
Capture is per identifier only: `syntax.ident_at(ctx, "name")`, or `$!name`
inside quotation. There are no unhygienic blocks.

#### 2.6.3 Quotation

- `quote[K]{ … }` is parsed as `K` **at the definition site**, with the
  registry active there, and yields `Syntax[K]`.
- `tokens{ … }` yields a `TokenTree` stamped with the definition-site
  environment (§13.2).
- Antiquotation: `$x` (category-checked), `$(e)`, `$xs...`.

#### 2.6.4 Grammar environments

Grammar environments are specified in §13.2. In summary: a token tree is
parsed with the environment it was stamped with. Spliced foreign token trees
must be whole groups. Explicit re-stamping is the escape hatch.

#### 2.6.5 Keywords match by text

Dispatch matches keyword **text**, not bindings (U-08). Visibility is still
scoped, because an entry is consulted only where it is active.

#### 2.6.6 Interpolation inside raw regions

A sublanguage parser may ask the host to parse a sub-span of a raw region.
The fixed lexer lexes that sub-span. The tokens get the **use-site** lexical
context and grammar environment, as if the user had written them outside
the region.

### 2.7 Scoping and activation **[C][A]**

- **Syntax declarations** are `syntax`, `macro`, `infix`/`prefix`/`postfix`,
  `precedence array`, `category`, `rule`, and syntax-bearing `import` items.
- In a sequence (module body or block), a declaration at item *i* is active
  for items *i+1 …* to the end of the sequence, and inactive elsewhere.
  Nothing activates retroactively.
- `export syntax X` makes entry `X` importable. Without it, entries are
  module-private.
- `import M (syntax X, …)` or `import M (syntax *)`. Value imports never
  import syntax.
- Each entry has an **origin identity** (§13.7). The same origin arriving by
  two paths is not a conflict.

---

## 3. Public semantics: macros and compile-time evaluation

### 3.1 Phases **[C][A]**

- **Phase 0** is the run time of the module. **Phase 1** is its compile
  time: parser functions, macros, type rules, checkers.
- Phase-1 code is ordinary L, checked by the same core checker and run by
  the same interpreter.
- Phase-1 code cannot reference the module's phase-0 bindings. It can build
  syntax that mentions them.
- Within one module only phases 0 and 1 exist. Macros-for-macros come from
  `meta import`.

### 3.2 Two kinds of macro **[A]**

| Kind | When invoked | Output | May emit syntax declarations |
|---|---|---|---|
| **Syntactic macro** | in **item position** (sequence item), **eagerly**, before the next item is read; elsewhere, during expansion (outside-in, left-to-right) | `Syntax[K]` / a sequence of items | only if it `requires declare_syntax`, and only in item position |
| **Type-directed macro** | during elaboration | `Elaborated` or syntax | **never** |

Phase 0 had a third kind, the declaration macro (`decl_macro`). It is
withdrawn **[A]**. Every macro in item position is head-expanded eagerly,
following the precedent of Racket's definition contexts. The only remaining
distinction is the `declare_syntax` capability.

### 3.3 Grammar-generating macros **[C][A]** (correction 5)

- A syntactic macro in item position that `requires declare_syntax` may
  return syntax declarations among its items.
- They activate at the item boundary **after** the macro's whole output, in
  the scope where the macro was used. This holds in nested blocks as well
  as at module level.
- The macro's own output cannot use the syntax it generates. Source after
  the macro use can. Earlier source is unaffected.
- **[v0.1]** Inside blocks, generated items may be syntax declarations and
  phase-0 local definitions only. They may not be `meta def`s, `import`s or
  `export`s.
- **[v0.1]** Macros may not generate `import` items anywhere. The module
  dependency graph must come from literal imports.
- A grammar-generating macro may query only **completed** top-level
  declarations (`env_query`).

Type-directed macros can never change grammar (correction 2).

### 3.4 Capabilities, limits, determinism

See §13.3 for the contract.

---

## 4. Public semantics: types

### 4.1 Overview

The core type system (§4.4) is **fixed and trusted**. Everything users write
(type annotations, custom types, rules, type-directed macros, module
checkers) is a **frontend** that elaborates to core. The core typing
judgement is never replaced (correction 4).

### 4.2 Elaboration (untrusted) **[C][A]**

The default elaborator is bidirectional, with local unification.
Elaboration order is left-to-right: function before arguments, fields in
written order. All output is re-checked by the core checker.

#### 4.2.1 Type-directed macros

The `Elab` API:

- `ctx:infer(stx)`, `ctx:check(stx, T)`;
- `ctx:expected_type()`, `ctx:unify(T1, T2)`, `ctx:resolve(T)`;
- `ctx:bind(e)`, for hygienic let-insertion;
- `ctx:lookup_rule(key, types)`;
- `ctx:error(stx, msg)`;
- `ctx:default_elab(stx)`.

Results are `Elaborated`, an **opaque** handle with a public `.type`. An
unresolved metavariable in `resolve` is `E-TYPE-UNKNOWN-YET`. There is no
postponement (U-10, OPTIONAL).

#### 4.2.2 User type extensions, graded

1. **Custom nominal types.** `type Meters = new Float` is sugar for an
   **opaque record** `Meters { value: Float }`. Privacy is enforced by the
   core (§13.4). This is a **core-guaranteed** property.
2. **Overload rules.** `rule "+" (Meters, Meters) => meters_add` adds an
   entry to the rule table (§6.4). If no rule matches, the result is
   `E-TYPE-NO-RULE` at the operator. Correctness of the chosen implementation
   is the rule author's responsibility. Core type-correctness of the result
   is guaranteed.
3. **Procedural type rules and constraints.** These are type-directed macros
   and phase-1 predicates over `Type` values. Any property they claim beyond
   core types is **advisory**.

#### 4.2.3 No public typed IR **[A]**

Core **types** are public (`Type` values that phase-1 code can inspect and
construct). Core **terms** are not: `Elaborated` is opaque. Type rules
inspect surface syntax plus the types of subterms. `--dump-core` is a
debugging aid, not an API. This keeps the core free to change in
representation and avoids a second public language.

### 4.3 Module checkers **[C][A]** (correction 4)

#### 4.3.1 What a checker is

A **module checker** is an alternative **frontend elaborator** for one
module's phase-0 items.

- It is a phase-1 library, declared with `checker X` as the first item.
- It receives each item after syntactic expansion, and may delegate to
  `ctx:default_elab`.
- It produces core terms, which the **trusted core checker always checks**.
- It may attach **extended interface** data (opaque to the core) to exports.

A checker **does not replace the typing semantics of L**. It decides which
surface programs it accepts and how it translates them. Their run-time
meaning and safety are the core's. Its own type system (refinements,
units, linearity, effects) is a **claim the checker makes**, not a
guarantee L makes.

#### 4.3.2 Guarantee split

Guaranteed by the trusted core, for every module whatever its checker, and
assuming the TCB (§7.1) is correct:

| ID | Guarantee |
|---|---|
| G1 | **Core type safety:** a core-checked program never applies a non-function, projects a missing field, matches a missing constructor, or passes a primitive an ill-typed argument. Run time can only end normally, `panic` (including declared primitive traps), exhaust a resource limit, or diverge. |
| G2 | **Memory safety** of the interpreter (no dangling references). |
| G3 | **Nominal privacy:** values of an opaque type are constructed, projected and matched only by core items of the defining module (§13.4). |
| G4 | **Phase separation:** phase-1 code never observes phase-0 values of the module being compiled. |
| G5 | **Capability confinement** of phase-1 code (§13.3); this is build integrity, not type safety. |
| G6 | **Exhaustive `case`** at run time. |

**Not** guaranteed by the core; these are the checker's (or rule author's)
responsibility:

| Property | Responsibility |
|---|---|
| Soundness of the checker's own type system (refinements, units beyond nominal types, linearity, effects, information flow, termination) | checker author |
| That elaboration preserves intended meaning | checker / macro / rule author |
| That extended-interface facts are true | exporting checker |
| That boundary guards correctly implement the claimed property | exporting checker (testable, not verified) |
| Hygiene correctness of generated code | the expander (untrusted) |

A checked core program is **core-safe**. It is **not** thereby sound with
respect to the checker's type system. Passing the core check is evidence of
G1–G6 only.

#### 4.3.3 Interoperability boundary

Every module has a **core interface** (names and core types), which is the
only interface the core relies on. A checker may add an **extended
interface** keyed by checker identity and version.

Each export whose extended type is stronger than its core type **must**
declare a boundary mode. Omitting it is `E-CHK-BOUNDARY-REQUIRED`.

| Mode | Meaning | v0.1 limits |
|---|---|---|
| `boundary core` | export claims nothing beyond the core type | — |
| `boundary checked` | the checker emits ordinary core **guard code**: a wrapper exported under the public name validates the claimed properties of inputs at run time and panics on violation; internal callers use the unwrapped function | **first-order** functions whose claimed parameter properties are run-time decidable |
| `boundary assumed` | no guards; importers that do not `trust X` get `W-CHK-ASSUMED` at each use | any |

Importer rules:

- An importer with checker `Y` sees only core types, unless it writes
  `import M (…) trust X` **and** `Y` declares that it reads `X`'s extended
  interface format.
- Values flowing *out of* an `X` module carry `X`'s claims only for
  importers that trust `X`.

Alternate checkers need **no new core primitives** **[A]**: guards are
ordinary core code, and extended interfaces are data the core ignores. A
gradual checker with a `Dyn` type would need new core features and is
OPTIONAL (U-11).

### 4.4 Core calculus — **Frozen** **[A]**

The core is **fully annotated**. Checking is syntax-directed, with no
inference and no metavariables.

**Types**

```
T ::= Unit | Bool | Int | Float | String
    | (T1, …, Tn) -> T
    | N[T1, …, Tn]                 -- nominal record/enum, identified by stamp (§13.4)
    | Array[T] | Ref[T]
    | α
σ ::= T | forall α1 … αn. T        -- only on def declarations (rank-1)
```

Phase-1 builtin types (`Syntax[K]`, `TokenTree`, `Type`, `Elaborated`,
`Parser`, `Elab`) are ordinary nominal opaque types owned by a builtin
module. The checker has **no special rules** for them. Their operations are
primitives (§13.6).

**Terms**

```
e ::= x | x[T1…Tn]                      -- variable; instantiation of a polymorphic def
    | () | true | false | int | float | string
    | fun (x1: T1, …, xn: Tn): T => e
    | e(e1, …, en)
    | let x: T = e1 in e2
    | letrec f1: T1 = fun…, …, fn: Tn = fun… in e
    | N[T…]{ f1 = e1, …, fk = ek }      -- record construction
    | e.f                                -- projection
    | N[T…].C(e1, …, en)                 -- enum construction
    | case e of p1 => e1 | … [| _ => e0] end   -- p ::= C(x1…xn) | true | false
    | ref(e) | !e | e1 := e2
    | seq(e1; e2)
    | label ℓ: T in e | break[T] ℓ(e)
    | loop[T] e
    | prim p[T…](e1, …, en)
    | panic[T](e)
```

**Declarations** (each belongs to exactly one module `m` and one phase `p`)

```
d ::= def x: σ = e
    | type N[α…] = record { f1: T1, … }     with visibility transparent | opaque
    | type N[α…] = enum { C1(T…), … }       with visibility transparent | opaque
```

**Typing judgement** `m, p; Δ; Γ; Λ ⊢ e : T`. Here `Δ` is the type
variables, `Γ` the variables, and `Λ` the labels.

| Form | Rule (summary) |
|---|---|
| `x` | `Γ(x) = T`, or `x` is a monomorphic def of phase `p` with type `T` |
| `x[T̄]` | `x` is a def of phase `p` with `forall ᾱ. T`, `|T̄| = |ᾱ|`, each `Ti` well-formed in `Δ`; result `T[T̄/ᾱ]` |
| literals | their base types; `()` : `Unit` |
| `fun` | body checked with `Γ, x̄:T̄` and **`Λ = ∅`** (labels do not cross functions); result `(T̄) -> T` when body : `T` |
| application | callee `(T̄) -> R`, arguments exactly `T̄` (type equality), result `R` |
| `let` | `e1 : T`; `e2` with `x:T` |
| `letrec` | every binding is a `fun` literal whose type equals its annotation; all bound in all bodies and in `e` |
| record construction | `N` is a record; `m = owner(N)` or `N` transparent; every field exactly once; field types instantiated |
| projection | `e : N[T̄]`, `N` record with field `f`; same visibility condition |
| enum construction | `N` enum with constructor `C`; visibility condition; argument types |
| `case` | scrutinee `N[T̄]` (visibility condition) or `Bool`; each constructor at most once; **exhaustive**, either all constructors or `_`; all arms the same type |
| `ref`/`!`/`:=` | `Ref[T]`; `:=` : `Unit` |
| `seq` | `e1 : Unit`; result type of `e2` |
| `label ℓ: T in e` | `e : T` under `Λ, ℓ:T` |
| `break[S] ℓ(e)` | `Λ(ℓ) = T`, `e : T`; result `S` |
| `loop[S] e` | `e : Unit`; result `S` |
| `prim p[T̄](ē)` | `p` in the primitive table, allowed at phase `p`; instantiate its scheme; argument types match |
| `panic[S](e)` | `e : String`; result `S` |
| `def x: σ = e` | if `σ = forall ᾱ. T` then **`e` must be a `fun` literal** (§13.5); check `e : T` with `Δ = ᾱ`. At **phase 1**, `e` must be a **syntactic value**: a `fun` literal, a literal, or a constructor applied to syntactic values (§13.5). |

Type equality is syntactic on stamps and arguments; for `forall`, up to
renaming. Well-formedness checks arity and bound variables. Duplicate
field, constructor or parameter names are errors.

### 4.5 Features definable as macros or library

| Surface feature | Defined as |
|---|---|
| `if/elseif/else`, `and`, `or`, `not` | syntactic macros → `case` on `Bool` |
| `while`, `break`, `continue` | macros → `label` + `loop` + `case` |
| numeric `for` | macro over `var` + `while` |
| iterator `for x in e` | type-directed macro using overload rules keyed on the iterable's type head |
| `return` | macro → `break ℓ_fn(e)`, with `ℓ_fn` installed by the `def` surface macro |
| `var`, assignment | macro over `Ref`; assignment as a `=` statement continuation |
| arithmetic and comparison operators | operator productions → type-directed macro → rule table → primitives |
| method call `obj:m(args)` | trailing production + type-directed macro |
| nested `match` | macro → flat `case` tree |
| string interpolation | sublanguage (raw region) |
| list literals, `assert`, `local function` | macros |
| units of measure | `new` type + rules + literal suffixes (Examples D, E) |
| opaque `new` types | surface sugar → single-field opaque record |

The core itself provides polymorphism, nominal types and privacy, phase
separation, modules (in the driver), and the checker.

### 4.6 Dynamic semantics of core — **Frozen**

- Call-by-value, strictly **left-to-right**: callee, then arguments; record
  fields in written order; `e1 := e2` evaluates `e1` before `e2`.
- `label ℓ in e` evaluates `e`. `break ℓ(v)` exits to the innermost dynamic
  instance of `ℓ`, which is also the lexical one, since labels do not cross
  `fun`.
- `loop e` repeats `e` until a `break` exits it.
- `panic(msg)`: at phase 0 the program aborts with the message and a nonzero
  exit status. At phase 1 it is compile error `E-META-PANIC` (§13.8).
- Primitive traps are defined per primitive (§13.6), e.g. integer overflow,
  division by zero, array bounds. Each trap is a `panic` with a fixed
  message prefix.
- **Call depth:** the interpreter enforces a maximum call depth (phase 0:
  configurable, default ≥ 10 000; phase 1: §13.3). Exceeding it is a panic
  `stack overflow`, **never** a host crash.
- `Int` is 64-bit two's complement and traps on overflow. `Float` is IEEE-754
  binary64. `String` is immutable UTF-8, with length in bytes.

---

## 5. Compiler phase boundaries **[A]** (correction 2)

### 5.1 Per-item pipeline

```
source ──lex──▶ tokens ──group──▶ token trees         (fixed; whole file; no user code)

for each sequence (module body, then nested blocks as they are reached), item by item:
   R_i  = registry active before item i
   P1  read          parse item i with R_i  (may run phase-1 parser functions)
   P2  head-expand   if item i is a macro use in item position: expand eagerly, repeat until
                     the head is not a macro; the result may be several items
   P3  activate      for each resulting syntax declaration: validate, conflict-check → R_{i+1}
   P4  expand        remaining syntactic macros (outside-in, left-to-right)
   P5  elaborate     default elaborator or module checker; type-directed macros run here
   P6  core-check    TRUSTED
   P7  commit        add to environment; phase-1 definitions become callable
after the module:
   P8  interface     core interface + extended interfaces + exported registry entries
   P9  run phase 0   when the program executes
```

### 5.2 Boundary rules

- **Lexing is a hard wall.** It is complete before any user code runs.
- **Item boundary.** `R_{i+1}` is fixed before any token of item *i+1* is
  read. If item *i* defines phase-1 code or syntax, P1–P7 for item *i*
  complete before item *i+1* is read.
- **Nested blocks.** A function body's block is a sequence. Its statements
  go through P1–P3 in order when the enclosing item is read, so block-level
  syntax declarations and grammar-generating macros affect later statements
  of that block. P4–P7 for the whole enclosing item happen afterwards.
  This is possible because phase-1 code cannot depend on the block's
  phase-0 locals.
- **Expansion ⇄ elaboration** interleave within an item. A type-directed
  macro may return syntax, which is expanded and then elaborated, but it
  cannot declare syntax.
- **Core check** sees only core terms: no syntax, registry, rules or checker
  state.

### 5.3 Same-module macros

A `meta def` at item *i* is callable by entries and macros from item *i+1*
on.

### 5.4 Separate compilation

See §13.7.

---

## 6. Conservative ambiguity detection and import semantics **[C][A]**

All checks run at **activation** (P3), independent of later source. They
may reject combinations that would never be ambiguous on real input. They
never accept two entries that could both be selected at one dispatch point.

### 6.1 Overlap

Two dispatch patterns `a1…am` and `b1…bn` **overlap** unless some position
`k ≤ min(m, n)` holds disjoint atoms:

- two literals are disjoint iff their texts differ;
- a literal and a class are disjoint iff the literal's token kind is not the
  class;
- two classes are disjoint iff they differ, with `ident` ≡ `raw-ident` for
  this purpose;
- `raw(t1)` and `raw(t2)` are disjoint iff `t1 ≠ t2`;
- `group(d1)` and `group(d2)` are disjoint iff `d1 ≠ d2`;
- a group is disjoint from every non-group atom.

If one pattern is a strict prefix of the other with no disjoint position,
they **overlap** (no longest-match rule).

**Lemma.** If all active entries in one table are pairwise non-overlapping,
at most one entry matches any token sequence. *Proof sketch:* if two match,
their atoms both match the token at each position up to the shorter length,
so no position is disjoint. This is elementary and stated for completeness.

**Cross-table rule.** A token text that is a `stmt` continuation key may not
be an `expr` trailing key in the same scope (§2.3.3).

**Keyed tables** (`literal-suffix`, `sublanguage`, overload rules) overlap
iff their keys are equal.

### 6.2 Conflict rule

When entry `E` activates into scope `S`:

1. Same origin already active → no-op.
2. Overlap with an entry active at the **same scope level** →
   `E-SYN-CONFLICT`, naming both origins and import paths.
3. Overlap with an entry from an **enclosing** scope → `E-SYN-CONFLICT`,
   unless `E` is marked `shadowing`. With the marker, the outer entry is
   hidden in `S` and its nested scopes.
4. Overlap with a **core** form or reserved word → `E-SYN-CORE`.
5. **Order independence.** The verdict does not depend on the order of
   imports or declarations within a scope. Diagnostics are ordered by
   `(origin module path, declaration index)`.

### 6.3 Precedence

See §2.5.3 and §2.5.6.

### 6.4 Overload rules

Keys are `(name, tuple of head type constructors)` with **concrete** heads
only **[v0.1]**. Equal keys from different origins are `E-RULE-CONFLICT`.
Keys containing type variables are OPTIONAL (U-12).

### 6.5 Not detected

Ambiguity inside a production body, beyond the LL(1) check for declarative
bodies.

---

## 7. Trusted type-checking boundary **[A]**

### 7.1 Trusted computing base (for G1–G4, G6)

1. The core checker (§4.4).
2. The primitive table: typings **and** implementations (§13.6).
3. The interpreter (§4.6).
4. The interface loader, which re-checks core on load in v0.1 (§13.7).
5. The driver's assignment of module identities (§13.4).

The capability gate and resource counters (§13.3) are trusted for G5.

### 7.2 Untrusted

Lexer, reader, registry, dispatch, parser functions, expander, hygiene,
elaborator, type-directed macros, rules, module checkers, and the
declarative-pattern compiler. A bug in any of these can cause wrong
rejection, bad diagnostics, or a well-typed program with the wrong meaning.
It cannot violate G1–G4 or G6.

### 7.3 Not provided

Semantic preservation; soundness of checker-defined type systems; truth of
extended interfaces; hygiene correctness; totality of compile-time code. All
are restated in §4.3.2.

---

## 8. Private implementation architecture (informative)

### 8.1 Components

| Component | Responsibility | Trusted |
|---|---|---|
| `lexer` | bytes → tokens (§2.1) | no |
| `reader` | token trees, raw regions | no |
| `registry` | persistent tables per scope: leading/trailing entries, keyed tables, precedence edges; snapshot IDs | no |
| `seqparser` | sequence loop; dispatch; P2–P3 | no |
| `pratt` | Pratt loop over levels | no |
| `patterncomp` | declarative patterns → parser functions | no |
| `syntax` | syntax objects, scopes, spans, env stamps | no |
| `expander` | macro invocation, scope operations | no |
| `elab` | default elaborator, Elab API | no |
| `core` | core AST, checker, serializer | **yes** |
| `prims` | primitive table (types + implementations, one source) | **yes** |
| `interp` | evaluator, counters, capability gate | **yes** |
| `driver` | modules, identities, interfaces, diagnostics | identity assignment only |

### 8.2 Implementation notes

- The registry is persistent, so snapshots are cheap and env stamps can
  refer to them.
- Phase-0 and phase-1 values share one representation.
- Diagnostics carry expansion chains.
- Per-item caching is a T14 optimisation and must be unobservable.
- Bytecode, if ever added, compiles core only.

### 8.3 Bootstrap

- Layer 0 of the prelude is written in **core surface syntax only**.
- Layer 1 defines `if`, `while`, `for`, `var`, operators and `match`.
- Each layer `meta import`s only lower layers.

### 8.4 Complexity review (Phase 0.1) **[A]**

| Mechanism | Decision | Reason |
|---|---|---|
| First-class grammar or category values | **Removed.** Categories and entries are declarations. Grammar is generated by macros emitting declarations. | One mechanism (declarations + declaration-emitting macros) instead of two (declarations + a grammar-value API). Registries are not mutable from phase 1. |
| Parser-combinator framework | **Not built in.** The Parser API is a small cursor interface (§2.4.4). Combinators can be an ordinary L library over it. | Keeps the compiler small. The declarative form covers common cases. |
| Public typed IR | **Removed.** `Elaborated` is opaque; core types are public, core terms are not. | Avoids freezing a second language; the core can change representation. |
| Core primitives for alternate checkers | **None.** Guards are ordinary core code; extended interfaces are opaque data. | Checkers stay outside the TCB. |
| Operators vs. other syntax | **Unified.** Operators are leading/trailing entries with a level. | Same scoping, import, conflict and shadowing rules. |
| `literal-suffix`, `sublanguage`, overload rules | **Unified** as keyed tables sharing the entry, origin, scope and conflict infrastructure. | One implementation. Overlap is key equality. |
| Declaration macro kind | **Removed.** All item-position macros are head-expanded eagerly; `declare_syntax` gates declaration output. | One macro kind for syntax, one for types. |
| Precedence override by edge deletion | **Removed.** Override is operator shadowing. | The order becomes monotone and order-independent. |
| `newtype_wrap` / `unwrap` in core | **Removed.** `new` types are single-field opaque records. | One privacy rule for records and enums. |
| Per-token registry references | **Replaced** by env stamps on phase-1 token trees and groups (§13.2). | Less data; a simpler rule. |
| User-declared keyed tables | **Not provided** (OPTIONAL). | Not needed for the stated vision. |

---

## 9. Comparison with prior systems

Sources are listed in §15. Items not re-checked against primary sources are
marked *(unverified)*.

### 9.1 Summary table

| System | Lexing | Parsing / extension point | Scope of extensions | Hygiene | Types & trust |
|---|---|---|---|---|---|
| **Lean 4** | token table; declared atoms become tokens | Pratt with leading/trailing tables per syntax category; longest match → priority → `choice` nodes resolved by the elaborator | per command, sequential; `local`/`scoped` | macro scopes; can be disabled | untrusted elaborator; small kernel re-checks |
| **Racket** | reader, replaceable per module (`#lang`, readtables) | S-expressions; macros over syntax objects | module and phase | scope sets; phases | Typed Racket as macros; contracts at typed/untyped boundaries |
| **Rhombus** | fixed shrubbery reader | enforestation interleaved with expansion; operators and macros are bindings | lexical, binding-based | scope sets | dynamic with static info |
| **Raku** | part of the grammar | grammars as classes; LTM; slangs via `augment slang` | lexically scoped | — (macros historically experimental) | gradual |
| **Metalua** | Lua lexer with extensible keywords | `gg` combinators; `-{}` splices | compiler instance / file | not hygienic by default *(unverified detail)* | dynamic |
| **SugarJ** | scannerless (SDF) | SGLR generalized parsing of composed grammars; Stratego desugaring; per-declaration incremental parsing | imported sugar libraries | rewriting, not scope sets | Java checks the output; SoundX later |
| **Turnstile** | Racket | Racket macros | Racket | Racket | type rules as macros; Turnstile+ discusses a trusted core and axioms |
| **L** | fixed; operator runs; raw regions | sequence + Pratt; deterministic dispatch patterns; free bodies | lexical, sequential, explicit import | scope sets + grammar environments | untrusted frontends; fixed core re-check |

### 9.2 Lessons adopted and rejected

The Phase 0 analysis stands, with these corrections:

- **Lean 4.** Lean's longest-match and priority rules are *deterministic*,
  and Lean defers residual ties to elaboration via `choice` nodes. L instead
  rejects overlaps at activation. Rejection is not more "correct" than
  Lean's approach. It is a different contract: earlier, simpler, and more
  restrictive.
- **Rhombus.** L adopts its "unrelated ⇒ parenthesise" rule but uses
  transitive arrays (§2.5.7). Binding-based dispatch remains a credible
  alternative (U-08).
- **SugarJ / generalized parsing.** See §9.3 for the corrected statement.

### 9.3 Parsing strategy comparison (corrected)

Two different questions must be kept apart:

1. **Ambiguity on an actual input.** A generalized parser (GLR, GLL, Earley,
   SGLR) **does** detect this: it produces more than one parse for that
   input, and can report it at that point.
2. **Ambiguity of a grammar** (does *any* input have two parses?). This is
   **undecidable** for arbitrary context-free grammars. Approximate and
   conservative detectors exist, and some grammar classes (e.g. LR(k)) are
   unambiguous by construction. No method decides it for all composed CFGs.

C6 requires conflicts to be rejected **when an extension is activated**,
before any particular input is seen. That is question 2, restricted to
whatever grammar class the design permits.

| Criterion | Pratt + deterministic dispatch (chosen) | Generalized parsing | PEG / combinators |
|---|---|---|---|
| Grammar after selection | unrestricted body | any CFG | any PEG / arbitrary code |
| Conflict check at activation | **decidable** (pattern overlap; §6.1 lemma) | undecidable in general; conservative approximations possible | none needed; ordered choice silently resolves |
| Ambiguity on an actual input | impossible at dispatch; body is the author's responsibility | detected (multiple parses) | hidden by ordered choice |
| Composition of independent extensions | rejected if overlapping; order-independent | composes; ambiguity may surface on later inputs | order-dependent |
| Implementation effort | low–moderate | high | low, but analysis is hard |
| Fit with fixed lexer and sequential activation | natural | weaker (strength is scannerless and whole-grammar) | natural |

Copper/Silver's modular determinism analysis (Schwerdfeger & Van Wyk, PLDI
2009) *(unverified details)* is the strongest known approach to guaranteed
composition for LR grammars, and is the reference point if U-14 relaxes the
rules.

**Recommendation [A]:** Pratt + sequential parsing with deterministic
dispatch patterns and unrestricted production bodies.

---

## 10. Conceptual examples

Illustrative syntax.

### Example A — custom statement syntax

```
-- module demo.unless
meta import std.syntax
syntax stmt "unless" cond:expr "do" body:block "end" => Unless
export syntax Unless

macro Unless(stx)
  case stx of Unless{ cond, body } =>
    return quote[stmt]{ if not $cond then $body end }
  end
end
```

```
-- module app
import demo.unless (syntax Unless)
def check(n: Int): Unit
  unless n > 0 do panic("non-positive") end
end
```

`if`/`not` in the quotation resolve and parse at `demo.unless`'s definition
site.

### Example B — scope isolation, sequential activation, conflicts

```
def f(): Int
  local x = 1
  do
    import demo.unless (syntax Unless)     -- active for the following statements of this block
    unless x > 0 do panic("no") end        -- OK
  end
  unless x > 0 do panic("no") end          -- E-PARSE: `unless` is an ordinary identifier here
  return x
end
```

```
import lib_a (syntax *)    -- stmt dispatch ["repeat"]
import lib_b (syntax *)    -- stmt dispatch ["repeat", int]
-- E-SYN-CONFLICT: ["repeat"] (lib_a.Repeat) is a strict prefix of ["repeat", int] (lib_b.RepeatN)
import lib_c (syntax *)    -- stmt dispatch ["repeat", group("(")]  … also conflicts with lib_a
-- lib_b and lib_c alone would coexist: disjoint at position 2.
```

### Example C — hygiene and explicit capture

```
macro swap(stx)                         -- swap!(a, b)
  case stx of MacroCall{ args = [a, b] } =>
    return quote[stmt]{ local tmp = !$a ; $a := !$b ; $b := tmp }
  end
end
-- user: local tmp = ref(1); local y = ref(2); swap!(tmp, y)   -- correct under scope sets

syntax expr "aif" cond:expr "then" body:expr "end" => Aif
macro Aif(stx)
  case stx of Aif{ cond, body } =>
    local it = syntax.ident_at(stx, "it")        -- deliberate, visible capture
    return quote[expr]{ case $cond of Some($it) => $body | None => () end }
  end
end
```

### Example D — macro-generated grammar, including in a block

```
-- module std.units
syntax decl "measure" name:ident "of" base:type "suffix" suffix:ident => Measure
export syntax Measure
macro Measure(stx) requires declare_syntax
  case stx of Measure{ name, base, suffix } =>
    return [
      quote[decl]{ type $name = new $base },
      quote[decl]{ syntax literal-suffix $suffix => $(suffix_parser(name)) },
      quote[decl]{ rule "+" ($name, $name) => $(adder(name)) },
    ]
  end
end
```

```
-- module app
import std.units (syntax Measure)
measure Meters of Float suffix m      -- item i
local d = 3.0m + 4.5m                 -- item i+1: suffix active; d : Meters

def g(): Unit
  measure Secs of Float suffix s      -- block item k: eager head-expansion
  local t = 2.0s                      -- block item k+1: active
end
local u = 1.0s                        -- E-PARSE: suffix `s` not active outside g's block
```

`Meters` is declared in `app` (the use site), so `app` may construct it
(§13.4). `3.0m` cannot appear *inside* the `measure` expansion.

### Example E — typed elaboration

```
infix "+" at arith.additive => typed plus
meta def plus(ctx: Elab, l: Syntax[expr], r: Syntax[expr]): Elaborated
  local el = ctx:infer(l)
  local er = ctx:check(r, el.type)
  case ctx:lookup_rule("+", [el.type, er.type]) of
    Some(rule) => return rule:apply(ctx, el, er)
    None       => return ctx:error(l, "no `+` for " .. show(el.type))
  end
end
```

`3.0m + 4.5m` elaborates to roughly
`meters_add(Meters{value = 3.0}, Meters{value = 4.5})` in `app`. If a buggy
rule produced `Meters + Float`, the core check (G1) would reject it.

### Example F — module checker and boundary

```
-- module geo
checker std.checkers.nonneg
export def isqrt(n: Int{>= 0}): Int{>= 0} … end   boundary checked
export def unsafe_half(n: Int{>= 0}): Int        boundary assumed
```

```
-- module app (default checker)
import geo (isqrt, unsafe_half)
isqrt(-4)          -- run time: guard panics "isqrt: n >= 0 violated"
unsafe_half(-4)    -- W-CHK-ASSUMED; no guard; core-safe, property silently unenforced
```

### Example G — precedence composition

```
-- lib pipes:  precedence array pipe = [ pipe : left ];  infix "|>" at pipe.pipe => …
-- lib cmp:    precedence array cmp  = [ comparison : none ];  infix "<=>" at cmp.comparison => …
import pipes (syntax *)
import cmp (syntax *)
local a = x |> f <=> y            -- E-PREC-UNRELATED: `|>` and `<=>` unrelated; parenthesise
do
  precedence array [ pipe.pipe, cmp.comparison ]   -- local bridge: pipe looser than comparison
  local b = x |> f <=> y          -- parses as x |> (f <=> y)
end
```

---

## 11. What remains difficult, and unproven claims

### 11.1 Difficult

1. **Grammar environments for token trees** (§13.2). The v0.1 rule is
   conservative and may be too restrictive for some macro styles.
2. **Type-directed macros without postponement** will require
   annotations.
3. **Overload rules with type variables** amount to type-class coherence
   (OPTIONAL).
4. **Diagnostics** across parser, macro and type layers.
5. **Tooling** must run phase-1 code to parse.
6. **Specifying** the Elab API and expansion order precisely.
7. **Scope for one developer.**

### 11.2 Unproven claims (flagged)

| ID | Claim | Status | How it will be tested |
|---|---|---|---|
| U-P1 | The Pratt procedure over a partial order (§2.5.2) accepts exactly the expressions whose parent–child operator pairs are suitably related, with a unique tree | believed, unproven | T6a: brute-force enumerator over random operator sequences and random orders |
| U-P2 | The core calculus (§4.4, §4.6) satisfies progress and preservation (G1) | standard-looking, **no proof done** | CORE-07 property tests; a written proof sketch is recommended before T2 completes |
| U-P3 | The grammar-environment rule (§13.2) prevents use-site grammar from changing the parse of macro-introduced token trees | argued, unproven | HYG-09 family; adversarial tests |
| U-P4 | Racket scope-set hygiene carries over to non-S-expression syntax with user parsers | Rhombus is evidence of feasibility; our variant is unvalidated | HYG suite; ported Racket cases |
| U-P5 | The per-item pipeline with eager head-expansion has no remaining compile-time cycles | argued (`technical-risks.md` §2) | META/GEN suites; driver cycle tests |
| U-P6 | Compilation is deterministic | design intent | double-compile tests on every conformance case |
| U-P7 | Re-checking interfaces on load is cheap enough | unmeasured | benchmark in T8 |
| U-P8 | The full feature set is achievable by one developer | **unproven**; internal consistency of this spec does not imply implementability | tranche progress |

---

## 12. Parser edge cases **[A]**

| Input / situation | Behaviour | Restriction |
|---|---|---|
| `a+-b` | tokens `a` `+-` `b`. If no operator `+-` is active: `E-PARSE-UNKNOWN-OP` with a fix-it "write `a + -b`" when `+` and prefix `-` exist | Users must space adjacent operators. The parser **never** splits a run: splitting would make meaning depend on which operators are declared, so adding `+-` later would silently change existing code. |
| `x--y` | `x`, then a line comment from `--` | `--` always starts a comment outside strings and raw regions. Lint `W-LEX-COMMENT-AFTER-OPERAND` when `--` directly follows an operand with no space. No operator may contain `--`. Write `x - -y`. |
| `a+--b` | `a` `+`, then a comment | Same rule. |
| `x|>f`, `a<=>b` | single tokens `|>` and `<=>`; declared as infix operators | Operators whose texts are prefixes of each other (`<`, `<=`, `<=>`) never interact, because lexing ignores declarations. `a<=>-b` is unknown op `<=>-`. |
| Nested generic types | `Array[Array[Int]]` uses brackets | There is no `>>` problem, because types use `[]`. |
| Conflicting literal patterns | §6.1 and Example B: strict-prefix overlap rejected; patterns disjoint at any position coexist | No longest match in v0.1. |
| `["for", ident, "="]` vs `["for", ident, "in"]` | both allowed (disjoint at position 3) | Dispatch needs three tokens of lookahead; patterns are finite, so lookahead is bounded. |
| Nested syntax scopes | inner declarations and imports add entries; overlap with outer entries requires `shadowing`; leaving the block restores the outer registry; nested `fun` bodies inherit the registry at their position | Shadowing is per entry. There is no "clear all". |
| Macro-generated declarations in blocks | eager head-expansion; active from the next block item to the end of the block (Example D) | [v0.1] only syntax declarations and phase-0 locals; no `meta def`, `import` or `export`. |
| Quote under a different environment | `quote[K]{}` is parsed with the definition-site registry: use-site syntax has no effect, and syntax missing at the definition site is a definition-time error. `tokens{}` trees are stamped (§13.2). | Mixed-environment loose tokens are rejected (`E-SYN-MIXED-ENV`). |
| Raw region with nested braces | `#t{ a { b } c }` contains ` a { b } c ` | Only `{` and `}` are counted. |
| Raw region with string literals | `#json{ {"k": "}"} }` closes early, by design | Use `#json[=[ {"k": "}"} ]=]`. No escapes in raw regions. |
| Raw region closer inside long-bracket content | `#t[=[ … ]] … ]=]` ends at `]=]` | Choose `n` so that `]=ⁿ]` does not occur in the content. |
| `#t[i]` | operator `#`, ident `t`, group `[i]` | Only `#ident{` and `#ident[=*[` start raw regions. |
| Raw regions inside raw regions | not recognised by the lexer | A sublanguage parser may host-parse a sub-span, which is lexed normally and may contain raw regions. |
| `f\n(x)` | two statements | Trailing call is not accepted after a newline. |

---

## 13. Foundational safety contracts **[A]**

Each contract states the rule, what must be fixed **before implementation**,
what is **deferred**, and **how to test** it.

### 13.1 Identifier identity, locations, phases, scopes

- **Representation:** `Ident(name, scopes, span)`. A scope ID is opaque,
  derived deterministically from `(module id, item index, ordinal within
  item)`.
- **Phase is contextual.** It is not stored on the identifier. The
  expander knows whether it is expanding phase-0 or phase-1 code, and the
  binding table is keyed by `(name, phase)`. A module creates one module
  scope per phase.
- **Resolution:** for a reference at phase `p`, take the bindings at phase `p`
  with the same name whose scope set is a **subset** of the reference's. The
  unique largest wins. Incomparable maxima are `E-HYG-AMBIGUOUS`. None is
  `E-UNBOUND`.
- **Equality operations:** `free_eq(a, b)` (resolve to the same binding) and
  `bound_eq(a, b)` (same name and same scope set).
- **Macro step:** fresh macro scope added to input and flipped on output; a
  use-site scope in definition contexts, removed from binders as in Racket.
- **Locations:** `Original` or `Synthetic(expansion_id, parent)`. An
  expansion record holds the macro's origin identity and use-site span.
  Locations never affect resolution.
- **Before implementation:** the data shape (§2.6.1) and the deterministic
  scope-ID scheme. **Deferred:** the details of use-site scope removal (T4),
  and cross-module phase shifting for `meta import` (T8).
- **Test:** HYG-01..08, HYG-10; determinism of scope IDs (META-05).

### 13.2 Token trees from different grammar environments

- A **grammar environment** is a registry snapshot. User source is parsed
  with whatever environment the sequence parser holds at that point.
- **Stamping:** a `TokenTree` value at phase 1 carries a root env stamp:
  - `tokens{}`: the definition site's environment;
  - a macro's token-tree argument: the use site's environment at
    invocation;
  - host-parsed raw-region sub-spans: the use site's environment.
- **Parsing a stamped tree** uses its root stamp.
- **Splicing** a token tree with a different stamp into a `tokens{}` quote is
  allowed **only as a whole group**: it must occupy its own `()`, `[]` or
  `{}`. The group keeps its own stamp. When the parser parses a category
  *inside* such a group, it uses the group's stamp.
- **Rejected:** any dispatch decision whose tokens come from two different
  stamps (`E-SYN-MIXED-ENV`).
- **Escape hatch:** `syntax.restamp(tree, ctx)` re-stamps explicitly, like
  `ident_at` does for names.
- **Preferred style:** splice already-parsed `Syntax[K]` into structured
  quotes, which avoids the issue entirely.
- **Before implementation:** the env field in the syntax data shape.
  **Deferred:** the exact snapshot representation (T5), and whether to relax
  the whole-group rule (U-07).
- **Test:** HYG-09a–e (§2.7 of the conformance plan).

### 13.3 Capabilities and resource limits

**Capabilities.** A phase-1 invocation runs with
`declared(requires) ∩ granted(build config)`. Always granted: `pure`,
`fresh`, `diagnostics`, `env_query`. Declared per macro: `declare_syntax`.
Build-granted: `read_file(prefix)`. Not available in v0.1: `env_var`,
`clock`, `network`, `process`. Every primitive is tagged with its
capability, and the interpreter checks the tag on each call. A denied call
is `E-META-CAP`.

**Deterministic counters.** All counters count steps, never time:

| Limit | Default (configurable) | Error |
|---|---|---|
| Interpreter steps per phase-1 invocation | 10⁷ | `E-META-FUEL` |
| Allocations per invocation (words) | 10⁸ | `E-META-MEMORY` |
| Phase-1 call depth | 1 000 | `E-META-DEPTH` |
| Macro expansion depth (macro output containing macro uses) | 256 | `E-EXPAND-DEPTH` |
| Macro invocations per item | 10⁵ | `E-EXPAND-COUNT` |
| Syntax nodes produced per invocation | 10⁶ | `E-EXPAND-SIZE` |

**No partial effects.** Phase-1 code affects compilation only through its
return value and its diagnostics. Registry changes happen only via returned
declarations, so aborting an invocation leaves no state behind.

**Phase-1 global state** cannot exist: phase-1 defs must be syntactic values
(§13.5). Each invocation therefore starts from the same state.

- **Before implementation:** counter hooks and the capability check in the
  interpreter (T2); the primitive capability tag in the table format.
  **Deferred:** `read_file` path semantics (T7), and the final default
  values.
- **Test:** META-03/04/07/08; determinism (the same step count at failure
  on every run).

### 13.4 Unforgeable private type identities

- **Stamp:** each `type` declaration gets a stamp
  `(module id, declaration index, name)`. The **driver** assigns module ids
  from the canonical module path. Core terms refer to types only by stamp.
- **Authorisation rule (core checker):** construction, projection and
  `case` on an **opaque** type are allowed only in core items whose module id
  equals the stamp's module id. Membership comes from the driver, not from
  anything in the term.
- **Macros get no privileged access [v0.1].** Code a macro from `M`
  generates into `N` is a core item of `N`. To create or inspect `M`'s opaque
  values, it must call **exported functions** of `M`. This removes the
  Phase 0 "authorised module annotation" scheme (risk S-04), which could have
  been forged by a buggy elaborator.
- **Generated types** (Example D) belong to the module where the generating
  macro was used. That module is their owner.
- **Out of scope:** malicious tampering with compiled interface files.
  Interfaces are re-checked on load, but module identity is trusted to the
  driver.
- **Before implementation:** the stamp format and the rule (T2).
  **Deferred:** inlining of exported helpers, which is an optimisation
  performed after checking.
- **Test:** CORE-05 (direct), HYG/ELAB tests where a macro attempts a raw
  construction (must fail), and Example D end-to-end.

### 13.5 Polymorphism with mutation; phase-1 values

- **Value restriction (core):** a `def` with a `forall` type must have a
  `fun` literal body. Local `let`/`letrec` bindings are monomorphic. Type
  application is allowed only on polymorphic defs.
- **Phase-1 value rule (core):** every phase-1 `def` body is a syntactic
  value: a `fun` literal, a literal, or a constructor of syntactic values.
  There is no `ref`, no array allocation, and no primitive or function call
  at phase-1 definition level.
- **Before implementation:** both rules (T2). **Deferred:** nothing.
- **Test:** CORE-04 (`def r: forall a. Ref[Array[a]] = ref(…)` rejected),
  CORE-09 (a phase-1 `def counter = ref(0)` rejected), and property tests
  that never generalise a `Ref`.

### 13.6 Trusted primitives

- **One table**, one source. Each entry has a name, a type scheme, the
  phases where it is allowed, a capability tag, its trap behaviour (exact
  panic message prefixes), and its implementation. The core checker and the
  interpreter both read the **same entry**.
- **Agreement obligation:** for every primitive, a property test generates
  arguments of the declared types and checks that the result satisfies
  `value_has_type(result, declared result type)`, or that a declared trap
  occurred. `value_has_type` is a test-only checker over run-time values.
- **Initial table (T2):**
  - `Int`: `add sub mul div rem neg eq lt le`. Overflow and division by zero
    trap.
  - `Float`: `add sub mul div neg eq lt le`, and `int_to_float`;
    `float_to_int` traps on NaN or out-of-range values.
  - `String`: `concat len eq`, and `int_to_string`, `float_to_string`.
  - `Array`: `new(n, init) get set len`. Bounds violations trap.
  - `print`: phase 0 only.
- **Adding a primitive** is a TCB change. It needs a table entry, an
  agreement test, and a decision-log note. Phase-1 syntax primitives arrive
  in T4 under the same process.
- **Before implementation:** the table format and the agreement harness.
  **Deferred:** later primitives.
- **Test:** CORE-06 and the agreement suite.

### 13.7 Module interfaces and deterministic activation

- **Interface contents:**
  - the module id;
  - a source hash and the hashes of imported interfaces;
  - the core interface: exports in declaration order, with core types and
    type declarations;
  - serialized core of exported phase-1 definitions;
  - exported registry entries with origin identities
    `(module id, declaration index, entry name)`;
  - extended interfaces keyed by checker.

  Serialization is canonical.
- **Loading [v0.1]:** the core of every loaded interface is **re-checked**
  (U-13).
- **Imports:**
  - Module import cycles are forbidden at **all** phases [v0.1]
    (`E-IMPORT-CYCLE`).
  - Imports are literal items. The driver compiles dependencies on demand,
    in deterministic order.
  - An `import` item activates its entries as one set.
  - The conflict verdict is order-independent (§6.2).
  - Re-exports preserve origin identity.
- **Before implementation:** origin-identity format, and the cycle rule.
  **Deferred:** binary format and caching (T8, T14).
- **Test:** SYN-06, AMB-05/06, META-06, and reproducibility (byte-identical
  interfaces across runs).

### 13.8 Expansion termination, recursion, errors

- **Termination is not guaranteed.** Phase 1 is Turing-complete. The §13.3
  limits make non-termination a deterministic compile error.
- **Expansion order:**
  - item-position macros eagerly;
  - then outside-in, left-to-right;
  - type-directed macros in elaboration order (§4.2).
- **Error reporting:**
  - every phase-1 failure (panic, limit, capability, `ctx:error`) is
    reported at the **use site**, with an expansion backtrace of
    `(macro origin, use-site span)` frames;
  - long backtraces are truncated deterministically (first 10 and last 10
    frames);
  - a phase-1 panic also includes the phase-1 call stack.
- **Recovery:** if an item fails, it contributes nothing to the registry.
  If a **grammar-generating** macro fails, the **rest of that sequence is
  not compiled** (`N-SEQ-ABANDONED`), to avoid cascades of "unknown syntax"
  errors. Other item failures do not stop later items.
- **Before implementation:** none for T1 or T2 beyond the §13.3 hooks.
  **Deferred:** backtrace format (T4), recovery policy tests (T8).
- **Test:** META-03/07/08, GEN-07, golden diagnostics.

---

## 14. Phase 0.1 change summary

See `design-decisions.md` §0 for the decision table.

**T1.1 amendments to frozen §2.1.** Two ratifications of previously
ambiguous text, with no other change: R-47 (control characters inside
string, comment and raw-region bodies) and R-48 (a lone CR is not a line
end, including inside strings). Rationale and history: `design-decisions.md`
R-47, R-48 and its implementation record (I-01, I-03, I-17).

---

## 15. References consulted

Primary sources accessed during Phase 0:

- Lean 4 reference manual, "Defining New Syntax":
  https://lean-lang.org/doc/reference/latest/Notations-and-Macros/Defining-New-Syntax/
- Racket Reference, "Syntax Model": https://docs.racket-lang.org/reference/syntax-model.html ;
  M. Flatt, "Binding as Sets of Scopes": https://users.cs.utah.edu/~mflatt/scope-sets-5/
- Rhombus/enforest, "Operator Precedence and Associativity":
  https://docs.racket-lang.org/enforest/Operator_Precedence_and_Associativity.html ;
  Flatt et al., OOPSLA 2023, https://doi.org/10.1145/3622818 ;
  https://docs.racket-lang.org/rhombus-model/parsing.html
- Raku: https://docs.raku.org/language/grammars ; https://docs.raku.org/language/slangs ;
  https://docs.raku.org/syntax/%7C ; https://docs.raku.org/syntax/is%20tighter
- Metalua: https://github.com/fab13n/metalua
- Erdweg et al., SugarJ, OOPSLA 2011, https://doi.org/10.1145/2048066.2048099
- Chang, Knauth, Greenman, "Type Systems as Macros", POPL 2017,
  https://www2.ccs.neu.edu/racket/pubs/popl17-ckg.pdf ; https://github.com/stchang/macrotypes ;
  Turnstile+, https://arxiv.org/abs/2107.01295

Background, not re-verified: Honu (GPCE 2012); Copper/Silver (PLDI 2009);
SoundX (POPL 2016); Typed Racket; Terra; Teal; Luau. Phase 0.1 consulted no
new sources. The statement about the undecidability of CFG ambiguity is
standard formal-language theory.
