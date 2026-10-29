(** An immutable named source buffer.

    Lines are separated by LF only; in CRLF the CR is the last byte of the
    preceding line, and a lone CR does not end a line. Columns are 1-based
    byte offsets within the line. *)

type t

val make : name:string -> string -> t
val name : t -> string
val text : t -> string
val length : t -> int

val line_col : t -> int -> int * int
(** [line_col src offset] is the 1-based [(line, column)] of byte [offset];
    [offset] may equal [length src].
    @raise Invalid_argument if [offset] is out of range. *)

val span : t -> start:int -> stop:int -> Span.t

val slice : t -> Span.t -> string
(** @raise Invalid_argument if the span is not within this source. *)
