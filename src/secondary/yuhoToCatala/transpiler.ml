open Ast

let rec string_of_literal = function
  | LInt i -> string_of_int i
  | LFloat f -> string_of_float f
  | LString s -> "\"" ^ s ^ "\""
  | LBoolean b -> string_of_bool b

let string_of_typ = function
  | TInt -> "int"
  | TFloat -> "float"
  | TString -> "string"
  | TBoolean -> "boolean"
  | TMoney -> "money"
  | TDate -> "date"
  | TDuration -> "duration"

let rec string_of_expr = function
  | Var v -> v
  | Lit l -> string_of_literal l
  | UnaryOp (op, e) -> op ^ " " ^ string_of_expr e
  | BinaryOp (op, e1, e2) -> string_of_expr e1 ^ " " ^ op ^ " " ^ string_of_expr e2

let rec string_of_stmt = function
  | VariableDeclaration (typ, name, expr) ->
      Printf.sprintf "let %s : %s = %s;" name (string_of_typ typ) (string_of_expr expr)
  | FunctionDeclaration (ret_typ, name, params, body) ->
      let params = List.map (fun (typ, name) -> Printf.sprintf "%s %s" (string_of_typ typ) name) params in
      Printf.sprintf "function %s(%s) : %s {\n%s\n}" name (String.concat ", " params) (string_of_typ ret_typ) (string_of_expr body)
  | Scope (name, stmts) ->
      Printf.sprintf "scope %s {\n%s\n}" name (String.concat "\n" (List.map string_of_stmt stmts))
  | Struct (name, fields) ->
      let fields = List.map (fun (typ, name) -> Printf.sprintf "%s %s" (string_of_typ typ) name) fields in
      Printf.sprintf "struct %s {\n%s\n}" name (String.concat "\n" fields)
  | Assertion expr -> Printf.sprintf "assert %s;" (string_of_expr expr)

let string_of_program prog =
  String.concat "\n" (List.map string_of_stmt prog)
