(* ----- YUHO lang V1.0 ----- *)

(* --- reference!!! --- *)
    (* grammer here is specified under the EBNF standard notation *)
    (* terminals => basic units of a language, eg. keywords, identifiers, operators *)
    (* non-terminals => higher-level structures built from terminals *)

(* --- note!!! --- *)
    (* YUHO grammer is a work in progress and subject to change *)
    (* take nothing here as final until otherwise specified *)

(* ---------- *)

(* --- keyword --- *)

keyword ::= "if" 
        | "else" 
        | "else if"
        | "for" (* same for-loop syntax as go *)
        | "fn"
        | statute_specification
        | charge
        | client 
        | party

(* --- statutes --- *)
    (* => for referencing statutes in documentation *)

statute_specification ::= statute "_S" section ( "." subsection )*
charge ::= statute_specification "_" ( damage "_" )* ( punishment )*

statute ::= string 
section ::= integer
section_title ::= string
subsection ::= integer
subsection_title ::= string
statute_body ::= string

(* --- damages --- *)
    (* => for referencing damages in documentation *)

damage ::= non_monetary_damage
        | monetary_damage
non_monetary_damage ::= string
monetary_damage ::= "S$" integer 

(* --- punishment --- *)
    (* => for referencing punishments in documentation *)

punishment ::= string
            | integer "_counts_of_" punishment

(* --- parties --- *)
    (* => for referencing your client and parties in documentation *)

client ::= party

party ::= plaintiff
        | defendant
        | third_party
        | other_party

plaintiff ::= "P" integer* "_" party_name
defendant ::= "D" integer* "_" party_name
third_party ::= "T" integer* "_" party_name
other_party ::= "O" integer* "_" party_name
party_name ::= string

(* --- identifier --- *)
    (* => YUHO identifier naming scheme is camel_case by default *)

identifier ::= char { char | digit | "_" } 
                                            
(* --- literal --- *)
    (* => note that there is no char datatype in yuho, this is just for formal specification *)
    (* => note that there is also no digit datatype in yuho, this is just for formal specification *)
    (* => above 2 notes are relevant for typecasting *)

char ::= "a" .. "z" 
string ::= '"' char+ '"' (* all text in yuho is a string by default as long as its enclosed by double quotes *)
digit ::= "0" .. "9"
integer ::= "-"? digit+ (* signed and unsigned integers *)
float ::= "-"? digit+ "." digit+ (* floating point number, there are no doubles in yuho *)
boolean ::= "TRUE"
        | "FALSE"

(* --- operators --- *)
    (* => assignment *)
    (* => basic arithmetic *)
    (* => comparison *)

operator = assignment_operator
        | mathematical_operator
        | comparison_operator

assignment_operator = "="

mathematical_operator = "+" 
                    | "-" 
                    | "*" 
                    | "/" 

comparison_operator = "<" 
                    | ">" 
                    | "<=" 
                    | ">=" 
                    | "==" 
                    | "!=" 

(* --- expression --- *)
    (* => includes defintion for mathematical and generic expressions *)
    (* => recursive definition for nested expressions *)

expression ::= generic_expression*
            | mathematical_expression*
            | expression*

generic_expression ::= expression expression+ 
                    | expression "(" identifier ")" (* function call *)
                    | identifier

mathematical_expression ::= term 
                        | term operator mathematical_expression

term ::= factor 
        | factor '*' term

factor ::= "(" mathematical_expression ")" 
        | ( integer | float )

(* --- statements --- *)
    (* => variable assignment *)
    (* => control flow statements eg. if, for-loop *)
    (* => yuho features implicit returns *)

statement = identifier "=" expression
         | keyword statement_body 

(* --- statement body --- *)
    (* => one or more statements enclosed within curly braces *)

statement_body = "{" statement+ "}" 

(* --- comment --- *)
    (* => anthing following a // on the same line *)

comment ::= "//" ( string* | integer* | float* | statement* )

(* --- program --- *)
    (* => zero or more statements *)
    (* => zero or more statement bodies *)

program ::= statement* 
        | statement_body*
