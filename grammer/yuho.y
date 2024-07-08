%{
#include <stdio.h>
#include <stdlib.h>

void yyerror(const char *s);
int yylex(void);
%}

%token LETTER DIGIT IDENTIFIER INTEGER FLOAT STRING COMMENT
%token INTEGER_TYPE FLOAT_TYPE PERCENT_TYPE MONEY_TYPE DATE_TYPE DURATION_TYPE BOOLEAN_TYPE STRING_TYPE TRUE FALSE
%token SCOPE PASS STRUCT FUNC RETURN MATCH CASE
%token PLUS MINUS MULTIPLY DIVIDE DIVIDE_INT MOD EQUAL NOT_EQUAL GREATER LESS GREATER_EQUAL LESS_EQUAL AND OR NOT

%%

program
    : statement_list
    ;

statement_list
    : statement_list statement
    | /* empty */
    ;

statement
    : variable_declaration
    | struct_declaration
    | struct_literal
    | match_case
    | function_declaration
    | return_expression
    ;

variable_declaration
    : SCOPE IDENTIFIER '{' variable_declaration_body '}'
    ;

variable_declaration_body
    : variable_declaration_body type IDENTIFIER ASSIGN expression ';'
    | /* empty */
    ;

struct_declaration
    : STRUCT IDENTIFIER '{' struct_declaration_body '}'
    ;

struct_declaration_body
    : struct_declaration_body type IDENTIFIER ','
    | /* empty */
    ;

struct_literal
    : IDENTIFIER ASSIGN '{' struct_literal_body '}'
    ;

struct_literal_body
    : struct_literal_body IDENTIFIER ASSIGN expression ','
    | /* empty */
    ;

match_case
    : MATCH IDENTIFIER '{' match_case_body 'case' '_' ASSIGN PASS ';' '}'
    ;

match_case_body
    : match_case_body 'case' expression ASSIGN expression ';'
    | /* empty */
    ;

function_declaration
    : type FUNC IDENTIFIER '(' function_parameters ')' '{' statement_list '}'
    ;

function_parameters
    : function_parameters type IDENTIFIER ','
    | /* empty */
    ;

return_expression
    : ASSIGN expression
    ;

expression
    : IDENTIFIER
    | INTEGER
    | FLOAT
    | STRING
    | boolean
    | percent
    | money
    | date
    | duration
    | arithmetic_operator
    | comparison_operator
    | logical_operator
    ;

boolean
    : TRUE
    | FALSE
    ;

percent
    : INTEGER '%'
    ;

money
    : '$' INTEGER '.' DIGIT DIGIT
    ;

date
    : DIGIT DIGIT '-' DIGIT DIGIT '-' DIGIT DIGIT DIGIT DIGIT
    ;

duration
    : INTEGER ' ' duration_unit
    ;

duration_unit
    : DAY
    | MONTH
    | YEAR
    ;

arithmetic_operator
    : PLUS
    | MINUS
    | MULTIPLY
    | DIVIDE
    | DIVIDE_INT
    | MOD
    ;

comparison_operator
    : EQUAL
    | NOT_EQUAL
    | GREATER
    | LESS
    | GREATER_EQUAL
    | LESS_EQUAL
    ;

logical_operator
    : AND
    | OR
    | NOT
    ;

type
    : INTEGER_TYPE
    | FLOAT_TYPE
    | PERCENT_TYPE
    | MONEY_TYPE
    | DATE_TYPE
    | DURATION_TYPE
    | BOOLEAN_TYPE
    | STRING_TYPE
    | IDENTIFIER
    ;

%%
void yyerror(const char *s) {
    fprintf(stderr, "Error: %s\n", s);
}

int main(void) {
    return yyparse();
}
