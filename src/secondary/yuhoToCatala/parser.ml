open Yojson.Basic.Util
open Ast

exception ParseError of string

let parse_literal json =
  match json with
  | `Int i -> LInt i
  | `Float f -> LFloat f
  | `String s -> LString s
  | `Bool b -> LBoolean b
  | _ -> raise (ParseError "Invalid literal")

let parse_typ json =
  match to_string json with
  | "int" -> TInt
  | "float" -> TFloat
  | "string" -> TString
  | "boolean" -> TBoolean
  | "money" -> TMoney
  | "date" -> TDate
  | "duration" -> TDuration
  | _ -> raise (ParseError "Invalid type")

let rec parse_expr json =
  match json with
  | `Assoc [("var", `String v)] -> Var v
  | `Assoc [("lit", lit)] -> Lit (parse_literal lit)
  | `Assoc [("unary_op", `List [`String op; expr])] -> UnaryOp (op, parse_expr expr)
  | `Assoc [("binary_op", `List [`String op; expr1; expr2])] ->
      BinaryOp (op, parse_expr expr1, parse_expr expr2)
  | _ -> raise (ParseError "Invalid expression")

let parse_stmt json =
  match json with
  | `Assoc [("variable_declaration", `List [typ; `String name; expr])] ->
      VariableDeclaration (parse_typ typ, name, parse_expr expr)
  | `Assoc [("function_declaration", `List [ret_typ; `String name; params; body])] ->
      let params = List.map (fun (`List [typ; `String name]) -> (parse_typ typ, name)) (to_list params) in
      FunctionDeclaration (parse_typ ret_typ, name, params, parse_expr body)
  | `Assoc [("scope", `List [`String name; stmts])] ->
      Scope (name, List.map parse_stmt (to_list stmts))
  | `Assoc [("struct", `List [`String name; fields])] ->
      let fields = List.map (fun (`List [typ; `String name]) -> (parse_typ typ, name)) (to_list fields) in
      Struct (name, fields)
  | `Assoc [("assertion", expr)] -> Assertion (parse_expr expr)
  | _ -> raise (ParseError "Invalid statement")

let parse_program json =
  match json with
  | `List stmts -> List.map parse_stmt stmts
  | _ -> raise (ParseError "Invalid program")
