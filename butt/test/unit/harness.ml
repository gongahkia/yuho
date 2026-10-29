(* Minimal stdlib-only test harness. Expected values in the suites are
   written by hand from docs/architecture.md §2.1 and §12, never produced by
   running the implementation. *)

open Front

type t = { mutable passed : int; mutable failed : int; mutable group : string }

let create () = { passed = 0; failed = 0; group = "" }
let group h name = h.group <- name

let report h name ok detail =
  if ok then h.passed <- h.passed + 1
  else begin
    h.failed <- h.failed + 1;
    Printf.printf "FAIL [%s] %s\n  %s\n" h.group name (Lazy.force detail)
  end

let src s = Source.make ~name:"t" s
let lex s = Lexer.lex (src s)

let contains_lf s = String.contains s '\n'

(* Checks every structural guarantee of a successful lex against the input
   bytes: tiling of trivia and token spans, exact slices, flags, sub-span
   containment, Eof placement and byte-for-byte reconstruction. *)
let invariants input (o : Lexer.output) =
  let n = String.length input in
  let problems = ref [] in
  let bad fmt = Printf.ksprintf (fun m -> problems := m :: !problems) fmt in
  let off = ref 0 in
  let count = Array.length o.tokens in
  if count = 0 then bad "no tokens";
  Array.iteri
    (fun i (tok : Token.t) ->
      List.iter
        (fun (tv : Token.trivia) ->
          let sp = tv.trivia_span in
          if sp.start <> !off then bad "trivia at %d, expected %d" sp.start !off;
          if Span.length sp = 0 then bad "empty trivia at %d" sp.start;
          if sp.stop > n || tv.trivia_text <> String.sub input sp.start (Span.length sp)
          then bad "trivia text mismatch at %d" sp.start;
          off := sp.stop)
        tok.leading_trivia;
      let sp = tok.span in
      if sp.start <> !off then bad "token %d at %d, expected %d" i sp.start !off;
      if sp.stop > n || tok.text <> String.sub input sp.start (Span.length sp) then
        bad "token %d text mismatch" i;
      off := sp.stop;
      if tok.space_before <> (tok.leading_trivia <> []) then bad "token %d space flag" i;
      let nl =
        List.exists (fun (tv : Token.trivia) -> contains_lf tv.trivia_text) tok.leading_trivia
      in
      if tok.newline_before <> nl then bad "token %d newline flag" i;
      let inside s = Span.contains ~outer:sp s in
      (match tok.kind with
      | Eof ->
          if i <> count - 1 then bad "Eof at index %d" i;
          if sp.start <> n || sp.stop <> n then bad "Eof span"
      | _ -> if i = count - 1 then bad "last token is not Eof");
      (match tok.kind with
      | Eof -> ()
      | _ -> if Span.length sp = 0 then bad "empty token %d" i);
      match tok.kind with
      | Int { suffix = Some s; _ } | Float { suffix = Some s } ->
          if not (inside s && s.stop = sp.stop) then bad "suffix span of token %d" i
      | Raw_ident { name } ->
          if not (inside name && name.start = sp.start + 1 && name.stop = sp.stop - 1) then
            bad "raw-ident name span"
      | Raw_region { tag; content; _ } ->
          if not (inside tag && inside content && tag.start = sp.start + 1 && tag.stop <= content.start)
          then bad "raw-region sub-spans"
      | _ -> ())
    o.tokens;
  if !off <> n then bad "tokens cover %d of %d bytes" !off n;
  if Token.reconstruct o.tokens <> input then bad "reconstruction differs";
  List.rev !problems

let check_invariants h name input o =
  let p = invariants input o in
  report h (name ^ " (invariants)") (p = []) (lazy (String.concat "; " p))

type tok = string * string * int * int

let tuple (t : Token.t) : tok = (Token.kind_name t.kind, t.text, t.span.start, t.span.stop)

let show (l : tok list) =
  "[" ^ String.concat "; " (List.map (fun (k, x, a, b) -> Printf.sprintf "%s %S %d %d" k x a b) l) ^ "]"

let non_eof (o : Lexer.output) =
  Array.to_list o.tokens |> List.filter (fun (t : Token.t) -> match t.kind with Eof -> false | _ -> true)

let render_diag input d = Diagnostic.render (src input) d

(* [toks h name input expected] - expected tokens exclude Eof. *)
let toks h name input expected =
  match lex input with
  | Error d -> report h name false (lazy ("unexpected error: " ^ render_diag input d))
  | Ok o ->
      check_invariants h name input o;
      let got = List.map tuple (non_eof o) in
      report h name (got = expected)
        (lazy (Printf.sprintf "expected %s\n  got      %s" (show expected) (show got)))

let with_ok h name input f =
  match lex input with
  | Error d -> report h name false (lazy ("unexpected error: " ^ render_diag input d))
  | Ok o ->
      check_invariants h name input o;
      f o

let lex_err h name input code (start, stop) =
  match lex input with
  | Ok _ -> report h name false (lazy "expected an error, got tokens")
  | Error d ->
      report h name
        (d.code = code && d.primary.start = start && d.primary.stop = stop)
        (lazy
          (Printf.sprintf "expected %s [%d,%d), got %s" (Diagnostic.code_name code) start
             stop (render_diag input d)))

let span_eq (s : Span.t) (a, b) = s.start = a && s.stop = b
let show_span (s : Span.t) = Span.to_string s
