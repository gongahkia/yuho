type t = Source

let source = Source
let equal (a : t) b = a = b
let compare (a : t) b = Stdlib.compare a b
let to_string Source = "source"
