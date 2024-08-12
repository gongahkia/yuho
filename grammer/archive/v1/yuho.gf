(* ----- YUHO lang V1.0 ----- *)

(* --- reference!!! --- *)
(* grammer here is specified under the EBNF standard notation *)
(* terminals => basic units of a language, eg. keywords, identifiers, operators *)
(* non-terminals => higher-level structures built from terminals *)

(* ---------- *)

(* lexical core *)
letter = "A" | "B" | "C" | "D" | "E" | "F" | "G" | "H" | "I" | "J" | "K" | "L" | "M" | "N" | "O" | "P" | "Q" | "R" | "S" | "T" | "U" | "V" | "W" | "X" | "Y" | "Z" | "a" | "b" | "c" | "d" | "e" | "f" | "g" | "h" | "i" | "j" | "k" | "l" | "m" | "n" | "o" | "p" | "q" | "r" | "s" | "t" | "u" | "v" | "w" | "x" | "y" | "z";
digit = "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9";
identifier = letter , { letter | digit };
integer = digit , { digit };
float = digit , { digit } , "." , digit , { digit };
string = "\"" , { letter | digit | " " | "!" | "#" | "$" | "%" | "&" | "'" | "(" | ")" | "*" | "+" | "," | "-" | "." | "/" | ":" | ";" | "<" | "=" | ">" | "?" | "@" | "[" | "]" | "^" | "_" | "`" | "{" | "|" | "}" | "~" } , "\"";
comment = "//" , { any character } | "/*" , { any character } , "*/";

(* datatypes *)
type = "integer" | "float" | "percent" | "money" | "date" | "duration" | "boolean" | "string" | identifier;
boolean = "TRUE" | "FALSE";
percent = integer , "%";
money = "$" , digit , { digit | "," } , "." , digit , digit;
date = digit , digit , "-" , digit , digit , "-" , digit , digit , digit , digit;
duration = integer , " " , ("day" | "month" | "year");

(* variable declaration *)
variable_declaration = "scope" , identifier , "{" , { type , identifier , ":=" , expression , ";" } , "}";
union_type = type , "|" , type;
pass_value = "pass";

(* data structures *)
struct_declaration = "struct" , identifier , "{" , { type , identifier , "," } , "}";
struct_literal = identifier , ":=" , "{" , { identifier , ":=" , expression , "," } , "}";

(* operators *)
arithmetic_operator = "+" | "-" | "*" | "/" | "//" | "%";
comparison_operator = "==" | "!=" | ">" | "<" | ">=" | "<=";
logical_operator = "and" | "or" | "not";

(* control structures *)
match_case = "match" , identifier , "{" , { "case" , expression , ":=" , expression , ";" } , "case" , "_" , ":=" , "pass" , ";" , "}";

(* functions *)
function_declaration = type , "func" , identifier , "(" , { type , identifier , "," } , ")" , "{" , { statement } , "}";
return_expression = ":=" , expression;

(* statements and expressions *)
statement = variable_declaration | struct_declaration | struct_literal | match_case | function_declaration | return_expression;
expression = identifier | integer | float | string | boolean | percent | money | date | duration | arithmetic_operator | comparison_operator | logical_operator;

(* program *)
program = { statement };