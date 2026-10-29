(* Hand-specified token-tree cases (LEX-08, LEX-11), the grammar-environment
   stamp, and the Reader.read input contract. *)

open Front
open Harness

(* Groups render as <open>children<close>, children separated by spaces. *)
let rec shape = function
  | Reader.Leaf (t : Token.t) -> t.text
  | Reader.Group g ->
      Printf.sprintf "%c%s%c" (Token.open_char g.delim)
        (String.concat " " (List.map shape g.children))
        (Token.close_char g.delim)

let read input =
  match lex input with
  | Error d -> Error ("lex error: " ^ render_diag input d)
  | Ok o -> Ok (Reader.read o.tokens)

let show_read_error input = function
  | Reader.Unbalanced d -> render_diag input d
  | Reader.Invalid_input e -> Reader.describe_input_error e

let tree h name input expected =
  match read input with
  | Error m -> report h name false (lazy m)
  | Ok (Error e) -> report h name false (lazy (show_read_error input e))
  | Ok (Ok r) ->
      let got = String.concat " " (List.map shape r.trees) in
      report h name (got = expected) (lazy ("got " ^ got))

let read_err h name input primary notes =
  match read input with
  | Error m -> report h name false (lazy m)
  | Ok (Ok _) -> report h name false (lazy "expected E-LEX-UNBALANCED")
  | Ok (Error (Reader.Invalid_input e)) ->
      report h name false (lazy (Reader.describe_input_error e))
  | Ok (Error (Reader.Unbalanced d)) ->
      let got_notes =
        List.map (fun (n : Diagnostic.note) -> (n.note_span.start, n.note_span.stop)) d.notes
      in
      report h name
        (d.code = Diagnostic.Lex_unbalanced && span_eq d.primary primary && got_notes = notes)
        (lazy (render_diag input d))

(* Hand-built tokens for the input-contract tests; spans are irrelevant. *)
let mk kind text : Token.t =
  {
    kind;
    text;
    span = Span.make ~file:"t" ~start:0 ~stop:(String.length text);
    space_before = false;
    newline_before = false;
    leading_trivia = [];
  }

let eof = mk Token.Eof ""
let x = mk Token.Ident "x"

let input_error h name tokens expected =
  match Reader.read tokens with
  | Error (Reader.Invalid_input e) ->
      report h name (e = expected) (lazy (Reader.describe_input_error e))
  | Error (Reader.Unbalanced _) -> report h name false (lazy "got Unbalanced")
  | Ok _ -> report h name false (lazy "accepted a malformed token array")

let rec all_groups acc = function
  | [] -> acc
  | Reader.Leaf _ :: rest -> all_groups acc rest
  | Reader.Group g :: rest -> all_groups (all_groups (g :: acc) g.children) rest

let run h =
  group h "LEX-08 token trees and E-LEX-UNBALANCED";
  tree h "empty" "" "";
  tree h "nested groups" "f(a, [b {c}])" "f (a , [b {c}])";
  tree h "adjacent groups" "()[]{}" "() [] {}";
  tree h "raw region is one leaf" "x #t{(} y" "x #t{(} y";
  tree h "delimiters in string are leaves" "(\")\")" "(\")\")";
  tree h "delimiters in comments are ignored" "( -- )\n)" "()";
  (match read "(a [b] c)" with
  | Ok (Ok { trees = [ Reader.Group g ]; _ }) ->
      report h "group span" (span_eq g.span (0, 9)) (lazy (show_span g.span));
      report h "group delimiter" (g.delim = Token.Paren) (lazy "wrong delimiter");
      (match g.children with
      | [ _; Reader.Group inner; _ ] ->
          report h "inner group span" (span_eq inner.span (3, 6)) (lazy (show_span inner.span))
      | _ -> report h "inner group span" false (lazy "unexpected children"))
  | _ -> report h "group span" false (lazy "unexpected result"));
  read_err h "mismatched close" "(]" (1, 2) [ (0, 1) ];
  read_err h "stray close" ")" (0, 1) [];
  read_err h "stray close after group" "(a))" (3, 4) [];
  read_err h "unclosed outer" "((a)" (0, 1) [ (4, 4) ];
  read_err h "innermost unclosed reported" "{[(" (2, 3) [ (3, 3) ];
  read_err h "crossed delimiters" "([)]" (2, 3) [ (1, 2) ];
  read_err h "first error wins" "(] )" (1, 2) [ (0, 1) ];

  group h "LEX-11 raw region early close in trees";
  read_err h "early-closed raw region leaves a stray brace" "#json{ {\"a\": \"}\"} }" (18, 19) [];
  tree h "long form reads cleanly" "#json[=[ {\"a\": \"}\"} ]=]" "#json[=[ {\"a\": \"}\"} ]=]";

  group h "grammar-environment stamp (M1)";
  (match read "f(a, [b {c}]) {}" with
  | Ok (Ok r) ->
      let gs = all_groups [] r.trees in
      report h "root carries the source stamp" (Grammar_env.equal r.env Grammar_env.source)
        (lazy (Grammar_env.to_string r.env));
      report h "every group carries the source stamp"
        (List.length gs = 4 && List.for_all (fun (g : Reader.group) -> Grammar_env.equal g.env Grammar_env.source) gs)
        (lazy (string_of_int (List.length gs)));
      report h "stamp is independent of the file name"
        (match read "()" with
        | Ok (Ok r2) -> (
            match Reader.read (match Lexer.lex (Source.make ~name:"other" "()") with Ok o -> o.tokens | Error _ -> [||]) with
            | Ok r3 -> Grammar_env.equal r2.env r3.env
            | Error _ -> false)
        | _ -> false)
        (lazy "stamps differ across files");
      report h "stamp renders deterministically" (Grammar_env.to_string Grammar_env.source = "source")
        (lazy (Grammar_env.to_string Grammar_env.source));
      report h "stamp compare is reflexive" (Grammar_env.compare Grammar_env.source Grammar_env.source = 0)
        (lazy "")
  | _ -> report h "stamp inputs read" false (lazy "unexpected result"));
  (match read "" with
  | Ok (Ok r) ->
      report h "empty source has a root stamp and no trees"
        (r.trees = [] && Grammar_env.equal r.env Grammar_env.source)
        (lazy "")
  | _ -> report h "empty source reads" false (lazy "unexpected result"));

  group h "trees/2 dump format";
  (let input = String.make 34 '(' ^ String.make 34 ')' in
   match read input with
   | Ok (Ok r) ->
       let lines = String.split_on_char '\n' (Dump.trees (src input) r) in
       let nth i = try List.nth lines i with _ -> "<missing>" in
       let pad n = String.make (2 * n) ' ' in
       report h "header carries the root stamp" (nth 0 = "format trees/2 file=t env=source") (lazy (nth 0));
       report h "top-level group line" (nth 1 = {|group env=source 1:1 [0,1) open "("|}) (lazy (nth 1));
       report h "depth 32 is indented, no marker"
         (nth 33 = pad 32 ^ {|group env=source 1:33 [32,33) open "("|})
         (lazy (nth 33));
       report h "depth 33 keeps the indentation cap and adds a marker"
         (nth 34 = pad 32 ^ {|depth=33 group env=source 1:34 [33,34) open "("|})
         (lazy (nth 34));
       report h "matching close at depth 33"
         (nth 35 = pad 32 ^ {|depth=33 end 1:35 [34,35) close ")"|})
         (lazy (nth 35));
       report h "eof line" (nth 69 = {|1:69 [68,68) eof ""|}) (lazy (nth 69))
   | _ -> report h "trees/2 inputs read" false (lazy "unexpected result"));

  group h "Reader.read input contract";
  report h "single Eof is valid empty input"
    (match Reader.read [| eof |] with Ok { trees = []; _ } -> true | _ -> false)
    (lazy "");
  report h "terminal Eof after tokens"
    (match Reader.read [| x; eof |] with Ok { trees = [ Reader.Leaf _ ]; _ } -> true | _ -> false)
    (lazy "");
  input_error h "empty array" [||] Reader.Missing_eof;
  input_error h "missing Eof" [| x |] Reader.Missing_eof;
  input_error h "Eof followed by a token" [| x; eof; x |] (Reader.Eof_not_last { index = 1 });
  input_error h "duplicate Eof" [| eof; eof |] (Reader.Eof_not_last { index = 0 });
  input_error h "Eof first, token, Eof" [| eof; x; eof |] (Reader.Eof_not_last { index = 0 });
  input_error h "contract checked before grouping" [| mk (Token.Close Token.Paren) ")"; eof; x |]
    (Reader.Eof_not_last { index = 1 })
