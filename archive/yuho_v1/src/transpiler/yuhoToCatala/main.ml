open Yojson.Basic
open Parser
open Transpiler

let () =
  let input_file = Sys.argv.(1) in
  let json = Yojson.Basic.from_file input_file in
  let program = parse_program json in
  let catala_code = string_of_program program in
  print_endline catala_code
