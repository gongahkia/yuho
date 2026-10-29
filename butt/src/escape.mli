(** Safe rendering of source bytes for dumps and diagnostics.

    Bytes and characters that could hide or disguise text on a terminal are
    escaped: ASCII control bytes and DEL as [\xHH]; C1 controls (U+0080 to
    U+009F), bidirectional controls (U+061C, U+200E, U+200F, U+202A to
    U+202E, U+2066 to U+2069), U+2028, U+2029 and U+FEFF as [\u{XXXX}]; bytes
    that are not well-formed UTF-8 as [\xHH]. All other UTF-8 is kept. *)

val quoted : string -> string
(** For the body of a double-quoted dump field: additionally escapes
    backslash and double quote, and renders LF, CR and tab as [\n], [\r],
    [\t]. The mapping is injective. *)

val display : string -> string
(** For free-form human-readable text such as file names in diagnostics:
    only the characters listed above are escaped. *)
