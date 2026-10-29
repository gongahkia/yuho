type t = { name : string; text : string; line_starts : int array }

let compute_line_starts text =
  let starts = ref [ 0 ] in
  String.iteri (fun i c -> if c = '\n' then starts := (i + 1) :: !starts) text;
  Array.of_list (List.rev !starts)

let make ~name text = { name; text; line_starts = compute_line_starts text }
let name t = t.name
let text t = t.text
let length t = String.length t.text

let line_col t offset =
  if offset < 0 || offset > String.length t.text then
    invalid_arg "Source.line_col";
  let lo = ref 0 and hi = ref (Array.length t.line_starts - 1) in
  while !lo < !hi do
    let mid = (!lo + !hi + 1) / 2 in
    if t.line_starts.(mid) <= offset then lo := mid else hi := mid - 1
  done;
  (!lo + 1, offset - t.line_starts.(!lo) + 1)

let span t ~start ~stop =
  if stop > String.length t.text then invalid_arg "Source.span";
  Span.make ~file:t.name ~start ~stop

let slice t (s : Span.t) =
  if (not (String.equal s.file t.name)) || s.stop > String.length t.text then
    invalid_arg "Source.slice";
  String.sub t.text s.start (s.stop - s.start)
