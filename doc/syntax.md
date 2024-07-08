# `Yuho` language syntax

## Introduction

* file extension of `.yh`
* strongly, statically-typed
* camelCase naming scheme
* limited syntax out of the box
    * allow for language to be quickly learnt
    * allow for detailed modelling of statute logic
    * not semicolon-delimited
* functional language
    * all values are immutable
    * every statement is an expression 
    * every expression evaluates to a single value
    * limited theoretical support for higher-order functions, functions are therefore 1.5 class citizens (not first class)
    * mimicks the completeness of the law

## Comments

```yh
// ----- COMMENT -----

// this is a single-line comment

/* 
this is a 
multi-line 
comment
*/
```

## Variable declaration

```yh
// ----- VARIABLE DECLARATION -----
    // : 
    // := => 
    // scope =>

```

## Types

```yh
// ----- DATATYPE -----

// NUMERICAL PRIMITIVES
    // integer => stores an integer number value of any precision
    // float => stores a floating-point number value of any precision
    // percent => written as an integer suffixed with the % operator
        // on the back-end evaluates to a float 
    // money => written as a float prefixed with the $ operator where every 3 characters are delimited with a , comma operator and the last 2 characters are prefixed with the . period operator
        // on the back-end evaluates to a float
        // note that the money datatype is currency-agnostic
    // date => declared in the format DD-MM-YYYY where each segment is delimited by the - dash operator
        // on the back-end evaluates to an integer relative to the number of days from the earliest date within the provided scope, allowing computation on date values
    // duration => suffixed by one or a combination of the following (day, month, year) in that hierachichal order
        // on the back-end any unmentioned duration indicators are assigned the default value of 0
        // on the back-end, duration is then converted to an integer representing number of days

integer anExampleInteger := 200
float anExampleFloat := 0.1823448
percent anExamplePercentage := 25% // this evaluates to 0.25 
money anExampleMoneyAmount := $12,000,298,322.28 // this evaluates to 12000298322.28
date anExampleDate := 12-01-2020 // this evaluates to an integer dependant on the relative earliest date within the local scope
duration anExampleDuration := 1 day // this evaluates to 1 day 0 month 0 year, which then evaluates to 1 day total

// GENERIC PRIMITIVES
    // boolean => TRUE, FALSE
    // string => declared within "" double quotation marks

boolean anExampleBoolean := TRUE
string anExampleString := "if the act by which the death is caused is done with the intention of causing death"
```

## Data structures

```yh
// ----- DATA STRUCTURE -----
    // there is only ONE data structure in Yuho, the struct
    // this means that there are no other conventional data structures, such as lists, tuples etc
    // Yuho takes inspiration from languages like Lua and PHP here, where the core syntax is built around the singular data structure, the dictionary cum table
    // the rationale behind this is as follows
        // 1. all literals are immutable by default, so data structures designed specifically to be dynamically-sized or mutable like lists and conventional dictionaries need not exist
        // 2. every named structured value represented within a statute should have a named field for readability and ease of understanding for the average lawyer
        // 3. feel free to make as many nested structs as you want, those are allowed as well
        // 4. also feel free to leave struct value datatypes completely unmentioned, allowing for the creation of defined enums as required

// --- STRUCTS ---
    // struct => defines a struct, which is a user-defined , comma-delimited collection of named fields and its corresponding datatype declared within {} curly braces
        // note that the field value's datatype is specified before the field's named identifier
        // note that Yuho's struct named field identifiers themselves can be of any datatype and do not necessarily have to be a string
        // also note that structs are really a custom user-defined datatype which can then be called as any other datatype
        // lastly observe that the last named field of the struct is also suffixed with a , comma similar to Go
    // . => struct values are accessed via the dot syntax (and enum variants are called within the context of enums)
    // := => indicates the relationship between a specified named field and the immutable value assigned to it (meaning, therefore that struct fields are also immutable)
    // this flexible syntax allows for the following data structures to be implemented if necessary (examples included below)
        // fixed-sized array
        // fixed-size tuple
        // fixed-size dictionary
        // immutable enum
        // a normal struct
        // etc.

// - AN ARRAY -

struct anExampleArrayDatatype {
    string 0,
    string 1,
    string 2,
}

anExampleArrayDatatype anEgArrayLiteral := {
    0 := "watermelon",
    1 := "sugar",
    2 := "high",
}

anEgArrayLiteral.1 // evaluates to the string value "sugar"

// - A TUPLE -

struct anExampleTupleDatatype {
    string 0,
    boolean 1,
    money 2,
}

anExampleTupleDatatype anEgTupleLiteral := {
    0 := "okay thank you very much and",
    1 := FALSE,
    2 := $10.56,
}

// - A DICTIONARY -

struct anExampleDictionaryDatatype {
    string defZero,
    string defOne,
    string defTwo,
}

anExampleDictionaryDatatype anEgDictionaryLiteral := {
    defZero := "lovely",
    defOne := "and",
    defTwo := "goodbye",
}

// - AN ENUM -

struct anExampleEnumDatatype {
    apple,
    orange,
    pear,
    pineapple,
}

anExampleEnumDatatype anEgEnumLiteral := anExampleEnum.apple
anExampleEnumDatatype aSecondEnumLiteral := anExampleEnum.orange
anExampleEnumDatatype aThirdEnumLiteral := anExampleEnum.pear
anExampleEnumDatatype aFinalEnumLiteral := anExampleEnum.pineapple

// - A NORMAL STRUCT -

struct anExampleNormalStruct {
    string name,
    integer age, 
    money wealth,
    date DOB,
}

anExampleNormalStruct anEgNormalStructLiteral := {
    name := "Tan Ah Hock",
    age := 20,
    wealth := $10,000,000.00,
    DOB := 10-10-2002,
}
```

## Operators

```yh
// ----- OPERATORS -----

// --- ARITHMETIC OPERATOR ---

+ // addition
- // subtraction
* // multiplication
/ // division
// // integer divison
% // modulo

// --- COMPARISON OPERATOR ---

== // partial equality check for equality in value but not type, since Yuho's strict type system already automatically prevents type coercion
!= // partial inequality check for inequality in value but not type, since Yuho's strict type system already automatically prevents type coercion
> // comparison operator
< // comparison operator
>= // comparison operator
<= // comparison operator

// --- LOGICAL OPERATOR ---

and // logical AND
or // logical OR
not // logical NOT
```

## Control structures

```yh
// ----- CONTROL STRUCTURE -----
    // note that there are no loops in Yuho for obvious reasons
    // the obvious reason is this => what purpose would there be in looping over an iterable structure when we are dealing with statutes
    // just for completeness, recursion and traversal functions used for iteration (map, fold, filter) are also NOT supported
    // higher-order functions ARE supported in theory, but please don't write them

// --- CONDITIONALS ---
    // 


```

## Functions

```yh
// ----- FUNCTION -----

```

## Testing

```yh
// ----- TESTING -----
    // assert => 

```
