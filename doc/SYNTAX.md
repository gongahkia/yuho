# `Yuho` language syntax

## Table Of Contents

1. [Introduction](#introduction)
2. [Comments](#comments)
3. [Variable Declaration](#variable-declaration)
4. [Types](#types)
5. [Data Structures](#data-structures)
6. [Operators](#operators)
7. [Control Structures](#control-structures)
8. [Functions](#functions)
9. [Statute Blocks](#statute-blocks)
10. [Imports](#imports)
11. [Testing](#testing)

## Introduction

* Yuho source files have the file extension `.yh`
* strongly, statically-typed
* Yuho source files follow the snake_case naming scheme
* variables, functions, structs and all user-defined constructs follow the camelCase naming scheme
* indentation is optional but recommended for readability with nested `{}` curly braces
* features limited syntax out of the box
    * allows language to be quickly picked up and used
    * allows for detailed modelling of statute logic
    * semicolons are optional (allowed but not required)
* functional language
    * all values are immutable
    * every statement is an expression
    * every expression evaluates to a single value
    * mimicks the logical and syntactical completeness of the law

## Comments

```yh
// this is a single-line comment

/*
this is a
multi-line
comment
*/

/// this is a doc comment
```

## Variable Declaration

```yh
// := provides immutable variable declaration and binding
// the type is specified before the variable name
// every value in Yuho is IMMUTABLE

int anInteger := 200
float aFloat := 400.00
string aString := "even more examples are shown below"
bool aBool := TRUE
money aMoney := $10.56
percent aPercent := 25%
date aDate := 2020-01-12
duration aDuration := 1 year

// pass acts as a null/void value, skipping execution
// optional types use ? suffix
int? maybeAnInt := pass
```

## Types

```yh
// --- BUILTIN TYPES ---

// int — integer value of any precision
int anExampleInt := 200

// float — floating-point value of any precision
float anExampleFloat := 0.1823448

// bool — TRUE or FALSE
bool anExampleBool := TRUE

// string — declared within "" double quotation marks
string anExampleString := "if the act by which the death is caused is done with the intention of causing death"

// percent — integer suffixed with %, evaluates to a float on the back-end
percent anExamplePercent := 25%

// money — currency symbol followed by comma-separated amount
//   supported symbols: $ £ € ¥ ₹ SGD USD EUR GBP JPY CNY INR AUD
//   on the back-end evaluates to a float, currency-agnostic
money anExampleMoney := $12,000,298.28

// date — ISO8601 format YYYY-MM-DD
date anExampleDate := 2020-01-12

// duration — integer followed by unit(s): year(s), month(s), day(s), hour(s), minute(s), second(s)
//   multiple parts can be chained
duration anExampleDuration := 1 day
duration anotherDuration := 2 years, 6 months

// void — used as function return type when no value is returned
```

## Data Structures

```yh
// --- STRUCTS ---
// struct defines a comma-delimited collection of named typed fields within {} curly braces
// field type is specified before the field name
// the last field may also have a trailing comma
// struct values are accessed via . dot syntax
// := assigns an immutable value to a field

// a normal struct
struct Person {
    string name,
    int age,
    money wealth,
    date dob,
}

// struct literal (instantiation)
Person aPerson := Person {
    name := "Tan Ah Hock",
    age := 20,
    wealth := $10,000,000.00,
    dob := 2002-10-10,
}

aPerson.name // evaluates to "Tan Ah Hock"
aPerson.age  // evaluates to 20

// --- ENUM-LIKE STRUCTS ---
// structs without typed fields act as enums
// variants are accessed via . dot syntax

struct Fruit {
    apple,
    orange,
    pear,
}

Fruit myFruit := Fruit.apple

// --- GENERIC STRUCTS ---
// structs can have type parameters

struct Container<T> {
    T value,
    string label,
}

// --- ARRAY TYPES ---
// arrays use [Type] syntax

[int] numbers
[string] names

// --- OPTIONAL TYPES ---
// optional types use ? suffix

int? maybeNumber
string? maybeName
```

## Operators

```yh
// --- ARITHMETIC OPERATORS ---

+ // addition
- // subtraction
* // multiplication
/ // division
% // modulo

// --- COMPARISON OPERATORS ---

== // equality check
!= // inequality check
>  // greater than
<  // less than
>= // greater than or equal
<= // less than or equal

// --- LOGICAL OPERATORS ---

&& // logical AND
|| // logical OR
!  // logical NOT
```

## Control Structures

```yh
// there are NO LOOPS in Yuho — statutes don't loop
// there are NO if-else constructs — use match-case instead
// Yuho provides pattern-matching via match-case with consequence

// --- MATCH-CASE ---
// match optionally takes a scrutinee expression in parentheses
// each case arm has a pattern, optional guard, and a consequence expression
// _ is the wildcard catch-all pattern that MUST be specified
// pass skips execution of the current block

// match without scrutinee (guard-based)
money currentBankAccount := $100,000.00
string verdict := match {
    case TRUE if currentBankAccount <= $200,000.00 := consequence "Broke";
    case TRUE if currentBankAccount > $200,000.00 := consequence "Not broke";
    case _ := consequence "Unknown";
}

// match with scrutinee
bool isGuilty := TRUE
string judgement := match (isGuilty) {
    case TRUE := consequence "Go to Jail!";
    case FALSE := consequence "Acquitted!";
    case _ := consequence pass;
}

// match with struct patterns
struct Verdict {
    guilty,
    notGuilty,
    mistrial,
}

string result := match (myVerdict) {
    case guilty := consequence "Sentenced";
    case notGuilty := consequence "Free";
    case _ := consequence "Retrial";
}
```

## Functions

```yh
// fn <name>(<Type> <param>, ...) : <returnType> { <body> }
// return prefixes the return expression
// every function MUST return an established or user-defined type

fn add(int a, int b) : int {
    return a + b;
}

fn evaluate(string deceptionType, bool causesDamageHarm) : string {
    match {
        case TRUE if deceptionType == "none" := consequence "Not cheating";
        case TRUE if causesDamageHarm := consequence "Said to cheat";
        case _ := consequence "Not said to cheat";
    }
}
```

## Statute Blocks

```yh
// statute blocks model legal provisions with structured sub-blocks
// syntax: statute <sectionNumber> "<title>" { ... }
// section numbers can be prefixed with S, have decimal sub-sections, and letter suffixes

statute 415 "Cheating" {

    // definitions block — defines key legal terms
    definitions {
        deceive := "To cause a person to believe something that is false";
        fraudulently := "With intent to defraud another person";
        dishonestly := "With intention of causing wrongful gain or wrongful loss";
    }

    // elements block — specifies actus_reus, mens_rea, or circumstance
    elements {
        actus_reus deception := "Deceiving any person";
        mens_rea intent := "Fraudulently or dishonestly";
        circumstance harm := "Causing or likely to cause damage to body, mind, reputation, or property";
    }

    // penalty block — specifies imprisonment and/or fine ranges
    // ranges use .. operator between two values
    penalty {
        imprisonment := 1 year .. 7 years;
        fine := $0.00 .. $50,000.00;
        supplementary := "Additional conditions may apply";
    }

    // illustration blocks — concrete examples of statute application
    illustration example1 {
        "A intentionally deceives B into believing that a worthless article is valuable, and thus induces B to buy it. A cheats."
    }

    illustration example2 {
        "A falsely pretends to be in government service and induces B to let him have goods on credit. A cheats."
    }
}
```

### Element Groups (AND/OR relationships)

```yh
// elements can be grouped using all_of (AND) and any_of (OR)
// groups can be nested to model complex logical relationships

statute 415 "Cheating" {
    elements {
        all_of {
            actus_reus deception := "Deceiving any person";
            any_of {
                mens_rea fraudulent := "Fraudulently inducing the person";
                mens_rea dishonest := "Dishonestly inducing the person";
            }
            actus_reus inducement := "Inducing delivery of property, consent to retain, or act/omission";
            circumstance harm := "Causing or likely to cause damage to body, mind, reputation, or property";
        }
    }
}
```

### Exception Blocks

```yh
// exception blocks model statutory defences, provisos, and General Exceptions
// syntax: exception [label] { "condition" "effect" }

statute 300 "Murder" {
    elements {
        actus_reus act := "Causing death of a person";
        mens_rea intent := "Intention of causing death";
    }

    exception provocation {
        "If the offender was deprived of self-control by grave and sudden provocation"
        "Culpable homicide not amounting to murder"
    }

    exception privateDefence {
        "If the offender exercises the right of private defence that extends to causing death"
        "Not an offence"
    }
}
```

### Case Law Blocks

```yh
// caselaw blocks associate judicial interpretations with statute elements
// syntax: caselaw "case name" "citation" { "holding" element <name> }

statute 415 "Cheating" {
    elements {
        actus_reus deception := "Deceiving any person";
    }

    caselaw "PP v Tan Cheng Bock" "[2019] SGCA 1" {
        "Deception requires active misleading, not mere silence"
        element deception
    }
}
```

### Extended Penalty

```yh
// penalty block supports caning and death penalty in addition to imprisonment and fine

penalty {
    imprisonment := 5 years .. 20 years;
    fine := $0.00 .. $20,000.00;
    caning := 6 .. 24 strokes;
    death := TRUE;
    supplementary := "Mandatory minimum of 6 strokes for repeat offenders";
}
```

## Imports

```yh
// --- IMPORT ---
// import brings definitions from other Yuho source files

// import entire module
import "penal_code/s415_cheating"

// import specific names
import { CheatingCase, evaluate } from "penal_code/s415_cheating"

// import everything
import * from "penal_code/s415_cheating"

// --- REFERENCING ---
// referencing is used in test files to import statutes from the library

referencing penal_code/s415_cheating
```

## Testing

```yh
// assert verifies that an expression evaluates to TRUE
// throws an error during validation if it evaluates to FALSE
// an optional message string can follow the condition

fn add(int a, int b) : int {
    return a + b;
}

assert add(1, 2) == 3;
assert add(2, 3) == 5;
assert add(3, 4) == 7, "Expected 3 + 4 to equal 7";
```

## Modelling Ambiguity

Statutes often have contested meanings (e.g., what counts as "dishonestly inducing"). Yuho handles this in two ways:

### Doc comments for competing interpretations

Use `///` doc comments to annotate elements with alternative readings:

```yh
statute 415 "Cheating" {
    elements {
        /// strict view: requires active misrepresentation (PP v Tan Cheng Bock)
        /// liberal view: includes passive non-disclosure of material facts
        actus_reus deception := "Deceiving any person";
    }
}
```

### Separate evaluation functions for alternative interpretations

Model competing interpretations as distinct functions and test both:

```yh
fn evaluateStrict(string deceptionType, bool causesDamageHarm) : string {
    match {
        case TRUE if deceptionType == "active" && causesDamageHarm := consequence "Said to cheat";
        case _ := consequence "Not said to cheat";
    }
}

fn evaluateLiberal(string deceptionType, bool causesDamageHarm) : string {
    match {
        case TRUE if deceptionType != "none" && causesDamageHarm := consequence "Said to cheat";
        case _ := consequence "Not said to cheat";
    }
}

// test a fact pattern against both interpretations
assert evaluateStrict("passive", TRUE) == "Not said to cheat";
assert evaluateLiberal("passive", TRUE) == "Said to cheat";
```

### Cross-referencing statutes

Import definitions from one statute into another to model how statutes reference shared terms:

```yh
// s24 defines "dishonestly" — import it into s415
import { dishonestly } from "penal_code/s24_definitions"

// s415 can now reference the imported definition
statute 415 "Cheating" {
    definitions {
        dishonestly := dishonestly; // from s24
    }
}
```
