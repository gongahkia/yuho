%%{
  machine Yuho;

  # ----- token definitions -----

  COMMENT = "//" ~[\r\n]*;
  MULTILINE_COMMENT = "/*" .*? "*/";

  TRUE = "TRUE";
  FALSE = "FALSE";
  MATCH = "match";
  CASE = "case";
  CONSEQUENCE = "consequence";
  PASS = "pass";
  STRUCT = "struct";
  FN = "fn";
  PERCENT = "%";
  MONEY_PREFIX = "$";
  DATE_FORMAT = "DD-MM-YYYY";
  DURATION_UNITS = "day" | "month" | "year";

  IDENTIFIER = [a-zA-Z_] [a-zA-Z_0-9]*;
  DOT = ".";
  STRING = '"' [^"]* '"';
  INTEGER = [0-9]+;
  FLOAT = [0-9]+ "." [0-9]*;
  PERCENTAGE = INTEGER PERCENT;
  MONEY = MONEY_PREFIX [0-9]{1,3} ("," [0-9]{3})* "." [0-9]{2};
  DATE = [0-9]{2}-[0-9]{2}-[0-9]{4};
  DURATION = INTEGER (DURATION_UNITS ("," INTEGER DURATION_UNITS)*)?;

  PLUS = "+";
  MINUS = "-";
  MULT = "*";
  DIV = "/";
  ASSIGN = ":=";
  EQUAL = "==";
  NOTEQUAL = "!=";
  GT = ">";
  LT = "<";
  AND = "&&";
  OR = "||";
  SEMICOLON = ";";
  COLON = ":";
  LBRACE = "{";
  RBRACE = "}";
  LPAREN = "(";
  RPAREN = ")";
  COMMA = ",";
  UNDERSCORE = "_";

  # ----- state machine representation for the parser -----

  main := |*
    COMMENT { /* skip comments */ }
    | MULTILINE_COMMENT { /* skip multiline comments */ }
    | TRUE { /* handle TRUE token */ }
    | FALSE { /* handle FALSE token */ }
    | MATCH { /* handle MATCH token */ }
    | CASE { /* handle CASE token */ }
    | CONSEQUENCE { /* handle CONSEQUENCE token */ }
    | PASS { /* handle PASS token */ }
    | STRUCT { /* handle STRUCT token */ }
    | FN { /* handle FN token */ }
    | PERCENT { /* handle PERCENT token */ }
    | MONEY_PREFIX { /* handle MONEY_PREFIX token */ }
    | DATE_FORMAT { /* handle DATE_FORMAT token */ }
    | DURATION_UNITS { /* handle DURATION_UNITS token */ }
    | IDENTIFIER { /* handle IDENTIFIER token */ }
    | DOT { /* handle DOT token */ }
    | STRING { /* handle STRING token */ }
    | INTEGER { /* handle INTEGER token */ }
    | FLOAT { /* handle FLOAT token */ }
    | PERCENTAGE { /* handle PERCENTAGE token */ }
    | MONEY { /* handle MONEY token */ }
    | DATE { /* handle DATE token */ }
    | DURATION { /* handle DURATION token */ }
    | PLUS { /* handle PLUS token */ }
    | MINUS { /* handle MINUS token */ }
    | MULT { /* handle MULT token */ }
    | DIV { /* handle DIV token */ }
    | ASSIGN { /* handle ASSIGN token */ }
    | EQUAL { /* handle EQUAL token */ }
    | NOTEQUAL { /* handle NOTEQUAL token */ }
    | GT { /* handle GT token */ }
    | LT { /* handle LT token */ }
    | AND { /* handle AND token */ }
    | OR { /* handle OR token */ }
    | SEMICOLON { /* handle SEMICOLON token */ }
    | COLON { /* handle COLON token */ }
    | LBRACE { /* handle LBRACE token */ }
    | RBRACE { /* handle RBRACE token */ }
    | LPAREN { /* handle LPAREN token */ }
    | RPAREN { /* handle RPAREN token */ }
    | COMMA { /* handle COMMA token */ }
    | UNDERSCORE { /* handle UNDERSCORE token */ }
    ;
  *|;
}%%
