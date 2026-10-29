(* Exit codes: 0 success (warnings allowed), 1 lexical or delimiter error,
   2 usage error, 3 input could not be read. *)

open Front

let usage =
  "usage: lexdump (tokens [--trivia] | trees | check) FILE\n\
  \  tokens   dump the token stream (format tokens/2)\n\
  \  trees    dump the token trees (format trees/2)\n\
  \  check    report diagnostics only\n"

type mode = Tokens of bool | Trees | Check

let parse_args = function
  | [ "tokens"; file ] -> Some (Tokens false, file)
  | [ "tokens"; "--trivia"; file ] | [ "tokens"; file; "--trivia" ] ->
      Some (Tokens true, file)
  | [ "trees"; file ] -> Some (Trees, file)
  | [ "check"; file ] -> Some (Check, file)
  | _ -> None

let report src diags =
  List.iter (fun d -> prerr_string (Diagnostic.render src d)) diags;
  flush stderr

let run mode file =
  match In_channel.with_open_bin file In_channel.input_all with
  | exception Sys_error msg ->
      Printf.eprintf "lexdump: cannot read input: %s\n" (Escape.display msg);
      3
  | text -> (
      let src = Source.make ~name:file text in
      match Lexer.lex src with
      | Error d ->
          report src [ d ];
          1
      | Ok { tokens; warnings } -> (
          report src warnings;
          match mode with
          | Tokens trivia ->
              print_string (Dump.tokens ~trivia src tokens);
              0
          | Trees | Check -> (
              match Reader.read tokens with
              | Error (Reader.Unbalanced d) ->
                  report src [ d ];
                  1
              | Error (Reader.Invalid_input e) ->
                  Printf.eprintf "lexdump: internal error: %s\n"
                    (Reader.describe_input_error e);
                  1
              | Ok r ->
                  (match mode with
                  | Trees -> print_string (Dump.trees src r)
                  | _ ->
                      Printf.printf "ok: %d tokens, %d top-level trees\n"
                        (Array.length tokens) (List.length r.trees));
                  0)))

let () =
  let code =
    match parse_args (List.tl (Array.to_list Sys.argv)) with
    | None ->
        prerr_string usage;
        2
    | Some (mode, file) -> run mode file
  in
  flush stdout;
  flush stderr;
  exit code
