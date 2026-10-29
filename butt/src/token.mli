(** Tokens of the fixed lexer (architecture §2.1).

    Every token owns the trivia (whitespace and comments) that precedes it,
    so concatenating each token's trivia texts and its text, in order,
    reproduces the source byte-for-byte. The final [Eof] token owns any
    trailing trivia. *)

type delim = Paren | Bracket | Brace
type raw_form = Brace_form | Long_form of int  (** level n of [\[=ⁿ\[] *)

type kind =
  | Ident
  | Raw_ident of { name : Span.t }  (** the identifier between backticks *)
  | Int of { hex : bool; suffix : Span.t option }
  | Float of { suffix : Span.t option }
  | String  (** text includes the quotes; escapes are not decoded *)
  | Op
  | Punct
  | Open of delim
  | Close of delim
  | Raw_region of { tag : Span.t; form : raw_form; content : Span.t }
  | Eof

type trivia_kind = Whitespace | Line_comment | Long_comment of int

type trivia = {
  trivia_kind : trivia_kind;
  trivia_span : Span.t;
  trivia_text : string;
}

type t = {
  kind : kind;
  text : string;  (** exact source slice of [span] *)
  span : Span.t;
  space_before : bool;  (** any trivia immediately precedes the token *)
  newline_before : bool;  (** that trivia contains an LF *)
  leading_trivia : trivia list;
}

val kind_name : kind -> string
val delim_name : delim -> string
val open_char : delim -> char
val close_char : delim -> char

val reconstruct : t array -> string
(** Concatenation of all trivia and token texts. *)
