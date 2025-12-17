# ----- token definitions -----

token COMMENT {\/\/[^\r\n]*}
token MULTILINE_COMMENT {\/\*[^*]*\*+([^/*][^*]*\*+)*\/}
token TRUE {TRUE}
token FALSE {FALSE}
token MATCH {match}
token CASE {case}
token CONSEQUENCE {consequence}
token PASS {pass}
token STRUCT {struct}
token FN {fn}
token PERCENT {%}
token MONEY_PREFIX {\$}
token DATE_FORMAT {DD-MM-YYYY}
token DURATION_UNITS {day|month|year}
token IDENTIFIER {[_a-zA-Z][_a-zA-Z0-9]*}
token DOT {\.}
token STRING {"[^"]*"}
token INTEGER {[0-9]+}
token FLOAT {[0-9]+\.[0-9]*}
token PERCENTAGE {INTEGER%}
token MONEY {\$[0-9]{1,3}(,[0-9]{3})*\.[0-9]{2}}
token DATE {[0-9]{2}-[0-9]{2}-[0-9]{4}}
token DURATION {INTEGER (DURATION_UNITS (,{INTEGER DURATION_UNITS})*)?}
token PLUS {\+}
token MINUS {-}
token MULT {\*}
token DIV {/}
token ASSIGN {: =}
token EQUAL {==}
token NOTEQUAL {!=}
token GT {>}
token LT {<}
token AND {&&}
token OR {\|\|}
token SEMICOLON {;}
token COLON {:}
token LBRACE {\{}
token RBRACE {\}}
token LPAREN {\(}
token RPAREN {\)}
token COMMA {,}
token UNDERSCORE {_}

# ----- grammar rules -----

program: (declaration | functionDefinition | structDefinition | matchCase)* EOF
declaration: type IDENTIFIER ASSIGN expression SEMICOLON | type IDENTIFIER SEMICOLON
type: int | float | percent | money | date | duration | bool | string | IDENTIFIER
expression: expression (PLUS | MINUS | MULT | DIV) expression | expression (GT | LT | EQUAL | NOTEQUAL) expression | expression (AND | OR) expression | IDENTIFIER | IDENTIFIER DOT IDENTIFIER | literal
literal: STRING | INTEGER | FLOAT | PERCENTAGE | MONEY | DATE | DURATION | TRUE | FALSE
statement: declaration | assignment | functionCall | matchCase | passStatement
assignment: IDENTIFIER ASSIGN expression SEMICOLON
matchCase: MATCH (LPAREN expression RPAREN)? LBRACE caseClause* RBRACE
caseClause: CASE expression ASSIGN CONSEQUENCE expression SEMICOLON | CASE UNDERSCORE ASSIGN CONSEQUENCE passStatement SEMICOLON
passStatement: PASS SEMICOLON
functionDefinition: FN IDENTIFIER LPAREN parameterList RPAREN COLON type block
parameterList: (parameter (COMMA parameter)*)?
parameter: type IDENTIFIER
functionCall: IDENTIFIER LPAREN argumentList RPAREN SEMICOLON
argumentList: (expression (COMMA expression)*)?
structDefinition: STRUCT IDENTIFIER LBRACE structMember* RBRACE
structMember: type IDENTIFIER (COMMA | SEMICOLON)
block: LBRACE statement* RBRACE
