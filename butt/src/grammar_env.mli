(** Grammar-environment identity: the [env] stamp of architecture §2.6.1
    and §13.2.

    This identifies which grammar environment a token tree must be parsed
    with. It is unrelated to source-file identity ([Span.file]). T1 creates
    only {!source}; registries, snapshots and re-stamping arrive in later
    tranches, which add further values to this type without changing its
    interface. *)

type t

val source : t
(** The stamp of user-written source (§2.6.1 [Source]). The reader assigns it
    to every tree it builds. It records where a tree came from; it does not
    say which declarations are active. *)

val equal : t -> t -> bool
val compare : t -> t -> int

val to_string : t -> string
(** Stable, deterministic rendering used by dumps; ["source"] for {!source}. *)
