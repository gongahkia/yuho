(* Stack-safety tests. Dune runs this with OCAMLRUNPARAM=l=32k (a 256 KiB
   stack). The canary proves the limit is in effect, so a pass means the
   lexer, reader and dumps did not recurse on input size or depth. *)

open Front

let failures = ref 0
let checks = ref 0

let check name ok detail =
  incr checks;
  if not ok then begin
    incr failures;
    Printf.printf "FAIL %s: %s\n" name detail
  end

let lex s = Lexer.lex (Source.make ~name:"t" s)

let read_ok s =
  match lex s with
  | Error _ -> None
  | Ok o -> ( match Reader.read o.tokens with Ok r -> Some (o, r) | Error _ -> None)

let canary () =
  let rec deep n = if n = 0 then 0 else 1 + deep (n - 1) in
  match deep 10_000_000 with
  | _ -> false
  | exception Stack_overflow -> true

let rec depth_of acc = function
  | [ Reader.Group g ] -> depth_of (acc + 1) g.children
  | _ -> acc

let () =
  check "reduced stack limit is in effect (run via dune test)" (canary ())
    "a 10M-deep recursion did not overflow";
  let n = 1_000_000 in
  (match read_ok (String.make n '(' ^ String.make n ')') with
  | Some (_, r) -> check "1M nested parens" (depth_of 0 r.trees = n) "wrong depth"
  | None -> check "1M nested parens" false "lex or read failed");
  let k = 300_000 in
  let opens = String.concat "" (List.init k (fun _ -> "([{")) in
  let closes = String.concat "" (List.init k (fun _ -> "}])")) in
  (match read_ok (opens ^ "x" ^ closes) with
  | Some (o, r) ->
      check "900k nested mixed delimiters" (depth_of 0 r.trees = 3 * k) "wrong depth";
      check "deep input reconstructs" (Token.reconstruct o.tokens = opens ^ "x" ^ closes) "mismatch"
  | None -> check "900k nested mixed delimiters" false "lex or read failed");
  (match lex (String.make n '[') with
  | Ok o -> (
      match Reader.read o.tokens with
      | Error (Reader.Unbalanced d) ->
          check "1M unclosed opens report the innermost" (d.primary.start = n - 1) (Span.to_string d.primary)
      | _ -> check "1M unclosed opens" false "expected Unbalanced")
  | Error _ -> check "1M unclosed opens" false "lex failed");
  check "raw region with 1M nested braces"
    (match lex ("#t{" ^ String.make n '{' ^ String.make n '}' ^ "}") with
    | Ok o -> Array.length o.tokens = 2
    | Error _ -> false)
    "";
  check "1M-token flat input"
    (match lex (String.concat " " (List.init n (fun _ -> "a"))) with
    | Ok o -> Array.length o.tokens = n + 1
    | Error _ -> false)
    "";
  (* Past the indentation cap, quadrupling the depth of this fixed-width
     fixture must not multiply dump size by anything near 16. *)
  let dump_size d =
    match read_ok (String.make d '{' ^ String.make d '}') with
    | Some (_, r) -> String.length (Dump.trees (Source.make ~name:"t" (String.make d '{' ^ String.make d '}')) r)
    | None -> -1
  in
  let s1 = dump_size 50_000 and s4 = dump_size 200_000 in
  check "200k-deep tree dump completes" (s4 > 0) "";
  check "tree dump size is not quadratic in depth"
    (s4 < 5 * s1)
    (Printf.sprintf "50k deep: %d bytes, 200k deep: %d bytes" s1 s4);
  check "tree dump stays under 160 bytes per token" (s4 < 160 * 400_001) (string_of_int s4);
  Printf.printf "%d stack checks passed, %d failed\n" (!checks - !failures) !failures;
  if !failures > 0 then exit 1
