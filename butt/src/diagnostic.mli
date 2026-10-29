(** Lexical and delimiter diagnostics with stable codes. *)

type severity = Error | Warning

type code =
  | Lex_utf8  (** [E-LEX-UTF8] *)
  | Lex_char  (** [E-LEX-CHAR] *)
  | Lex_comment  (** [E-LEX-COMMENT] *)
  | Lex_string  (** [E-LEX-STRING] *)
  | Lex_escape  (** [E-LEX-ESCAPE] *)
  | Lex_raw  (** [E-LEX-RAW] *)
  | Lex_raw_ident  (** [E-LEX-RAW-IDENT] *)
  | Lex_unbalanced  (** [E-LEX-UNBALANCED] *)
  | Lex_comment_after_operand  (** [W-LEX-COMMENT-AFTER-OPERAND] *)

type note = { note_span : Span.t; note_message : string }

type t = private {
  code : code;
  message : string;
  primary : Span.t;
  notes : note list;
}

val make : ?notes:note list -> code -> Span.t -> string -> t
val note : Span.t -> string -> note
val code_name : code -> string
val severity : t -> severity

val render : Source.t -> t -> string
(** One line for the primary span followed by one line per note, each of the
    form [file:line:col \[start,stop): ...], newline-terminated. The file
    name and messages pass through {!Escape.display}. *)
