type severity = Error | Warning

type code =
  | Lex_utf8
  | Lex_char
  | Lex_comment
  | Lex_string
  | Lex_escape
  | Lex_raw
  | Lex_raw_ident
  | Lex_unbalanced
  | Lex_comment_after_operand

type note = { note_span : Span.t; note_message : string }
type t = { code : code; message : string; primary : Span.t; notes : note list }

let make ?(notes = []) code primary message = { code; message; primary; notes }
let note note_span note_message = { note_span; note_message }

let code_name = function
  | Lex_utf8 -> "E-LEX-UTF8"
  | Lex_char -> "E-LEX-CHAR"
  | Lex_comment -> "E-LEX-COMMENT"
  | Lex_string -> "E-LEX-STRING"
  | Lex_escape -> "E-LEX-ESCAPE"
  | Lex_raw -> "E-LEX-RAW"
  | Lex_raw_ident -> "E-LEX-RAW-IDENT"
  | Lex_unbalanced -> "E-LEX-UNBALANCED"
  | Lex_comment_after_operand -> "W-LEX-COMMENT-AFTER-OPERAND"

let severity d =
  match d.code with Lex_comment_after_operand -> Warning | _ -> Error

let location src (s : Span.t) =
  let line, col = Source.line_col src s.start in
  Printf.sprintf "%s:%d:%d %s" (Escape.display s.file) line col (Span.to_string s)

let render src d =
  let b = Buffer.create 128 in
  let sev = match severity d with Error -> "error" | Warning -> "warning" in
  Printf.bprintf b "%s: %s[%s]: %s\n" (location src d.primary) sev
    (code_name d.code) (Escape.display d.message);
  List.iter
    (fun n ->
      Printf.bprintf b "%s: note: %s\n" (location src n.note_span)
        (Escape.display n.note_message))
    d.notes;
  Buffer.contents b
