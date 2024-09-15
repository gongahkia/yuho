%{
#include "y.tab.h"
%}

%%

[A-Za-z]([A-Za-z0-9])*           { return IDENTIFIER; }
[0-9]+                           { return INTEGER; }
[0-9]+"."[0-9]+                  { return FLOAT; }
\"([^\"\n])*\"                   { return STRING; }
"//".*                           { /* ignore comment */ }
"/*"([^*]|\*+[^/*])*\*+"/"       { /* ignore comment */ }
"scope"                          { return SCOPE; }
"pass"                           { return PASS; }
"struct"                         { return STRUCT; }
"func"                           { return FUNC; }
"return"                         { return RETURN; }
"match"                          { return MATCH; }
"case"                           { return CASE; }
"TRUE"                           { return TRUE; }
"FALSE"                          { return FALSE; }
"integer"                        { return INTEGER_TYPE; }
"float"                          { return FLOAT_TYPE; }
"percent"                        { return PERCENT_TYPE; }
"money"                          { return MONEY_TYPE; }
"date"                           { return DATE_TYPE; }
"duration"                       { return DURATION_TYPE; }
"boolean"                        { return BOOLEAN_TYPE; }
"string"                         { return STRING_TYPE; }
"+"                              { return PLUS; }
"-"                              { return MINUS; }
"*"                              { return MULTIPLY; }
"/"                              { return DIVIDE; }
"//"                             { return DIVIDE_INT; }
"%"                              { return MOD; }
"=="                             { return EQUAL; }
"!="                             { return NOT_EQUAL; }
">"                              { return GREATER; }
"<"                              { return LESS; }
">="                             { return GREATER_EQUAL; }
"<="                             { return LESS_EQUAL; }
"and"                            { return AND; }
"or"                             { return OR; }
"not"                            { return NOT; }
":="                             { return ASSIGN; }
[ \t\n]+                         { /* ignore whitespace */ }
.                                { /* ignore any other character */ }

%%

int yywrap(void) {
    return 1;
}

int main(int argc, char **argv) {
    yylex();
    return 0;
}
