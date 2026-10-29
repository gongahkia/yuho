(* Checks against oracles that share no code with the lexer: the stdlib
   UTF-8 decoder, Str regular expressions transcribed from §2.1.3, and the
   input bytes themselves. Sized for the routine test run; the exhaustive
   versions are in test/stress. *)

open Front
open Harness

(* ---- UTF-8 ------------------------------------------------------------ *)

let oracle_first_invalid s =
  let n = String.length s in
  let rec go i =
    if i >= n then None
    else
      let d = String.get_utf_8_uchar s i in
      if Uchar.utf_decode_is_valid d then go (i + Uchar.utf_decode_length d) else Some i
  in
  go 0

let utf8_agrees s =
  let expected = oracle_first_invalid s in
  Lexer.first_invalid_utf8 s = expected
  && (expected = None) = String.is_valid_utf_8 s
  &&
  match (Lexer.lex (src s), expected) with
  | Error d, Some i -> d.code = Diagnostic.Lex_utf8 && span_eq d.primary (i, i + 1)
  | Error d, None -> d.code <> Diagnostic.Lex_utf8
  | Ok _, None -> true
  | Ok _, Some _ -> false

let utf8 h =
  let bad = ref [] and cases = ref 0 in
  let test s =
    incr cases;
    if not (utf8_agrees s) then bad := s :: !bad
  in
  for a = 0 to 255 do
    test (String.make 1 (Char.chr a));
    for b = 0 to 255 do
      test (Printf.sprintf "%c%c" (Char.chr a) (Char.chr b))
    done
  done;
  let edges = [ 0x00; 0x7F; 0x80; 0x8F; 0x90; 0x9F; 0xA0; 0xBF; 0xC0; 0xFF ] in
  for a = 0xE0 to 0xF7 do
    for b = 0 to 255 do
      List.iter (fun c -> test (Printf.sprintf "\"%c%c%c\"" (Char.chr a) (Char.chr b) (Char.chr c))) edges;
      if a >= 0xF0 then
        List.iter (fun d -> test (Printf.sprintf "%c%c\x80%c" (Char.chr a) (Char.chr b) (Char.chr d))) edges
    done
  done;
  let rng = Random.State.make [| 0x0717 |] in
  for _ = 1 to 100_000 do
    test
      (String.init (1 + Random.State.int rng 8) (fun _ ->
           let r = Random.State.int rng 10 in
           Char.chr
             (if r < 3 then 0x80 + Random.State.int rng 0x40
              else if r < 6 then 0xC0 + Random.State.int rng 0x40
              else 32 + Random.State.int rng 95)))
  done;
  report h
    (Printf.sprintf "UTF-8 validation agrees with the stdlib decoder (%d inputs)" !cases)
    (!bad = [])
    (lazy (String.concat " | " (List.map String.escaped (List.filteri (fun i _ -> i < 5) !bad))))

(* ---- numeric literals --------------------------------------------------- *)

(* §2.1.3 regular expressions, tried together with longest match; then the
   optional identifier suffix. Exponent digits follow I-07. *)
let number_forms =
  List.map
    (fun (k, r) -> (k, Str.regexp r))
    [
      ("int", "0x[0-9A-Fa-f_]+");
      ("float", "[0-9][0-9_]*\\.[0-9][0-9_]*\\([eE][+-]?[0-9][0-9_]*\\)?");
      ("float", "[0-9][0-9_]*[eE][+-]?[0-9][0-9_]*");
      ("int", "[0-9][0-9_]*");
    ]

let suffix_re = Str.regexp "[A-Za-z_][A-Za-z0-9_]*"

let oracle_number s =
  let best =
    List.fold_left
      (fun best (k, r) ->
        if Str.string_match r s 0 then
          let e = Str.match_end () in
          match best with Some (_, e') when e' >= e -> best | _ -> Some (k, e)
        else best)
      None number_forms
  in
  Option.map
    (fun (k, e) ->
      let stop = if Str.string_match suffix_re s e then Str.match_end () else e in
      (k, String.sub s 0 stop, if stop > e then Some (e, stop) else None))
    best

let numbers h =
  let alphabet = "0189_.eE+-xXafFgmu" in
  let rng = Random.State.make [| 0x2101 |] in
  let bad = ref [] in
  for _ = 1 to 30_000 do
    let s =
      String.make 1 "0123456789".[Random.State.int rng 10]
      ^ String.init (Random.State.int rng 8) (fun _ -> alphabet.[Random.State.int rng (String.length alphabet)])
    in
    match (lex s, oracle_number s) with
    | Ok o, Some (k, text, suffix) ->
        let t = o.tokens.(0) in
        let got_suffix =
          match t.kind with
          | Int { suffix = sp; _ } | Float { suffix = sp } -> Option.map (fun (sp : Span.t) -> (sp.start, sp.stop)) sp
          | _ -> Some (-1, -1)
        in
        if Token.kind_name t.kind <> k || t.text <> text || got_suffix <> suffix then bad := s :: !bad
    | _ -> bad := s :: !bad
  done;
  report h "numeric literals agree with the §2.1.3 regex oracle (30000 inputs)" (!bad = [])
    (lazy (String.concat " | " (List.filteri (fun i _ -> i < 8) !bad)))

(* ---- reconstruction from token trees ------------------------------------ *)

let flatten (r : Reader.t) =
  let acc = ref [] in
  let rec walk = function
    | [] -> ()
    | Reader.Leaf t :: rest ->
        acc := t :: !acc;
        walk rest
    | Reader.Group g :: rest ->
        acc := g.open_tok :: !acc;
        walk g.children;
        acc := g.close_tok :: !acc;
        walk rest
  in
  walk r.trees;
  Array.of_list (List.rev (r.eof :: !acc))

let tree_reconstruction h =
  let frags =
    [| "a"; " "; "\n"; "\r\n"; "("; ")"; "["; "]"; "{"; "}"; "#t{x}"; "#t[[ ) ]]"; "-- c\n"; "--[[ ( ]]"; "\"(\""; "1.5"; "+-"; "," |]
  in
  let rng = Random.State.make [| 0x7EE |] in
  let bad = ref 0 and balanced = ref 0 in
  for _ = 1 to 20_000 do
    let s =
      String.concat "" (List.init (Random.State.int rng 30) (fun _ -> frags.(Random.State.int rng (Array.length frags))))
    in
    match lex s with
    | Error _ -> incr bad
    | Ok o -> (
        match Reader.read o.tokens with
        | Ok r ->
            incr balanced;
            let toks = flatten r in
            if Token.reconstruct toks <> s || toks <> o.tokens then incr bad
        | Error (Reader.Unbalanced _) -> ()
        | Error (Reader.Invalid_input _) -> incr bad)
  done;
  report h "token trees keep every token and reconstruct the source (20000 inputs)" (!bad = 0)
    (lazy (string_of_int !bad));
  report h "tree reconstruction saw enough balanced inputs" (!balanced > 1000) (lazy (string_of_int !balanced))

(* ---- CRLF versus LF ------------------------------------------------------ *)

let crlf_equivalence h =
  let frags = [| "x"; " "; "\n"; "f(a)"; "-- c\n"; "--[[ a\nb ]]"; "#t{ a\n b }"; "#t[[\n]]"; "\"s\""; "1.5e3"; "+-"; "`k`" |] in
  let rng = Random.State.make [| 0xC21F |] in
  let crlf s = String.concat "\r\n" (String.split_on_char '\n' s) in
  let drop_cr s = String.concat "" (String.split_on_char '\r' s) in
  let view s (o : Lexer.output) =
    let source = src s in
    Array.to_list o.tokens
    |> List.map (fun (t : Token.t) ->
           (Token.kind_name t.kind, drop_cr t.text, Source.line_col source t.span.start |> fst, t.space_before, t.newline_before))
  in
  let bad = ref [] in
  for _ = 1 to 3_000 do
    let s = String.concat "" (List.init (Random.State.int rng 25) (fun _ -> frags.(Random.State.int rng (Array.length frags)))) in
    let s' = crlf s in
    match (lex s, lex s') with
    | Ok a, Ok b -> if view s a <> view s' b then bad := s :: !bad
    | Error _, Error _ -> ()
    | _ -> bad := s :: !bad
  done;
  report h "LF and CRLF sources give the same tokens and lines (3000 inputs)" (!bad = [])
    (lazy (String.concat " | " (List.map String.escaped (List.filteri (fun i _ -> i < 3) !bad))))

(* ---- long runs and unterminated bodies ---------------------------------- *)

let long_inputs h =
  let n = 200_000 in
  let check name input expected =
    match lex input with
    | Ok o ->
        let got = List.map tuple (Array.to_list o.tokens) in
        report h name (got = expected) (lazy (show (List.filteri (fun i _ -> i < 4) got)))
    | Error d -> report h name false (lazy (render_diag input d))
  in
  let plus = String.make n '+' in
  check "200k-character operator run is one token" plus [ ("op", plus, 0, n); ("eof", "", n, n) ];
  let alt = String.concat "" (List.init (n / 2) (fun _ -> "+-")) in
  check "alternating +- run is one token" alt [ ("op", alt, 0, n); ("eof", "", n, n) ];
  let s = String.make n '<' ^ "--" ^ String.make n '>' in
  check "a run stops before --, which comments out the rest" s [ ("op", String.make n '<', 0, n); ("eof", "", (2 * n) + 2, (2 * n) + 2) ];
  let s = String.make n '.' ^ "#t{x}" in
  check "a run stops before a raw region" s [ ("op", String.make n '.', 0, n); ("raw-region", "#t{x}", n, n + 5); ("eof", "", n + 5, n + 5) ];
  let ident = String.make n 'a' in
  check "200k-character identifier" ident [ ("ident", ident, 0, n); ("eof", "", n, n) ];
  lex_err h "unterminated 200k string" ("\"" ^ String.make n 'a') Diagnostic.Lex_string (0, n + 1);
  lex_err h "unterminated brace raw region with 200k nested braces" ("#t{" ^ String.make n '{') Diagnostic.Lex_raw (0, 3);
  lex_err h "unterminated long raw region with many near-closers"
    ("#t[==[" ^ String.concat "" (List.init 50_000 (fun _ -> "]=]]===]")))
    Diagnostic.Lex_raw (0, 6);
  lex_err h "unterminated long comment with many near-closers"
    ("--[=[" ^ String.concat "" (List.init 50_000 (fun _ -> "]]]==]")))
    Diagnostic.Lex_comment (0, 5);
  lex_err h "invalid UTF-8 after 200k valid bytes" (String.make n 'a' ^ "\xff") Diagnostic.Lex_utf8 (n, n + 1)

let run h =
  group h "LEX-01 UTF-8 (independent oracle)";
  utf8 h;
  group h "LEX-05 numeric literals (independent oracle)";
  numbers h;
  group h "LEX-13 reconstruction from token trees";
  tree_reconstruction h;
  group h "LEX-01 CRLF and LF";
  crlf_equivalence h;
  group h "long and unterminated inputs";
  long_inputs h
