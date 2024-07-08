# `Yuho` language syntax

## Introduction

* file extension of `.yh`
* simple limited syntax out of the box
* allow for detailed modelling of statute logic
* functional language
    * all values are immutable
    * every statement is an expression 
    * every expression evaluates to a single value
* strongly, statically-typed
* camelCase naming scheme
* not semicolon-delimited

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
    // string => declared within '' single quotation marks
        // these are rarely used as they are 

boolean anExampleBoolean := TRUE
string anExampleString := 'if the act by which the death is caused is done with the intention of causing death'
```

## Control structures

```yh
// ----- CONTROL STRUCTURE -----

```

## Data structures

```yh
// ----- DATA STRUCTURE -----

```

## Functions

```yh
// ----- FUNCTION -----

```
