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
9. [Testing](#testing)

## Introduction

* Yuho source files have the file extension `.yh`
* strongly, statically-typed
* camelCase naming scheme
* indentation is optional but recommended for easier readability with multiple nested {} curly braces
* features limited syntax out of the box
    * allow for language to be quickly picked up and used
    * allow for detailed modelling of statute logic
    * not semicolon-delimited
* functional language
    * all values are immutable
    * every statement is an expression 
    * every expression evaluates to a single value
    * limited theoretical support for higher-order functions, functions are therefore 1.5 class citizens (not first class)
    * mimicks the logical and syntactical completeness of the law

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

## Variable Declaration

```yh
// ----- VARIABLE DECLARATION -----
    // := => provides a simultaneous immutable variable declaration and binding between a specified named variable identifier and its assigned value, wherein the value cannot be then reassigned or modified after its initial assignment
        // note that the datatype of any named variable is specified before the variable identifier similar to C++
        // every value in Yuho is therefore IMMUTABLE
    // scope => declares the lexical scope of a given section of Yuho code for modularity within {} curly braces, the equivalent of a namespace in most other C-style programming languages
        // . => scoped variables, structs and functions are then called via . dot syntax
        // also observe how this syntax is nearly identical to a struct's declaration

scope teachingVariableDeclaration {
    integer anInteger := 100
    float aFloat := 200.00
    string aString := "more examples are shown below fam"
}

teachingVariableDeclaration.anInteger // evaluates to 100
teachingVariableDeclaration.anFloat // evaluates to 200.00
teachingVariableDeclaration.anString // evaluates to "more examples are shown below fam"
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

## Data Structures

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

## Control Structures

```yh
// ----- CONTROL STRUCTURE -----
    // note that there are NO LOOPS in Yuho for obvious reasons
    // the obvious reason is this => what purpose would there be in looping over an iterable structure when we are dealing with statutes, there are no loops in statute definitions!
    // just for completeness, recursion and traversal functions used for iteration (map, fold, filter) are also NOT supported
    // higher-order functions ARE supported in theory, but please don't write them
    // they often create odd side-effects especially when written by those with little experience in functional languages, and we want Yuho to be as idiot-proof as possible

// --- CONDITIONALS ---
    // adhering to similar functional paradigms, Yuho provides for advanced pattern-matching capabilities as the one proper way to model conditional constructs with its match case constructs
    // there are therefore NO if else if else constructs in Yuho
    // this likewise mimicks the all-encompassing nature of statutory provisions, no exceptions can arise from Yuho lang and edge-cases are covered out of the box

// MATCH CASE _
    // match => declares the beginning of a match case construct within curly braces
    // case => specifies each predicate case condition that could arise from a match construct
    // := => delimits the relationship between a given case and its consequence
    // consequence => follows every case and exception condition as the resulting expression of a given case predicate being fulfilled
    // _ => catch-all fall-through default operator that executes when all other predicate case conditions fail to be met that MUST ALWAYS BE SPECIFIED to cover all edge cases
    // pass => skips execution and evaluaton of the current block, the equivalent of pass in other programming languages like Python
        // note that where a given fall-through default case has no code to evaluate, we just write pass (as seen below)
    // also observe that we can directly assign the result of a match case construct to variables similar to other functional languages

money currentBankAccount := $100,000.00

boolean brokeOrNot := match anExampleMatchValue {
    case currentBankAccount <= $200,000.00 := consequence TRUE
    case currentBankAccount > $200,000.00 := consequence FALSE
    case _ := consequence pass // since this is a boolean match statement, the _ case predicate in actuality will never run, so we leave the code as pass
} // here brokeOrNot evaluates in the back-end to TRUE
```

## Functions

```yh
// ----- FUNCTION -----
    // <returnValueDatatype> func <functionName> ( <parameterDatatype(s)> <parameterName(s)> ) { <functionDefinitionBody> }  => declaration and definition of a named function, very similar to how C-style languages handle function definition syntax
    // := => prefixes the function's return expression or value, equivalent to the return keyword in most other programming languages
        // similar to other functional languages, there are NO void types in Yuho, every function MUST return an established or user-defined datatype
    // though anonymous functions are theoretically supported in Yuho, we avoid them for the sake of simplicity, readability and clarity in function definition

int func aSimpleComputation (int a, int b) {
    := a + b // this is the return expression
}

float func aMoreComplexComputation (float c, float d, float e) {
    f := 100.00
    := c + d + e + f // this is the return expression
}
```

## Testing

```yh
// ----- TESTING -----
    // assert => asserts that the following expression on the same line always evaluates to boolean TRUE, and throws an error during tranpilation if it evaluates instead to boolean FALSE

// taking the function definition from before...

scope test1 {

    int func aSimpleComputation (int a, int b) { 
        := a + b 
    }

    assert aSimpleComputation(1, 2) == 3 // evaluates to TRUE
    assert aSimpleComputation(2, 3) == 5 // evaluates to TRUE
    assert aSimpleComputation(3, 4) == 6 // evaluates to FALSE, so throws an error and Yuho program ends here

}
```
