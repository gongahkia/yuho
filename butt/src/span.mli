(** Half-open byte ranges [\[start, stop)] into a named source. *)

type t = private { file : string; start : int; stop : int }

val make : file:string -> start:int -> stop:int -> t
(** @raise Invalid_argument if [start < 0] or [stop < start]. *)

val length : t -> int
val equal : t -> t -> bool
val compare : t -> t -> int

val contains : outer:t -> t -> bool
(** [contains ~outer s] holds when [s] lies within [outer] in the same file. *)

val to_string : t -> string
(** ["[start,stop)"]. *)
