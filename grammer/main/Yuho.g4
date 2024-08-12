grammar Yuho;

// ----- lexical rules -----

COMMENT: '//' ~[\r\n]* -> skip;
MULTILINE_COMMENT: '/*' .*? '*/' -> skip;

TRUE: 'TRUE';
FALSE: 'FALSE';
MATCH: 'match';
CASE: 'case';
CONSEQUENCE: 'consequence';
PASS: 'pass';
STRUCT: 'struct';
FN: 'fn';
PERCENT: '%';
MONEY_PREFIX: '$';

DAY: 'day';
MONTH: 'month';
YEAR: 'year';
DURATION_UNITS: DAY | MONTH | YEAR;

IDENTIFIER: [a-zA-Z_][a-zA-Z_0-9]*;
DOT: '.';

STRING: '"' .*? '"';
INTEGER: [0-9]+;
FLOAT: [0-9]+ '.' [0-9]*;
PERCENTAGE: INTEGER PERCENT;
MONEY: MONEY_PREFIX [0-9]{1,3}(',' [0-9]{3})* '.' [0-9]{2};
DATE: [0-9]{2} '-' [0-9]{2} '-' [0-9]{4};
DURATION: INTEGER (DURATION_UNITS (',' INTEGER DURATION_UNITS)*)?;

PLUS: '+';
MINUS: '-';
MULT: '*';
DIV: '/';
ASSIGN: ':=';
EQUAL: '==';
NOTEQUAL: '!=';
GT: '>';
LT: '<';
AND: '&&';
OR: '||';

SEMICOLON: ';';
COLON: ':';
LBRACE: '{';
RBRACE: '}';
LPAREN: '(';
RPAREN: ')';
COMMA: ',';
UNDERSCORE: '_';

WS: [ \t\r\n]+ -> skip;

// ----- parser rules -----

program: (declaration | functionDefinition | structDefinition | matchCase)* EOF;

declaration: type IDENTIFIER ASSIGN expression SEMICOLON
           | type IDENTIFIER SEMICOLON;

type: 'int' | 'float' | 'percent' | 'money' | 'date' | 'duration' | 'bool' | 'string' | IDENTIFIER;

expression: expression (PLUS | MINUS | MULT | DIV) expression
          | expression (GT | LT | EQUAL | NOTEQUAL) expression
          | expression (AND | OR) expression
          | IDENTIFIER
          | IDENTIFIER DOT IDENTIFIER  
          | literal;

literal: STRING | INTEGER | FLOAT | PERCENTAGE | MONEY | DATE | DURATION | TRUE | FALSE;

statement: declaration
         | assignment
         | functionCall
         | matchCase
         | passStatement;

assignment: IDENTIFIER ASSIGN expression SEMICOLON;

matchCase: MATCH (LPAREN expression RPAREN)? LBRACE caseClause* RBRACE;

caseClause: CASE expression ASSIGN CONSEQUENCE expression SEMICOLON
           | CASE UNDERSCORE ASSIGN CONSEQUENCE passStatement SEMICOLON;

passStatement: PASS SEMICOLON;

functionDefinition: FN IDENTIFIER LPAREN parameterList RPAREN COLON type block;

parameterList: (parameter (COMMA parameter)*)?;

parameter: type IDENTIFIER;

functionCall: IDENTIFIER LPAREN argumentList RPAREN SEMICOLON;

argumentList: (expression (COMMA expression)*)?;

structDefinition: STRUCT IDENTIFIER LBRACE structMember* RBRACE;

structMember: type IDENTIFIER (COMMA | SEMICOLON);

block: LBRACE statement* RBRACE;
