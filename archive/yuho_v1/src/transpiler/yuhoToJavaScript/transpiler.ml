open ast

let rec transpile_literal = function
  | LInt i -> string_of_int i
  | LFloat f -> string_of_float f
  | LString s -> "\"" ^ s ^ "\""
  | LBoolean b -> string_of_bool b

let transpile_type = function
  | TInt -> "number"
  | TFloat -> "number"
  | TString -> "string"
  | TBoolean -> "boolean"
  | TMoney -> "number"
  | TDate -> "Date"
  | TDuration -> "number"

let rec transpile_expr = function
  | Var v -> v
  | Lit l -> transpile_literal l
  | UnaryOp (op, e) -> "(" ^ op ^ transpile_expr e ^ ")"
  | BinaryOp (op, e1, e2) -> "(" ^ transpile_expr e1 ^ " " ^ op ^ " " ^ transpile_expr e2 ^ ")"

let rec transpile_stmt = function
  | VariableDeclaration (typ, name, expr) ->
      "let " ^ name ^ " = " ^ transpile_expr expr ^ ";"
  | FunctionDeclaration (ret_type, name, params, body) ->
      let params_str = String.concat ", " (List.map (fun (_, n) -> n) params) in
      "function " ^ name ^ "(" ^ params_str ^ ") { return " ^ transpile_expr body ^ "; }"
  | Scope (name, stmts) ->
      "let " ^ name ^ " = (function() {" ^ String.concat " " (List.map transpile_stmt stmts) ^ "})();"
  | Struct (name, fields) ->
      let fields_str = String.concat ", " (List.map (fun (_, n) -> n ^ ": null") fields) in
      "function " ^ name ^ "() { return {" ^ fields_str ^ "}; }"
  | Assertion expr ->
      "console.assert(" ^ transpile_expr expr ^ ");"

let transpile_program (prog: program) : string =
  String.concat "\n" (List.map transpile_stmt prog)

(* Example usage *)

let example_program: program = [
  VariableDeclaration (TInt, "x", Lit (LInt 42));
  FunctionDeclaration (TInt, "add", [(TInt, "a"); (TInt, "b")], BinaryOp ("+", Var "a", Var "b"));
  Assertion (BinaryOp ("==", Var "x", Lit (LInt 42)));
]

let () =
  let js_code = transpile_program example_program in
  print_endline js_code
