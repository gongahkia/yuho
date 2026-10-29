(** Token trees over [()], [\[\]] and [{}] (architecture §2.1.5, §2.6.1).

    Raw regions stay single opaque leaves. Reading is iterative, so nesting
    depth is bounded only by memory. *)

type tree = Leaf of Token.t | Group of group

and group = {
  delim : Token.delim;
  open_tok : Token.t;
  close_tok : Token.t;
  children : tree list;
  env : Grammar_env.t;  (** §2.6.1 [env]; always {!Grammar_env.source} in T1 *)
  span : Span.t;  (** open delimiter start to close delimiter end *)
}

type t = {
  trees : tree list;
  eof : Token.t;  (** carries the trailing trivia *)
  env : Grammar_env.t;  (** root stamp (§2.6.1 [TokenTree]) *)
}

(** Token arrays that violate the {!read} contract. Lexer output never does. *)
type input_error =
  | Missing_eof  (** the array is empty or its last token is not [Eof] *)
  | Eof_not_last of { index : int }  (** an [Eof] before the last position *)

type error =
  | Unbalanced of Diagnostic.t  (** [E-LEX-UNBALANCED] *)
  | Invalid_input of input_error

val read : Token.t array -> (t, error) result
(** Contract: the array contains exactly one [Eof], in the last position.
    [\[|eof|\]] (empty source) is valid and yields no trees; an empty array is
    [Missing_eof]. Violations are reported as [Invalid_input] before any
    grouping, so no token is ever silently dropped.

    Delimiter errors report the first problem in source order: a stray close
    (its span), a mismatched close (close span plus the open span as a note),
    or an unclosed open at end of input (the innermost open span plus the
    end-of-input span as a note). *)

val describe_input_error : input_error -> string
