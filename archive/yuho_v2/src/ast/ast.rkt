#lang racket

(require token)

(define-type AST
    [model (list AST)]
    [declaration (type string string (optional AST))]
    [type (string)]
    [logical-expression (list AST)]
    [relational-expression (list AST)]
    [additive-expression (list AST)]
    [multiplicative-expression (list AST)]
    [primary-expression (string)]
    [expression (AST)]
    [literal (token)]
    [statement (AST)]
    [assignment (string AST)]
    [match-case (AST (list case-clause))]
    [case-clause (AST string AST)]
    [pass-statement]
    [function-definition (string (list parameter) string (list AST))]
    [parameter (string string)]
    [function-call (string (list AST))]
    [struct-definition (string (list struct-member))]
    [struct-member (string string)]
    [entry-point (list AST)]
    [program (list AST)])