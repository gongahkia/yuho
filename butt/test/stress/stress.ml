(* Exhaustive oracle comparisons and large inputs. Oracles share no code
   with the lexer: the stdlib UTF-8 decoder and §2.1.3 regular expressions. *)

open Front

let failures = ref 0

let check name ok detail =
  if ok then Printf.printf "ok   %s\n%!" name
  else begin
    incr failures;
    Printf.printf "FAIL %s: %s\n%!" name detail
  end

let lex s = Lexer.lex (Source.make ~name:"s" s)

let oracle_first_invalid s =
  let n = String.length s in
  let rec go i =
    if i >= n then None
    else
      let d = String.get_utf_8_uchar s i in
      if Uchar.utf_decode_is_valid d then go (i + Uchar.utf_decode_length d) else Some i
  in
  go 0

let utf8 () =
  let bad = ref 0 and cases = ref 0 in
  let test s =
    incr cases;
    if Lexer.first_invalid_utf8 s <> oracle_first_invalid s then incr bad
  in
  for a = 0xC0 to 0xFF do
    for b = 0 to 255 do
      for c = 0 to 255 do
        test (Printf.sprintf "%c%c%c" (Char.chr a) (Char.chr b) (Char.chr c))
      done
    done
  done;
  for a = 0xF0 to 0xF7 do
    for b = 0 to 255 do
      for c = 0x70 to 0xC5 do
        for d = 0x70 to 0xC5 do
          if (c + d) land 3 = 0 then test (Printf.sprintf "%c%c%c%c" (Char.chr a) (Char.chr b) (Char.chr c) (Char.chr d))
        done
      done
    done
  done;
  let rng = Random.State.make [| 42 |] in
  for _ = 1 to 2_000_000 do
    test
      (String.init (1 + Random.State.int rng 8) (fun _ ->
           let r = Random.State.int rng 10 in
           Char.chr
             (if r < 3 then 0x80 + Random.State.int rng 0x40
              else if r < 6 then 0xC0 + Random.State.int rng 0x40
              else Random.State.int rng 256)))
  done;
  check (Printf.sprintf "UTF-8 agrees with the stdlib decoder (%d inputs)" !cases) (!bad = 0) (string_of_int !bad)

let numbers () =
  let forms =
    List.map
      (fun (k, r) -> (k, Str.regexp r))
      [
        ("int", "0x[0-9A-Fa-f_]+");
        ("float", "[0-9][0-9_]*\\.[0-9][0-9_]*\\([eE][+-]?[0-9][0-9_]*\\)?");
        ("float", "[0-9][0-9_]*[eE][+-]?[0-9][0-9_]*");
        ("int", "[0-9][0-9_]*");
      ]
  in
  let suffix_re = Str.regexp "[A-Za-z_][A-Za-z0-9_]*" in
  let oracle s =
    List.fold_left
      (fun best (k, r) ->
        if Str.string_match r s 0 then
          let e = Str.match_end () in
          match best with Some (_, e') when e' >= e -> best | _ -> Some (k, e)
        else best)
      None forms
    |> Option.map (fun (k, e) ->
           (k, String.sub s 0 (if Str.string_match suffix_re s e then Str.match_end () else e)))
  in
  let alphabet = "0189_.eE+-xXafFgmu" in
  let rng = Random.State.make [| 7 |] in
  let bad = ref 0 in
  for _ = 1 to 300_000 do
    let s =
      String.make 1 "0123456789".[Random.State.int rng 10]
      ^ String.init (Random.State.int rng 10) (fun _ -> alphabet.[Random.State.int rng (String.length alphabet)])
    in
    match (lex s, oracle s) with
    | Ok o, Some (k, text) ->
        if Token.kind_name o.tokens.(0).kind <> k || o.tokens.(0).text <> text then incr bad
    | _ -> incr bad
  done;
  check "numeric literals agree with the regex oracle (300000 inputs)" (!bad = 0) (string_of_int !bad)

let lex_and_read s =
  match lex s with
  | Error d -> Error ("lexer: " ^ Diagnostic.code_name d.code ^ " at " ^ Span.to_string d.primary)
  | Ok o -> (
      match Reader.read o.tokens with
      | Ok r -> Ok (o, r)
      | Error (Reader.Unbalanced d) ->
          Error ("reader: " ^ Diagnostic.code_name d.code ^ " at " ^ Span.to_string d.primary)
      | Error (Reader.Invalid_input e) -> Error ("reader: " ^ Reader.describe_input_error e))

(* Work at 2 MB and 8 MB; a linear lexer gives ratios near 4 and a quadratic
   one near 16. Allocation is deterministic; CPU time is noisier, so its
   threshold is looser. Every input must lex and read successfully, or the
   measurement fails. *)
let scaling () =
  let rep k unit = String.concat "" (List.init (k / String.length unit) (fun _ -> unit)) in
  let shapes =
    [
      ("identifiers", fun k -> String.make k 'a');
      ("lint on every line", fun k -> rep k "x--y\n");
      ("near-closers in a long comment", fun k -> "--[===[" ^ rep k "]==]=]" ^ "]===]");
      ("# tags without openers", fun k -> rep k "#abcdefg[ ] ");
      ("deep nesting", fun k -> String.make (k / 2) '(' ^ String.make (k / 2) ')');
      ("mixed tokens", fun k -> rep k "f(a,b) 1.5e3m \"s\\n\" ");
    ]
  in
  List.iter
    (fun (name, gen) ->
      let measure s =
        Gc.compact ();
        let w = Gc.minor_words () and t = Sys.time () in
        let result = lex_and_read s in
        let dt = Sys.time () -. t and dw = Gc.minor_words () -. w in
        Result.map (fun ((o : Lexer.output), (r : Reader.t)) -> (dt, dw, Array.length o.tokens, List.length r.trees)) result
      in
      match (measure (gen 2_000_000), measure (gen 8_000_000)) with
      | Ok (ta, wa, na, _), Ok (tb, wb, nb, _) ->
          let tr = tb /. Float.max ta 1e-3 and wr = wb /. Float.max wa 1. in
          check
            (Printf.sprintf "linear work: %s (%d -> %d tokens; time %.2fs -> %.2fs, ratio %.1f; allocation ratio %.2f)"
               name na nb ta tb tr wr)
            (nb >= na && wr < 4.5 && tr < 10.0)
            ""
      | Error m, _ | _, Error m -> check ("linear work: " ^ name) false m)
    shapes

(* 32,000,000 bytes (decimal megabytes, not MiB): 2,000,000 copies of a
   16-byte line holding 8 tokens and 2 top-level trees. *)
let large () =
  let line = "f(x, [y]) -- cc\n" and copies = 2_000_000 in
  let s = String.concat "" (List.init copies (fun _ -> line)) in
  check "32,000,000-byte fixture has the intended size"
    (String.length line = 16 && String.length s = 32_000_000)
    (string_of_int (String.length s));
  (match lex_and_read s with
  | Ok (o, r) ->
      check "32,000,000-byte source lexes and reads"
        (Array.length o.tokens = (8 * copies) + 1 && List.length r.trees = 2 * copies)
        (Printf.sprintf "%d tokens, %d trees" (Array.length o.tokens) (List.length r.trees));
      check "32,000,000-byte source reconstructs" (Token.reconstruct o.tokens = s) ""
  | Error m -> check "32,000,000-byte source lexes and reads" false m);
  let s = String.make 10_000_000 '(' ^ String.make 10_000_000 ')' in
  match lex_and_read s with
  | Ok (_, r) -> check "10M nested groups" (List.length r.trees = 1) ""
  | Error m -> check "10M nested groups" false m

let () =
  utf8 ();
  numbers ();
  scaling ();
  large ();
  if !failures > 0 then exit 1
