%{
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// ----- token types -----

enum yytokentype {
    COMMENT = 258,
    MULTILINE_COMMENT,
    TRUE,
    FALSE,
    MATCH,
    CASE,
    CONSEQUENCE,
    PASS,
    STRUCT,
    FN,
    PERCENT,
    MONEY_PREFIX,
    DATE_FORMAT,
    DURATION_UNITS,
    IDENTIFIER,
    DOT,
    STRING,
    INTEGER,
    FLOAT,
    PERCENTAGE,
    MONEY,
    DATE,
    DURATION,
    PLUS = 43,
    MINUS,
    MULT,
    DIV,
    ASSIGN,
    EQUAL,
    NOTEQUAL,
    GT,
    LT,
    AND,
    OR,
    SEMICOLON = 59,
    COLON,
    LBRACE,
    RBRACE,
    LPAREN,
    RPAREN,
    COMMA,
    UNDERSCORE
};

void yyerror(const char *s);
int yylex(void);

%}

%token COMMENT MULTILINE_COMMENT TRUE FALSE MATCH CASE CONSEQUENCE PASS STRUCT FN PERCENT MONEY_PREFIX DATE_FORMAT DURATION_UNITS
%token IDENTIFIER DOT STRING INTEGER FLOAT PERCENTAGE MONEY DATE DURATION
%token PLUS MINUS MULT DIV ASSIGN EQUAL NOTEQUAL GT LT AND OR SEMICOLON COLON LBRACE RBRACE LPAREN RPAREN COMMA UNDERSCORE

%%
program:
    declarations
    | functionDefinitions
    | structDefinitions
    | matchCases
    ;

declarations:
    declarations declaration
    | declaration
    ;

declaration:
    type IDENTIFIER ASSIGN expression SEMICOLON
    | type IDENTIFIER SEMICOLON
    ;

type:
    'int'
    | 'float'
    | 'percent'
    | 'money'
    | 'date'
    | 'duration'
    | 'bool'
    | 'string'
    | IDENTIFIER
    ;

expression:
    expression PLUS expression
    | expression MINUS expression
    | expression MULT expression
    | expression DIV expression
    | expression GT expression
    | expression LT expression
    | expression EQUAL expression
    | expression NOTEQUAL expression
    | expression AND expression
    | expression OR expression
    | IDENTIFIER
    | IDENTIFIER DOT IDENTIFIER
    | literal
    ;

literal:
    STRING
    | INTEGER
    | FLOAT
    | PERCENTAGE
    | MONEY
    | DATE
    | DURATION
    | TRUE
    | FALSE
    ;

statement:
    declaration
    | assignment
    | functionCall
    | matchCase
    | passStatement
    ;

assignment:
    IDENTIFIER ASSIGN expression SEMICOLON
    ;

matchCase:
    MATCH LPAREN expression RPAREN LBRACE caseClauses RBRACE
    ;

caseClauses:
    caseClauses caseClause
    | caseClause
    ;

caseClause:
    CASE expression ASSIGN CONSEQUENCE expression SEMICOLON
    | CASE UNDERSCORE ASSIGN CONSEQUENCE passStatement SEMICOLON
    ;

passStatement:
    PASS SEMICOLON
    ;

functionDefinitions:
    functionDefinitions functionDefinition
    | functionDefinition
    ;

functionDefinition:
    FN IDENTIFIER LPAREN parameterList RPAREN COLON type block
    ;

parameterList:
    parameterList COMMA parameter
    | parameter
    | /* empty */
    ;

parameter:
    type IDENTIFIER
    ;

functionCall:
    IDENTIFIER LPAREN argumentList RPAREN SEMICOLON
    ;

argumentList:
    argumentList COMMA expression
    | expression
    | /* empty */
    ;

structDefinitions:
    structDefinitions structDefinition
    | structDefinition
    ;

structDefinition:
    STRUCT IDENTIFIER LBRACE structMembers RBRACE
    ;

structMembers:
    structMembers structMember
    | structMember
    ;

structMember:
    type IDENTIFIER SEMICOLON
    ;

block:
    LBRACE statements RBRACE
    ;

statements:
    statements statement
    | statement
    ;
%%

void yyerror(const char *s) {
    fprintf(stderr, "Error: %s\n", s);
}

int main(void) {
    yyparse();
    return 0;
}
