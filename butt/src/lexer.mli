(** The fixed lexer (architecture §2.1). Grammar declarations never affect
    it, so the same bytes always produce the same tokens. *)

type output = {
  tokens : Token.t array;  (** non-empty; the last token is [Eof] *)
  warnings : Diagnostic.t list;  (** in source order *)
}

val lex : Source.t -> (output, Diagnostic.t) result
(** The whole input is first validated as UTF-8; lexing then stops at the
    first error. Never raises on any input. *)

val first_invalid_utf8 : string -> int option
(** Offset of the first byte that does not begin a well-formed UTF-8
    sequence (RFC 3629: no overlongs, surrogates, or values above U+10FFFF). *)
