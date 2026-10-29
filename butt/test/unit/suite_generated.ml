(* Fixed-seed generated tests. The oracle is always independent of the lexer:
   the input bytes themselves (reconstruction), the generator's own tree
   (nesting), or a deliberately simplified model of §2.1.4 (operator runs). *)

open Front
open Harness

let seed = 0x5EED_0001
let pick rng arr = arr.(Random.State.int rng (Array.length arr))

let fragments =
  [|
    "a"; "_x1"; "`r`"; "0"; "12"; "1.5"; "1e5"; "3em"; "0x1F"; "0xFFu8"; "1."; ".5";
    "\"s\""; "\"\\n\\u{41}\""; "\"\xc3\xa9\""; "+"; "-"; "+-"; "|>"; "<=>"; "."; "..";
    "#"; ":"; ","; ";"; "("; ")"; "["; "]"; "{"; "}"; " "; "\t"; "\n"; "\r\n"; "\r";
    "-- c\n"; "--[[ x ]]"; "--[=[ ]] ]=]"; "#t{ a {b} }"; "#t[[ ] ]]"; "#j[=[ x ]=]";
    "-- \xc3\xa9\n"; "--"; "=";
  |]

let random_source rng =
  let b = Buffer.create 64 in
  for _ = 1 to Random.State.int rng 40 do
    Buffer.add_string b (pick rng fragments)
  done;
  Buffer.contents b

let random_bytes rng =
  String.init (Random.State.int rng 64) (fun _ ->
      if Random.State.int rng 4 = 0 then Char.chr (Random.State.int rng 256)
      else Char.chr (32 + Random.State.int rng 95))

let lex_is_total h name gen count =
  let rng = Random.State.make [| seed |] in
  let ok = ref 0 and errors = ref 0 and problems = ref [] in
  for i = 1 to count do
    let input = gen rng in
    match lex input with
    | exception e -> problems := Printf.sprintf "case %d raised %s" i (Printexc.to_string e) :: !problems
    | Ok o ->
        incr ok;
        (match invariants input o with
        | [] -> ()
        | p -> problems := Printf.sprintf "case %d %S: %s" i input (String.concat "; " p) :: !problems);
        if lex input <> Ok o then problems := Printf.sprintf "case %d nondeterministic" i :: !problems
    | Error d ->
        incr errors;
        if d.primary.stop > String.length input || Diagnostic.severity d <> Diagnostic.Error then
          problems := Printf.sprintf "case %d bad diagnostic" i :: !problems
  done;
  report h name (!problems = [])
    (lazy (String.concat "\n  " (List.filteri (fun i _ -> i < 5) (List.rev !problems))));
  (!ok, !errors)

(* Simplified model of operator runs, identifiers and line comments over the
   alphabet below; no numbers, strings, raw regions or long comments. *)
let op_alphabet = [| 'a'; 'b'; '+'; '-'; '<'; '>'; '='; '|'; '.'; ' '; '\n' |]

let model s =
  let n = String.length s in
  let is_letter c = c = 'a' || c = 'b' in
  let is_op c = not (is_letter c || c = ' ' || c = '\n') in
  let rec go i acc =
    if i >= n then List.rev acc
    else
      let c = s.[i] in
      if c = ' ' || c = '\n' then go (i + 1) acc
      else if c = '-' && i + 1 < n && s.[i + 1] = '-' then
        let rec eol j = if j < n && s.[j] <> '\n' then eol (j + 1) else j in
        go (eol i) acc
      else
        let pred = if is_letter c then is_letter else is_op in
        let rec run j =
          if j < n && pred s.[j] && not (s.[j] = '-' && j + 1 < n && s.[j + 1] = '-') then
            run (j + 1)
          else j
        in
        let j = run (i + 1) in
        go j (((if is_letter c then "ident" else "op"), String.sub s i (j - i), i, j) :: acc)
  in
  go 0 []

let operator_model h =
  let rng = Random.State.make [| seed + 1 |] in
  let mismatches = ref [] in
  for _ = 1 to 5000 do
    let input = String.init (Random.State.int rng 24) (fun _ -> pick rng op_alphabet) in
    match lex input with
    | Error d -> mismatches := (input ^ ": " ^ render_diag input d) :: !mismatches
    | Ok o ->
        if List.map tuple (non_eof o) <> model input then mismatches := input :: !mismatches
  done;
  report h "operator runs agree with the simplified model (5000 cases)" (!mismatches = [])
    (lazy (String.concat " | " (List.filteri (fun i _ -> i < 5) !mismatches)))

let stability h =
  let rng = Random.State.make [| seed + 2 |] in
  let prefixes =
    [| "syntax infix \"<|>\" at 50 => f\n"; "declare_syntax x\n"; "syntax prefix \"+-\" => g\n" |]
  in
  let normalize shift (t : Token.t) =
    ( tuple t |> fun (k, x, a, b) -> (k, x, a - shift, b - shift),
      t.space_before,
      t.newline_before,
      List.map (fun (tv : Token.trivia) -> tv.trivia_text) t.leading_trivia )
  in
  let bad = ref [] and compared = ref 0 in
  for _ = 1 to 2000 do
    let prefix = pick rng prefixes in
    let body = "\n" ^ random_source rng in
    let shift = String.length prefix - 1 in
    match (lex body, lex (prefix ^ String.sub body 1 (String.length body - 1))) with
    | Ok alone, Ok combined ->
        incr compared;
        let a = Array.to_list alone.tokens |> List.map (normalize 0) in
        let c = Array.to_list combined.tokens in
        let c = List.filteri (fun i _ -> i >= List.length c - List.length a) c |> List.map (normalize shift) in
        if a <> c then bad := body :: !bad
    | Error d1, Error d2 ->
        if d1.code <> d2.code || d1.primary.start <> d2.primary.start - shift then bad := body :: !bad
    | _ -> bad := body :: !bad
  done;
  report h "LEX-03 tokens after declarations are unchanged (2000 cases)" (!bad = [])
    (lazy (String.concat " | " (List.filteri (fun i _ -> i < 3) !bad)));
  report h "LEX-03 stability compared enough successful cases" (!compared > 500)
    (lazy (string_of_int !compared))

type gen = L of string | G of Token.delim * gen list

let rec gen_tree rng ~leaves depth =
  if depth = 0 || Random.State.int rng 10 < 4 then L (pick rng leaves)
  else
    let d = pick rng [| Token.Paren; Token.Bracket; Token.Brace |] in
    G (d, List.init (Random.State.int rng 5) (fun _ -> gen_tree rng ~leaves (depth - 1)))

let rec expected_shape = function
  | L s -> s
  | G (d, cs) ->
      Printf.sprintf "%c%s%c" (Token.open_char d)
        (String.concat " " (List.map expected_shape cs))
        (Token.close_char d)

let rec render rng ~seps = function
  | L s -> s
  | G (d, cs) ->
      let sep () = pick rng seps in
      String.make 1 (Token.open_char d)
      ^ sep ()
      ^ String.concat (sep ()) (List.map (render rng ~seps) cs)
      ^ sep ()
      ^ String.make 1 (Token.close_char d)

let nesting h =
  let rng = Random.State.make [| seed + 3 |] in
  let leaves = [| "x"; "1"; "+"; "\"s)\""; "#t{a(}"; "`k`" |] in
  let seps = [| " "; "\n"; "\t"; " -- c\n"; " --[[ ( ]] " |] in
  let bad = ref [] in
  for _ = 1 to 2000 do
    let trees = List.init (1 + Random.State.int rng 3) (fun _ -> gen_tree rng ~leaves 6) in
    let input = String.concat " " (List.map (render rng ~seps) trees) in
    let expected = String.concat " " (List.map expected_shape trees) in
    match lex input with
    | Error _ -> bad := input :: !bad
    | Ok o -> (
        match Reader.read o.tokens with
        | Ok r when String.concat " " (List.map Suite_reader.shape r.trees) = expected -> ()
        | _ -> bad := input :: !bad)
  done;
  report h "generated trees read back to the generator's shape (2000 cases)" (!bad = [])
    (lazy (String.concat " | " (List.filteri (fun i _ -> i < 3) !bad)))

let mutation h =
  let rng = Random.State.make [| seed + 4 |] in
  let leaves = [| "x"; "1"; "+" |] in
  let seps = [| " "; "\n"; " -- c\n" |] in
  let bad = ref [] and mutated = ref 0 in
  for _ = 1 to 2000 do
    let input = render rng ~seps (gen_tree rng ~leaves 6) in
    match lex input with
    | Error _ -> bad := input :: !bad
    | Ok o -> (
        let delims =
          Array.to_list o.tokens
          |> List.filter (fun (t : Token.t) ->
                 match t.kind with Open _ | Close _ -> true | _ -> false)
        in
        match delims with
        | [] -> ()
        | _ -> (
            let t = List.nth delims (Random.State.int rng (List.length delims)) in
            let p = t.span.start in
            let input' = String.sub input 0 p ^ String.sub input (p + 1) (String.length input - p - 1) in
            incr mutated;
            match lex input' with
            | Ok o' -> (
                match Reader.read o'.tokens with
                | Error (Reader.Unbalanced _) -> ()
                | _ -> bad := input' :: !bad)
            | Error _ -> bad := input' :: !bad))
  done;
  report h "deleting any one delimiter yields E-LEX-UNBALANCED" (!bad = [])
    (lazy (String.concat " | " (List.filteri (fun i _ -> i < 3) !bad)));
  report h "mutation test exercised enough cases" (!mutated > 500) (lazy (string_of_int !mutated))

let dumps_are_stable h =
  let rng = Random.State.make [| seed + 5 |] in
  let bad = ref 0 in
  for _ = 1 to 500 do
    let input = random_source rng in
    let s = Source.make ~name:"t" input in
    match Lexer.lex s with
    | Ok o ->
        let d1 = Dump.tokens ~trivia:true s o.tokens in
        let d2 =
          match Lexer.lex (Source.make ~name:"t" input) with
          | Ok o2 -> Dump.tokens ~trivia:true s o2.tokens
          | Error _ -> ""
        in
        if d1 <> d2 then incr bad
    | Error _ -> ()
  done;
  report h "repeated dumps are identical (500 cases)" (!bad = 0) (lazy (string_of_int !bad))

let run h =
  group h "LEX-13 reconstruction and totality (generated)";
  let ok, _ = lex_is_total h "fragment sources: invariants hold, never raises (5000 cases)" random_source 5000 in
  report h "fragment generator produced enough successful lexes" (ok > 1000) (lazy (string_of_int ok));
  let _ = lex_is_total h "arbitrary bytes: invariants hold, never raises (5000 cases)" random_bytes 5000 in
  group h "LEX-02 operator runs (generated)";
  operator_model h;
  group h "LEX-03 stability (generated)";
  stability h;
  group h "LEX-08 nesting (generated)";
  nesting h;
  mutation h;
  group h "determinism";
  dumps_are_stable h
