type t = { file : string; start : int; stop : int }

let make ~file ~start ~stop =
  if start < 0 || stop < start then invalid_arg "Span.make";
  { file; start; stop }

let length s = s.stop - s.start

let equal a b =
  String.equal a.file b.file && a.start = b.start && a.stop = b.stop

let compare a b =
  match String.compare a.file b.file with
  | 0 -> (
      match Int.compare a.start b.start with
      | 0 -> Int.compare a.stop b.stop
      | c -> c)
  | c -> c

let contains ~outer s =
  String.equal outer.file s.file && outer.start <= s.start && s.stop <= outer.stop

let to_string s = Printf.sprintf "[%d,%d)" s.start s.stop
