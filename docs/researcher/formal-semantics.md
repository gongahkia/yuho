# Yuho Formal Semantics

This document defines the formal semantics of the Yuho DSL for encoding
Singapore Criminal Law statutes. Yuho has nominal typing, big-step
operational semantics, and a defeasible reasoning layer for exception defeat.

---

## 1. Abstract Syntax

The abstract syntax is presented in BNF at the AST level (corresponding to
`src/yuho/ast/nodes.py`). In addition to statutes and functions, Yuho also
supports annotation metadata, `legal_test` blocks, and `conflict_check`
declarations for jurisprudential and study-oriented workflows.

### 1.1 Modules

```
Module     ::= Import* StructDef* EnumDef* TypeAlias* FunctionDef* Statute*
               LegalTest* ConflictCheck* VarDecl* Assert*
Import     ::= 'import' Path Names?
Referencing ::= 'referencing' Path
Annotation ::= '@' AnnotationName ('(' StringLit (',' StringLit)* ')')?
AnnotationName ::= 'presumed' | 'precedent' | 'hierarchy' | 'amended'
```

### 1.2 Types

```
Type       ::= BuiltinType | NamedType | GenericType | OptionalType | ArrayType
BuiltinType ::= 'int' | 'float' | 'bool' | 'string' | 'money' | 'percent'
              | 'date' | 'duration' | 'void'
NamedType  ::= Identifier
GenericType ::= Identifier '<' Type (',' Type)* '>'
OptionalType ::= Type '?'
ArrayType  ::= '[' Type ']'
RefinementType ::= Type '{' Expr '..' Expr '}'
```

### 1.3 Enums and Type Aliases

```
EnumDef    ::= 'enum' Identifier '{' EnumVariant (',' EnumVariant)* '}'
EnumVariant ::= Identifier ('(' Type (',' Type)* ')')?
TypeAlias  ::= 'type' Identifier '=' Type
```

### 1.4 Expressions

```
Expr       ::= Literal | Identifier | FieldAccess | IndexAccess
             | FunctionCall | BinaryExpr | UnaryExpr | MatchExpr
             | StructLiteral | 'pass'

Literal    ::= IntLit | FloatLit | BoolLit | StringLit
             | MoneyLit | PercentLit | DateLit | DurationLit

BinaryExpr ::= Expr Op Expr
Op         ::= '+' | '-' | '*' | '/' | '%'
             | '==' | '!=' | '<' | '>' | '<=' | '>='
             | '&&' | '||'

UnaryExpr  ::= ('!' | '-') Expr

MatchExpr  ::= 'match' Expr? '{' MatchArm* '}'
MatchArm   ::= 'case' Pattern Guard? ':=' 'consequence' Expr
Guard      ::= 'if' Expr

Pattern    ::= '_' | Literal | Identifier | StructPattern
StructPattern ::= Identifier '{' FieldPattern (',' FieldPattern)* '}'
FieldPattern  ::= Identifier (':' Pattern)?
```

### 1.4 Statements

```
Stmt       ::= VarDecl | Assignment | Return | Pass | Assert | ExprStmt
VarDecl    ::= Type Identifier (':=' Expr)?
Assignment ::= LValue ':=' Expr
Return     ::= 'return' Expr?
Assert     ::= 'assert' Expr (',' StringLit)?
Block      ::= '{' Stmt* '}'
```

### 1.5 Definitions

```
StructDef  ::= 'struct' Identifier TypeParams? '{' FieldDef* '}'
FieldDef   ::= Type Identifier
FunctionDef ::= 'fn' Identifier '(' ParamList? ')' (':' Type)? Block
ParamDef   ::= Type Identifier
```

### 1.6 Statute Structure

```
Statute    ::= Annotation* 'statute' SectionNum StringLit? TemporalMeta? HierarchyMeta? '{' StatuteMember* '}'
TemporalMeta ::= ('effective' DateLit)? ('repealed' DateLit)?
HierarchyMeta ::= ('subsumes' SectionNum)? ('amends' SectionNum)?
StatuteMember ::= Definitions | Elements | Penalty | Illustration
               | Exception | CaseLaw

Definitions ::= 'definitions' '{' DefEntry* '}'
DefEntry    ::= Identifier ':=' StringLit

Elements    ::= 'elements' '{' (Element | ElementGroup)* '}'
Element     ::= ElementType Identifier ':=' Expr CausedBy? BurdenQual?
ElementType ::= 'actus_reus' | 'mens_rea' | 'circumstance'
              | 'obligation' | 'prohibition' | 'permission'
CausedBy    ::= 'caused_by' Identifier
BurdenQual  ::= 'burden' ('prosecution' | 'defence') ProofStandard?
ProofStandard ::= 'beyond_reasonable_doubt' | 'balance_of_probabilities' | 'prima_facie'
ElementGroup ::= ('all_of' | 'any_of') '{' (Element | ElementGroup)* '}'

Penalty     ::= 'penalty' Sentencing? '{' PenaltyClauses MandatoryMin? '}'
Sentencing  ::= 'concurrent' | 'consecutive'
MandatoryMin ::= 'minimum' ('imprisonment' ':=' DurationLit | 'fine' ':=' MoneyLit)
Exception   ::= 'exception' Identifier? '{' StringLit StringLit? ('when' Expr)? '}'
CaseLaw     ::= 'caselaw' StringLit StringLit? '{' StringLit ('element' Identifier)? '}'
Illustration ::= 'illustration' Identifier? '{' StringLit '}'
```

### 1.7 Legal Tests And Conflict Checks

```
LegalTest ::= Annotation* 'legal_test' Identifier '{' LegalTestField* RequiresClause? '}'
LegalTestField ::= Type Identifier
RequiresClause ::= 'requires' Expr

ConflictCheck ::= Annotation* 'conflict_check' Identifier '{'
                  'source' ':=' StringLit
                  'target' ':=' StringLit
                  '}'
```

---

## 2. Type System

Yuho uses **nominal typing** with limited coercion.

### 2.1 Typing Judgments

We write `Gamma |- e : T` to mean "under type environment Gamma, expression
e has type T."

#### Literals

```
-------------------  (T-Int)
Gamma |- n : int

-------------------  (T-Float)
Gamma |- f : float

-------------------  (T-Bool)
Gamma |- b : bool    where b in {TRUE, FALSE}

-------------------  (T-String)
Gamma |- s : string  where s is a string literal

-------------------  (T-Money)
Gamma |- $n : money

-------------------  (T-Percent)
Gamma |- n% : percent

-------------------  (T-Date)
Gamma |- YYYY-MM-DD : date

-------------------  (T-Duration)
Gamma |- n units : duration
```

#### Variables and Fields

```
Gamma(x) = T
-------------------  (T-Var)
Gamma |- x : T

Gamma |- e : S    S.fields(f) = T
-----------------------------------  (T-Field)
Gamma |- e.f : T

Gamma |- e1 : [T]    Gamma |- e2 : int
-----------------------------------------  (T-Index)
Gamma |- e1[e2] : T
```

#### Binary Operators

```
Gamma |- e1 : int    Gamma |- e2 : int    op in {+,-,*,/,%}
-------------------------------------------------------------  (T-ArithInt)
Gamma |- e1 op e2 : int

Gamma |- e1 : T1    Gamma |- e2 : T2
T1 in {int,float}   T2 in {int,float}   (T1=float or T2=float)
op in {+,-,*,/,%}
-------------------------------------------------------------  (T-ArithFloat)
Gamma |- e1 op e2 : float

Gamma |- e1 : T    Gamma |- e2 : T    op in {==,!=,<,>,<=,>=}
-------------------------------------------------------------  (T-Compare)
Gamma |- e1 op e2 : bool

Gamma |- e1 : bool    Gamma |- e2 : bool    op in {&&,||}
-------------------------------------------------------------  (T-Logic)
Gamma |- e1 op e2 : bool
```

### 2.2 Coercion Rules

```
int <: float       (implicit widening)
money + money -> money  (same currency)
duration + duration -> duration
duration arithmetic is component-wise
```

### 2.3 Struct Typing

```
struct S defined with fields {f1: T1, ..., fn: Tn}
Gamma |- e1 : T1   ...   Gamma |- en : Tn
--------------------------------------------  (T-StructLit)
Gamma |- S { f1 := e1, ..., fn := en } : S
```

### 2.4 Function Typing

```
Gamma, x1:T1, ..., xn:Tn |- body : Tr
-------------------------------------------------  (T-FnDef)
Gamma |- fn f(T1 x1, ..., Tn xn) : Tr { body }

Gamma(f) = (T1,...,Tn) -> Tr    Gamma |- ei : Ti
---------------------------------------------------  (T-Call)
Gamma |- f(e1,...,en) : Tr
```

---

## 3. Operational Semantics (Big-Step)

We define big-step (natural) semantics. We write `<e, sigma> => v` to mean
"expression e evaluated in store sigma produces value v."

`Annotation` nodes are semantically inert in evaluation: they enrich the model
with provenance or doctrinal metadata but do not change the runtime value of an
expression. `legal_test` blocks denote named requirement bundles whose
`requires` clause evaluates to a boolean condition over declared fields.
`conflict_check` blocks denote named metadata relations between two sources and
are consumed by higher-level analysis or transpilation layers rather than the
core evaluator.

### 3.1 Values

```
v ::= n          (integer)
    | f          (float)
    | true | false
    | s          (string)
    | $n         (money with currency)
    | n%         (percent)
    | d          (date)
    | dur        (duration)
    | {f1=v1,...,fn=vn}:S  (struct instance of type S)
    | [v1,...,vn] (list)
    | none
```

### 3.2 Expression Evaluation

#### Literals

```
<n, sigma> => n                    (E-Int)
<f, sigma> => f                    (E-Float)
<TRUE, sigma> => true              (E-True)
<FALSE, sigma> => false            (E-False)
<"s", sigma> => s                  (E-String)
<pass, sigma> => none              (E-Pass)
```

#### Variable Lookup

```
sigma(x) = v
-------------------                (E-Var)
<x, sigma> => v
```

#### Field Access

```
<e, sigma> => {f1=v1,...,fn=vn}:S    fi = f
----------------------------------------------  (E-Field)
<e.f, sigma> => vi
```

#### Binary Expressions

```
<e1, sigma> => v1    <e2, sigma> => v2    v1 op v2 = v
-------------------------------------------------------  (E-BinOp)
<e1 op e2, sigma> => v
```

Operator semantics:
- Arithmetic: standard with int->float promotion
- Comparison: structural equality for ==, !=; ordered comparison for <, >, <=, >=
- Logical: short-circuit evaluation for &&, ||

#### Unary Expressions

```
<e, sigma> => v    !v = v'
--------------------------  (E-Not)
<!e, sigma> => v'

<e, sigma> => n
--------------------------  (E-Neg)
<-e, sigma> => -n
```

### 3.3 Match Expression

```
<scrutinee, sigma> => v
match(pi, v) = theta_i    (first matching arm)
guard_i absent or <gi, sigma[theta_i]> => true
<body_i, sigma[theta_i]> => r
--------------------------------------------------  (E-Match)
<match(scrutinee) { case p1 if g1 := consequence b1; ... }, sigma> => r
```

Pattern matching function `match(p, v)`:

```
match(_, v)      = {}                              (wildcard)
match(lit, v)    = {} if eval(lit) = v, else fail  (literal)
match(x, v)      = {x -> v}                        (binding)
match(S{f1:p1,...,fn:pn}, {f1=v1,...}:S) =
    match(p1,v1) U ... U match(pn,vn)              (struct destructure)
```

### 3.4 Function Call

```
sigma(f) = fn f(T1 x1,...,Tn xn) : Tr { body }
<ei, sigma> => vi for each i
sigma' = sigma[x1 -> v1, ..., xn -> vn]   (new child scope)
<body, sigma'> => v   (via return or last expression)
-------------------------------------------------------  (E-Call)
<f(e1,...,en), sigma> => v
```

Return is modeled via `ReturnSignal` exception:

```
<e, sigma> => v
-----------------------------------  (E-Return)
<return e, sigma> => ReturnSignal(v)
```

### 3.5 Statement Execution

```
<e, sigma> => v    sigma' = sigma[x -> v]
------------------------------------------  (E-VarDecl)
<T x := e, sigma> => sigma'

<e, sigma> => v    sigma' = sigma[target -> v]
----------------------------------------------  (E-Assign)
<target := e, sigma> => sigma'

<cond, sigma> => true
---------------------  (E-AssertPass)
<assert cond, sigma> => sigma

<cond, sigma> => false
--------------------------  (E-AssertFail)
<assert cond, sigma> => ERROR
```

### 3.6 Block Execution

```
<s1, sigma> => sigma1
<s2, sigma1> => sigma2
...
<sn, sigma_{n-1}> => sigma_n
--------------------------------  (E-Block)
<{s1; s2; ...; sn}, sigma> => sigma_n
```

ReturnSignal propagates through block execution.

---

## 4. Defeasible Semantics

Yuho implements a **priority-ordered defeasible reasoning** model for
statute evaluation. The key relation is the **exception defeat** relation.

### 4.1 Statute Satisfaction

A statute S is **base-satisfied** by facts F iff all elements of S are
satisfied by F:

```
BaseSat(S, F) iff forall e in elements(S): Sat(e, F)
```

For element groups:

```
Sat(all_of{e1,...,en}, F) iff forall i: Sat(ei, F)
Sat(any_of{e1,...,en}, F) iff exists i: Sat(ei, F)
```

### 4.2 Exception Defeat

An exception E **defeats** a statute S given facts F iff:

```
Defeats(E, S, F) iff
    BaseSat(S, F) AND
    (guard(E) is absent => F matches exception label) AND
    (guard(E) is present => <guard(E), F> => true)
```

### 4.3 Final Verdict

```
Verdict(S, F) =
    "not_satisfied"       if NOT BaseSat(S, F)
    "exception_applied"   if BaseSat(S, F) AND exists E in exceptions(S): Defeats(E, S, F)
    "convicted"           if BaseSat(S, F) AND NOT exists E in exceptions(S): Defeats(E, S, F)
```

### 4.4 Partial Order on Rules

Exceptions have implicit priority by declaration order. The first matching
exception takes effect. This gives a total order on exceptions within a
statute:

```
E1 > E2 > ... > En    (by declaration order in source)
```

### 4.5 Reasoning Chain

The evaluator produces a **reasoning chain** -- an ordered sequence of
steps documenting element satisfaction, exception evaluation, and final
verdict. This chain is available for research export and audit.

---

## 5. Module Semantics

### 5.1 Import Resolution

```
import "path"           => resolve path.yh relative to importing file
import { x, y } from "path"  => resolve and bind x, y from exports
import * from "path"    => resolve and bind all exports
referencing path        => resolve library/{path}/statute.yh
```

### 5.2 Scoping Rules

Yuho uses **lexical scoping** with chained environments:

```
Env = { bindings: Map<Name, Value>,
        struct_defs: Map<Name, StructDef>,
        enum_defs: Map<Name, EnumDef>,
        type_aliases: Map<Name, Type>,
        function_defs: Map<Name, FunctionDef>,
        statutes: Map<Section, Statute>,
        parent: Env? }
```

Name resolution walks the parent chain:

```
lookup(x, env) =
    env.bindings[x]           if x in env.bindings
    lookup(x, env.parent)     if env.parent exists
    ERROR                     otherwise
```

### 5.3 Cross-Module Resolution

Imported symbols are injected into the importing module's top-level
environment. Cycle detection prevents infinite resolution loops.

---

## 6. Type Soundness Sketch

### 6.1 Progress

**Theorem (Progress):** If `Gamma |- e : T` and `e` is not a value,
then there exists `e'` such that `<e, sigma> => e'` for any store
`sigma` consistent with `Gamma`.

*Sketch:* By structural induction on the typing derivation. Each typing
rule has a corresponding evaluation rule. Literal types are already
values. Binary expressions evaluate by evaluating sub-expressions
(induction) then applying the operator. Function calls resolve via the
environment. Match expressions iterate arms until a match is found
(exhaustiveness checking ensures at least one arm matches). Struct
literals evaluate field expressions. Field access succeeds because
nominal typing guarantees field existence.

### 6.2 Preservation

**Theorem (Preservation):** If `Gamma |- e : T` and `<e, sigma> => v`,
then `v` has type `T`.

*Sketch:* By structural induction on the evaluation derivation.
Arithmetic operations preserve types (int+int=int, float promotion is
consistent). Comparison operations return bool. Function call returns
the declared return type (by induction on body evaluation). Match
expressions return the body type of the matched arm. Struct literals
produce instances of the declared struct type.

### 6.3 Limitations

- Duration and money arithmetic are approximate (30 days/month, 365 days/year)
- Optional types require explicit null checks (no gradual typing)
- Generic types are not fully checked (erased at runtime)
- The defeasible layer operates post-type-checking and is not type-directed

---

## 7. Notation Index

| Symbol | Meaning |
|--------|---------|
| `Gamma` | Type environment |
| `sigma` | Runtime store/environment |
| `|-` | "entails" / typing judgment |
| `=>` | "evaluates to" |
| `v` | Runtime value |
| `T` | Type |
| `theta` | Pattern match bindings |
| `BaseSat(S, F)` | Base element satisfaction |
| `Defeats(E, S, F)` | Exception defeat relation |
| `Verdict(S, F)` | Final evaluation verdict |
