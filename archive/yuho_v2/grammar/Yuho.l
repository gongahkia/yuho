%{
#include "y.tab.h"
%}

COMMENT
    "//"[^'\n']*  { /* Ignore */ }

MULTILINE_COMMENT
    "/*"([^*]|\*+[^*/])*\*+"/"  { /* Ignore */ }

TRUE              { return TRUE; }
FALSE             { return FALSE; }
MATCH             { return MATCH; }
CASE              { return CASE; }
CONSEQUENCE       { return CONSEQUENCE; }
PASS              { return PASS; }
STRUCT            { return STRUCT; }
FN                { return FN; }
PERCENT           { return PERCENT; }
MONEY_PREFIX      { return MONEY_PREFIX; }
DATE_FORMAT       { return DATE_FORMAT; }
DURATION_UNITS    { return DURATION_UNITS; }

IDENTIFIER        [a-zA-Z_][a-zA-Z_0-9]*
DOT               { return DOT; }

STRING            "\""([^"\n]|\\")* "\"" { yylval.sval = strdup(yytext); return STRING; }
INTEGER           [0-9]+ { yylval.ival = atoi(yytext); return INTEGER; }
FLOAT             [0-9]*"."[0-9]+ { yylval.fval = atof(yytext); return FLOAT; }
PERCENTAGE        { return PERCENTAGE; }
MONEY             "$"[0-9]+(,[0-9]{3})*"."[0-9]{2} { yylval.sval = strdup(yytext); return MONEY; }
DATE              [0-9]{2}-[0-9]{2}-[0-9]{4} { yylval.sval = strdup(yytext); return DATE; }
DURATION          [0-9]+("day"|"month"|"year") { yylval.sval = strdup(yytext); return DURATION; }

PLUS              { return PLUS; }
MINUS             { return MINUS; }
MULT              { return MULT; }
DIV               { return DIV; }
ASSIGN            { return ASSIGN; }
EQUAL             { return EQUAL; }
NOTEQUAL          { return NOTEQUAL; }
GT                { return GT; }
LT                { return LT; }
AND               { return AND; }
OR                { return OR; }

SEMICOLON         { return SEMICOLON; }
COLON             { return COLON; }
LBRACE            { return LBRACE; }
RBRACE            { return RBRACE; }
LPAREN            { return LPAREN; }
RPAREN            { return RPAREN; }
COMMA             { return COMMA; }
UNDERSCORE       { return UNDERSCORE; }

[ \t\r\n]+        { /* Ignore whitespace */ }
.                 { printf("Unexpected character: %s\n", yytext); }

%%

int yywrap(void) {
    return 1;
}
