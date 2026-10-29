(** Deterministic textual dumps of tokens and token trees (formats
    [tokens/2] and [trees/2]). Output depends only on the source name and
    bytes. Text fields are rendered with {!Escape.quoted}.

    [trees/2]: the header and every group line carry the grammar-environment
    stamp ([env=...]). Lines are indented two spaces per nesting level up to
    {!max_indent} levels; deeper lines keep that indentation and start with
    an explicit [depth=N] marker.

    Size and cost. Capping indentation removes the term that grew
    quadratically with nesting depth: indentation is at most
    [2 * max_indent] bytes per line. Each line otherwise holds fixed text,
    decimal numbers (line, column, byte offsets, depth, sub-span bounds) of
    O(log N) digits for an N-byte source, and the escaped token text. Escaping
    expands a byte at most 4x ([\xHH]). Each source byte belongs to at most
    one token text, and [trees/2] omits trivia. So a [trees/2] dump of T
    tokens is O(T log N + N) bytes. [tokens ~trivia:true] adds the escaped
    trivia, still O(T log N + N). Each line also costs one O(log L)
    line-table lookup for L lines. The whole dump is built in memory before
    it is returned. *)

val max_indent : int

val escape : string -> string
(** [Escape.quoted]. *)

val token_line : Source.t -> Token.t -> string
val tokens : ?trivia:bool -> Source.t -> Token.t array -> string
val trees : Source.t -> Reader.t -> string
