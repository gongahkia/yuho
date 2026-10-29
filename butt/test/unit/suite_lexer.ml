(* Hand-specified lexer cases, grouped by conformance ID
   (docs/conformance-plan.md, suite LEX). *)

open Front
open Harness

let tok_at h name input idx f =
  with_ok h name input (fun o ->
      if idx >= Array.length o.tokens then report h name false (lazy "index out of range")
      else f o.tokens.(idx))

let flags h name input idx (space, nl) =
  tok_at h name input idx (fun t ->
      report h name
        (t.space_before = space && t.newline_before = nl)
        (lazy
          (Printf.sprintf "expected space=%b newline=%b, got space=%b newline=%b" space nl
             t.space_before t.newline_before)))

let suffix h name input idx expected =
  tok_at h name input idx (fun t ->
      let got =
        match t.kind with
        | Int { suffix; _ } | Float { suffix } -> Option.map (fun (s : Span.t) -> (s.start, s.stop)) suffix
        | _ -> Some (-1, -1)
      in
      report h name (got = expected) (lazy "suffix span differs"))

let hex h name input expected =
  tok_at h name input 0 (fun t ->
      report h name
        (match t.kind with Int { hex; _ } -> hex = expected | _ -> false)
        (lazy "hex flag differs"))

let raw h name input idx ~tag ~content ~form =
  tok_at h name input idx (fun t ->
      match t.kind with
      | Raw_region r ->
          report h name
            (span_eq r.tag tag && span_eq r.content content && r.form = form)
            (lazy
              (Printf.sprintf "got tag=%s content=%s" (show_span r.tag) (show_span r.content)))
      | _ -> report h name false (lazy "not a raw region"))

let warnings h name input expected =
  with_ok h name input (fun o ->
      let got =
        List.map
          (fun (d : Diagnostic.t) ->
            (Diagnostic.code_name d.code, d.primary.start, d.primary.stop))
          o.warnings
      in
      let expected =
        List.map (fun (a, b) -> ("W-LEX-COMMENT-AFTER-OPERAND", a, b)) expected
      in
      report h name (got = expected)
        (lazy
          (String.concat ", "
             (List.map (fun (c, a, b) -> Printf.sprintf "%s [%d,%d)" c a b) got))))

let line_col h name input offset expected =
  let got = Source.line_col (src input) offset in
  report h name (got = expected)
    (lazy (Printf.sprintf "offset %d: got %d:%d" offset (fst got) (snd got)))

let run h =
  let open Diagnostic in
  group h "LEX-01 utf-8, spans, line ends";
  toks h "empty source" "" [];
  tok_at h "empty source eof" "" 0 (fun t ->
      report h "empty source eof" (tuple t = ("eof", "", 0, 0)) (lazy "eof differs"));
  toks h "utf-8 in string" "\"\xc3\xa9\"" [ ("string", "\"\xc3\xa9\"", 0, 4) ];
  toks h "utf-8 in comment" "-- \xf0\x9f\x98\x80\nx" [ ("ident", "x", 8, 9) ];
  toks h "utf-8 in raw region" "#t{\xce\xbb}" [ ("raw-region", "#t{\xce\xbb}", 0, 6) ];
  toks h "max scalar in string" "\"\xf4\x8f\xbf\xbf\"" [ ("string", "\"\xf4\x8f\xbf\xbf\"", 0, 6) ];
  lex_err h "invalid byte" "a\xff" Lex_utf8 (1, 2);
  lex_err h "overlong encoding" "\xc0\x80" Lex_utf8 (0, 1);
  lex_err h "overlong 3-byte" "\"\xe0\x80\xaf\"" Lex_utf8 (1, 2);
  lex_err h "surrogate" "\"\xed\xa0\x80\"" Lex_utf8 (1, 2);
  lex_err h "truncated sequence" "\"\xe2\x82\"" Lex_utf8 (1, 2);
  lex_err h "above U+10FFFF" "\xf4\x90\x80\x80" Lex_utf8 (0, 1);
  lex_err h "lone continuation" "\x80" Lex_utf8 (0, 1);
  lex_err h "truncated at end" "ab\xe2\x82" Lex_utf8 (2, 3);
  lex_err h "utf-8 checked before other errors" "\"abc\xff" Lex_utf8 (4, 5);
  toks h "crlf" "a\r\nb" [ ("ident", "a", 0, 1); ("ident", "b", 3, 4) ];
  flags h "crlf sets newline" "a\r\nb" 1 (true, true);
  line_col h "crlf: CR stays on line 1" "a\r\nb" 1 (1, 2);
  line_col h "crlf: LF stays on line 1" "a\r\nb" 2 (1, 3);
  line_col h "crlf: next line" "a\r\nb" 3 (2, 1);
  line_col h "end offset" "a\r\nb" 4 (2, 2);
  toks h "lone CR is whitespace" "a\rb" [ ("ident", "a", 0, 1); ("ident", "b", 2, 3) ];
  flags h "lone CR is not a line end" "a\rb" 1 (true, false);
  line_col h "lone CR does not start a line" "a\rb" 2 (1, 3);
  toks h "multi-line spans" "x\n  yy" [ ("ident", "x", 0, 1); ("ident", "yy", 4, 6) ];
  line_col h "column in bytes" "x\n  yy" 4 (2, 3);
  line_col h "column after utf-8" "\"\xc3\xa9\"x" 4 (1, 5);
  toks h "tab and space" "\t a" [ ("ident", "a", 2, 3) ];

  group h "LEX-02 maximal operator runs";
  toks h "a<-b" "a<-b" [ ("ident", "a", 0, 1); ("op", "<-", 1, 3); ("ident", "b", 3, 4) ];
  toks h "a+-b" "a+-b" [ ("ident", "a", 0, 1); ("op", "+-", 1, 3); ("ident", "b", 3, 4) ];
  toks h "x|>f" "x|>f" [ ("ident", "x", 0, 1); ("op", "|>", 1, 3); ("ident", "f", 3, 4) ];
  toks h "a<=>b" "a<=>b" [ ("ident", "a", 0, 1); ("op", "<=>", 1, 4); ("ident", "b", 4, 5) ];
  toks h "a<=>-b is one run" "a<=>-b" [ ("ident", "a", 0, 1); ("op", "<=>-", 1, 5); ("ident", "b", 5, 6) ];
  toks h "a.b" "a.b" [ ("ident", "a", 0, 1); ("op", ".", 1, 2); ("ident", "b", 2, 3) ];
  toks h "1..2" "1..2" [ ("int", "1", 0, 1); ("op", "..", 1, 3); ("int", "2", 3, 4) ];
  toks h "every operator character" "+-*/%^<>=~!&|?@$#:." [ ("op", "+-*/%^<>=~!&|?@$#:.", 0, 19) ];
  toks h "a - -b" "a - -b"
    [ ("ident", "a", 0, 1); ("op", "-", 2, 3); ("op", "-", 4, 5); ("ident", "b", 5, 6) ];
  toks h "punctuation" "a,b;c"
    [ ("ident", "a", 0, 1); ("punct", ",", 1, 2); ("ident", "b", 2, 3); ("punct", ";", 3, 4); ("ident", "c", 4, 5) ];
  toks h "delimiters" "f(x)[y]{z}"
    [
      ("ident", "f", 0, 1); ("open", "(", 1, 2); ("ident", "x", 2, 3); ("close", ")", 3, 4);
      ("open", "[", 4, 5); ("ident", "y", 5, 6); ("close", "]", 6, 7);
      ("open", "{", 7, 8); ("ident", "z", 8, 9); ("close", "}", 9, 10);
    ];
  toks h "punct splits operator runs" "+,-" [ ("op", "+", 0, 1); ("punct", ",", 1, 2); ("op", "-", 2, 3) ];
  toks h "trailing # is an operator" "x+#" [ ("ident", "x", 0, 1); ("op", "+#", 1, 3) ];
  toks h "#t without opener" "#t" [ ("op", "#", 0, 1); ("ident", "t", 1, 2) ];
  toks h "identifier forms" "_ a_1 Z9"
    [ ("ident", "_", 0, 1); ("ident", "a_1", 2, 5); ("ident", "Z9", 6, 8) ];

  group h "LEX-03 lexing is independent of declarations";
  (let decl = "syntax infix \"<|>\" at 50 => f\nsyntax infix \"+-\" at 60 => g\n" in
   let body = "\na <|> b +- c" in
   match (lex body, lex (decl ^ body)) with
   | Ok alone, Ok combined ->
       let shift = String.length decl in
       let alone = List.map tuple (non_eof alone) in
       let tail =
         List.filteri (fun i _ -> i >= List.length (non_eof combined) - List.length alone) (non_eof combined)
         |> List.map (fun (t : Token.t) -> (Token.kind_name t.kind, t.text, t.span.start - shift, t.span.stop - shift))
       in
       report h "body tokens unchanged by preceding declarations" (alone = tail) (lazy (show tail));
       report h "declared operators still lex by maximal run"
         (alone = [ ("ident", "a", 1, 2); ("op", "<|>", 3, 6); ("ident", "b", 7, 8); ("op", "+-", 9, 11); ("ident", "c", 12, 13) ])
         (lazy (show alone))
   | _ -> report h "stability inputs lex" false (lazy "unexpected error"));

  group h "LEX-04 jointness flags";
  flags h "f(x) joint" "f(x)" 1 (false, false);
  flags h "f (x) spaced" "f (x)" 1 (true, false);
  flags h "f\\n(x) newline" "f\n(x)" 1 (true, true);
  flags h "f\\r\\n(x) newline" "f\r\n(x)" 1 (true, true);
  flags h "line comment then newline" "f--c\n(x)" 1 (true, true);
  flags h "long comment with newline" "f--[[a\nb]](x)" 1 (true, true);
  flags h "long comment without newline" "f--[[c]](x)" 1 (true, false);
  flags h "first token" "x" 0 (false, false);
  flags h "first token after space" " x" 0 (true, false);
  flags h "eof after newline" "x\n" 1 (true, true);

  group h "LEX-05 literals and suffixes";
  toks h "3.0m" "3.0m" [ ("float", "3.0m", 0, 4) ];
  suffix h "3.0m suffix" "3.0m" 0 (Some (3, 4));
  toks h "10ms" "10ms" [ ("int", "10ms", 0, 4) ];
  suffix h "10ms suffix" "10ms" 0 (Some (2, 4));
  toks h "1e5" "1e5" [ ("float", "1e5", 0, 3) ];
  suffix h "1e5 no suffix" "1e5" 0 None;
  toks h "3em" "3em" [ ("int", "3em", 0, 3) ];
  suffix h "3em suffix" "3em" 0 (Some (1, 3));
  toks h "0x1Fu8" "0x1Fu8" [ ("int", "0x1Fu8", 0, 6) ];
  suffix h "0x1Fu8 suffix" "0x1Fu8" 0 (Some (4, 6));
  hex h "0x1Fu8 hex" "0x1Fu8" true;
  toks h "3 m" "3 m" [ ("int", "3", 0, 1); ("ident", "m", 2, 3) ];
  toks h "1." "1." [ ("int", "1", 0, 1); ("op", ".", 1, 2) ];
  toks h ".5" ".5" [ ("op", ".", 0, 1); ("int", "5", 1, 2) ];
  toks h "underscores" "1_000" [ ("int", "1_000", 0, 5) ];
  toks h "negative exponent" "1.5e-3" [ ("float", "1.5e-3", 0, 6) ];
  toks h "E and +" "1E+2" [ ("float", "1E+2", 0, 4) ];
  toks h "1e+ is suffix e then op" "1e+" [ ("int", "1e", 0, 2); ("op", "+", 2, 3) ];
  suffix h "1e+ suffix" "1e+" 0 (Some (1, 2));
  toks h "0x without digits" "0x" [ ("int", "0x", 0, 2) ];
  hex h "0x is decimal 0 with suffix" "0x" false;
  suffix h "0x suffix" "0x" 0 (Some (1, 2));
  toks h "0x_" "0x_" [ ("int", "0x_", 0, 3) ];
  hex h "0x_ is hex" "0x_" true;
  hex h "0X is not hex" "0X1" false;
  suffix h "0X1 suffix" "0X1" 0 (Some (1, 3));
  suffix h "hex then suffix" "0xffg" 0 (Some (4, 5));
  toks h "hex then dot" "0x1.5" [ ("int", "0x1", 0, 3); ("op", ".", 3, 4); ("int", "5", 4, 5) ];
  toks h "1.5.3" "1.5.3" [ ("float", "1.5", 0, 3); ("op", ".", 3, 4); ("int", "3", 4, 5) ];
  suffix h "long suffix" "12abc_9" 0 (Some (2, 7));
  suffix h "suffix after underscore" "1_a" 0 (Some (2, 3));
  toks h "1.e5" "1.e5" [ ("int", "1", 0, 1); ("op", ".", 1, 2); ("ident", "e5", 2, 4) ];
  suffix h "float suffix after exponent" "1.5e5x" 0 (Some (5, 6));
  suffix h "exponent then e-suffix" "1e5e5" 0 (Some (3, 5));
  toks h "leading zeros" "007" [ ("int", "007", 0, 3) ];
  (let s = "\"a\\n\\t\\r\\\\\\\"\\0\"" in
   toks h "all simple escapes" s [ ("string", s, 0, 15) ]);
  (let s = "\"\\u{1F600}\\u{0}\\u{10FFFF}\"" in
   toks h "unicode escapes" s [ ("string", s, 0, String.length s) ]);
  (let s = "\"(]{}\\\"\"" in
   toks h "delimiters inside string" s [ ("string", s, 0, 8) ]);
  toks h "tab inside string" "\"a\tb\"" [ ("string", "\"a\tb\"", 0, 5) ];
  toks h "string has no suffix" "\"a\"x" [ ("string", "\"a\"", 0, 3); ("ident", "x", 3, 4) ];
  flags h "ident after string is joint" "\"a\"x" 1 (false, false);
  lex_err h "escape above U+10FFFF" "\"\\u{110000}\"" Lex_escape (1, 11);
  lex_err h "surrogate escape" "\"\\u{D800}\"" Lex_escape (1, 9);
  lex_err h "empty unicode escape" "\"\\u{}\"" Lex_escape (1, 5);
  lex_err h "seven-digit unicode escape" "\"\\u{1234567}\"" Lex_escape (1, 12);
  lex_err h "unclosed unicode escape" "\"\\u{12\"" Lex_escape (1, 7);
  lex_err h "unicode escape without brace" "\"\\u12\"" Lex_escape (1, 4);
  lex_err h "unknown escape" "\"\\q\"" Lex_escape (1, 3);
  lex_err h "escape of non-ASCII" "\"\\\xc3\xa9\"" Lex_escape (1, 4);
  lex_err h "unterminated string" "\"abc" Lex_string (0, 4);
  lex_err h "lone quote" "\"" Lex_string (0, 1);
  lex_err h "backslash at end" "\"a\\" Lex_string (0, 3);

  group h "LEX-05 line endings inside strings";
  lex_err h "LF in string" "\"a\nb\"" Lex_string (2, 3);
  lex_err h "CRLF in string covers both bytes" "\"a\r\nb\"" Lex_string (2, 4);
  toks h "lone CR in string is a string byte" "\"a\rb\"" [ ("string", "\"a\rb\"", 0, 5) ];
  toks h "lone CR before closing quote" "\"a\r\"" [ ("string", "\"a\r\"", 0, 4) ];
  toks h "two lone CRs" "\"\r\r\"" [ ("string", "\"\r\r\"", 0, 4) ];
  lex_err h "lone CR then CRLF" "\"\r\r\n\"" Lex_string (2, 4);
  lex_err h "lone CR then end of input" "\"a\r" Lex_string (0, 3);
  toks h "escaped \\r and \\n" "\"\\r\\n\"" [ ("string", "\"\\r\\n\"", 0, 6) ];
  lex_err h "backslash before lone CR" "\"\\\r\"" Lex_escape (1, 3);
  lex_err h "backslash before LF" "\"\\\n\"" Lex_escape (1, 3);
  flags h "lone CR in string does not affect next token" "\"\r\"x" 1 (false, false);
  line_col h "lone CR in string does not start a line" "\"\r\"x" 3 (1, 4);

  group h "LEX-06 raw regions";
  toks h "brace form nesting" "#sql{ a { b } c }" [ ("raw-region", "#sql{ a { b } c }", 0, 17) ];
  raw h "brace form parts" "#sql{ a { b } c }" 0 ~tag:(1, 4) ~content:(5, 16) ~form:Token.Brace_form;
  toks h "long form level 1" "#t[=[ ]] x ]=]" [ ("raw-region", "#t[=[ ]] x ]=]", 0, 14) ];
  raw h "long form parts" "#t[=[ ]] x ]=]" 0 ~tag:(1, 2) ~content:(5, 11) ~form:(Token.Long_form 1);
  raw h "long form level 0" "#t[[a]]" 0 ~tag:(1, 2) ~content:(4, 5) ~form:(Token.Long_form 0);
  raw h "empty long form" "#t[[]]" 0 ~tag:(1, 2) ~content:(4, 4) ~form:(Token.Long_form 0);
  raw h "empty brace form" "#t{}" 0 ~tag:(1, 2) ~content:(3, 3) ~form:Token.Brace_form;
  toks h "#t[i] is not raw" "#t[i]"
    [ ("op", "#", 0, 1); ("ident", "t", 1, 2); ("open", "[", 2, 3); ("ident", "i", 3, 4); ("close", "]", 4, 5) ];
  toks h "space before brace" "#t {x}"
    [ ("op", "#", 0, 1); ("ident", "t", 1, 2); ("open", "{", 3, 4); ("ident", "x", 4, 5); ("close", "}", 5, 6) ];
  toks h "space after #" "# t{x}"
    [ ("op", "#", 0, 1); ("ident", "t", 2, 3); ("open", "{", 3, 4); ("ident", "x", 4, 5); ("close", "}", 5, 6) ];
  toks h "#t[=x] is not raw" "#t[=x]"
    [ ("op", "#", 0, 1); ("ident", "t", 1, 2); ("open", "[", 2, 3); ("op", "=", 3, 4); ("ident", "x", 4, 5); ("close", "]", 5, 6) ];
  toks h "tag must be an identifier" "#1{x}"
    [ ("op", "#", 0, 1); ("int", "1", 1, 2); ("open", "{", 2, 3); ("ident", "x", 3, 4); ("close", "}", 4, 5) ];
  toks h "raw region ends an operator run" "a+#t{x}"
    [ ("ident", "a", 0, 1); ("op", "+", 1, 2); ("raw-region", "#t{x}", 2, 7) ];
  toks h "# before raw region" "a##t{x}"
    [ ("ident", "a", 0, 1); ("op", "#", 1, 2); ("raw-region", "#t{x}", 2, 7) ];
  toks h "anything goes inside" "#t{\xc3\xa9\n\x01}" [ ("raw-region", "#t{\xc3\xa9\n\x01}", 0, 8) ];
  toks h "comment marker inside" "#t{ -- }" [ ("raw-region", "#t{ -- }", 0, 8) ];
  toks h "underscore tag" "#_x{}" [ ("raw-region", "#_x{}", 0, 5) ];
  lex_err h "unterminated brace form" "#t{ {" Lex_raw (0, 3);
  lex_err h "unbalanced brace form" "#t{ { }" Lex_raw (0, 3);
  lex_err h "wrong closing level" "#t[==[ abc ]=]" Lex_raw (0, 6);
  lex_err h "unterminated level 0" "#t[[ a ]=]" Lex_raw (0, 4);

  group h "LEX-07 raw identifiers";
  toks h "raw identifier" "`match`" [ ("raw-ident", "`match`", 0, 7) ];
  tok_at h "raw identifier name" "`match`" 0 (fun t ->
      report h "raw identifier name"
        (match t.kind with Raw_ident { name } -> span_eq name (1, 6) | _ -> false)
        (lazy "name span differs"));
  toks h "adjacent raw identifiers" "`a``b`" [ ("raw-ident", "`a`", 0, 3); ("raw-ident", "`b`", 3, 6) ];
  toks h "plain ident is a different kind" "match" [ ("ident", "match", 0, 5) ];
  lex_err h "digit after backtick" "`1`" Lex_raw_ident (0, 1);
  lex_err h "unterminated raw identifier" "`abc" Lex_raw_ident (0, 4);
  lex_err h "lone backtick" "`" Lex_raw_ident (0, 1);
  lex_err h "space in raw identifier" "`a b`" Lex_raw_ident (0, 2);

  group h "LEX-09 comments";
  toks h "line comment" "-- hi\nx" [ ("ident", "x", 6, 7) ];
  toks h "long comment" "--[[ multi\nline ]]x" [ ("ident", "x", 18, 19) ];
  toks h "long comment level 2" "--[==[ ]] ]=] ]==]x" [ ("ident", "x", 18, 19) ];
  toks h "--[ space is a line comment" "--[ x\ny" [ ("ident", "y", 6, 7) ];
  toks h "--[=x is a line comment" "--[=x\ny" [ ("ident", "y", 6, 7) ];
  toks h "long comments do not nest" "--[[ --[[ ]] x" [ ("ident", "x", 13, 14) ];
  toks h "adjacent long comments" "--[[a]]--[[b]]c" [ ("ident", "c", 14, 15) ];
  toks h "comment at end without newline" "x --c" [ ("ident", "x", 0, 1) ];
  toks h "bare --" "--" [];
  toks h "non-ASCII in comment" "-- \xc3\xa9" [];
  toks h "control character in comment" "--\x01\nx" [ ("ident", "x", 4, 5) ];
  lex_err h "unterminated long comment" "--[[ abc" Lex_comment (0, 4);
  lex_err h "wrong level closer" "--[=[ ]] " Lex_comment (0, 5);
  tok_at h "trivia kinds" "  -- a\n--[=[b]=]x" 0 (fun t ->
      let got =
        List.map
          (fun (tv : Token.trivia) ->
            ( (match tv.trivia_kind with
              | Whitespace -> "ws"
              | Line_comment -> "line"
              | Long_comment n -> Printf.sprintf "long/%d" n),
              tv.trivia_span.start,
              tv.trivia_span.stop ))
          t.leading_trivia
      in
      report h "trivia kinds"
        (got = [ ("ws", 0, 2); ("line", 2, 6); ("ws", 6, 7); ("long/1", 7, 16) ])
        (lazy "trivia differs"));

  group h "LEX-10 comment priority and lint";
  toks h "x--y" "x--y" [ ("ident", "x", 0, 1) ];
  warnings h "x--y warns" "x--y" [ (1, 3) ];
  toks h "a+--b" "a+--b" [ ("ident", "a", 0, 1); ("op", "+", 1, 2) ];
  warnings h "a+--b does not warn" "a+--b" [];
  warnings h "spaced comment does not warn" "x -- y" [];
  toks h "x---y" "x---y" [ ("ident", "x", 0, 1) ];
  warnings h "x---y warns" "x---y" [ (1, 3) ];
  warnings h "after close delimiter" "f()--c" [ (3, 5) ];
  warnings h "long comment after number" "1--[[c]]2" [ (1, 3) ];
  toks h "long comment between numbers" "1--[[c]]2" [ ("int", "1", 0, 1); ("int", "2", 8, 9) ];
  warnings h "two warnings in order" "x--a\ny--b" [ (1, 3); (6, 8) ];
  warnings h "after string" "\"s\"--c" [ (3, 5) ];
  warnings h "after raw identifier" "`a`--c" [ (3, 5) ];
  warnings h "after raw region" "#t{}--c" [ (4, 6) ];
  warnings h "after open delimiter" "(--c" [];
  warnings h "at start of input" "--c" [];
  warnings h "after newline" "x\n--c" [];
  warnings h "after punctuation" "x,--c" [];

  group h "LEX-11 raw regions and strings";
  (let s = "#json{ {\"a\": \"}\"} }" in
   toks h "brace form closes at brace inside string" s
     [ ("raw-region", "#json{ {\"a\": \"}\"}", 0, 17); ("close", "}", 18, 19) ];
   raw h "early close content" s 0 ~tag:(1, 5) ~content:(6, 16) ~form:Token.Brace_form);
  (let s = "#json[=[ {\"a\": \"}\"} ]=]" in
   toks h "long form is unaffected" s [ ("raw-region", s, 0, 23) ];
   raw h "long form content" s 0 ~tag:(1, 5) ~content:(8, 20) ~form:(Token.Long_form 1));

  group h "LEX-12 characters outside allowed regions";
  lex_err h "lambda" "\xce\xbb" Lex_char (0, 2);
  lex_err h "arrow between tokens" "x \xe2\x86\x92 y" Lex_char (2, 5);
  lex_err h "form feed" "\x0c" Lex_char (0, 1);
  lex_err h "vertical tab" "x\x0b" Lex_char (1, 2);
  lex_err h "DEL" "\x7f" Lex_char (0, 1);
  lex_err h "NUL" "\x00" Lex_char (0, 1);
  lex_err h "byte order mark" "\xef\xbb\xbfx" Lex_char (0, 3);
  lex_err h "backslash" "a\\b" Lex_char (1, 2);
  lex_err h "single quote" "'x'" Lex_char (0, 1);
  toks h "non-ASCII in string" "\"\xce\xbb\"" [ ("string", "\"\xce\xbb\"", 0, 4) ];
  lex_err h "escape byte outside" "a\x1bb" Lex_char (1, 2);
  lex_err h "C1 control outside" "\xc2\x85" Lex_char (0, 2);

  group h "control bytes inside bodies (I-01, ratified)";
  toks h "U+0001 in string" "\"\x01\"" [ ("string", "\"\x01\"", 0, 3) ];
  toks h "NUL in string" "\"a\x00b\"" [ ("string", "\"a\x00b\"", 0, 5) ];
  toks h "ESC, BEL, DEL in string" "\"\x1b\x07\x7f\"" [ ("string", "\"\x1b\x07\x7f\"", 0, 5) ];
  toks h "NUL in line comment" "--\x00\nx" [ ("ident", "x", 4, 5) ];
  toks h "NUL and ESC in long comment" "--[[\x00\x1b]]x" [ ("ident", "x", 8, 9) ];
  toks h "NUL in brace raw region" "#t{\x00}" [ ("raw-region", "#t{\x00}", 0, 5) ];
  toks h "NUL in long raw region" "#t[[\x00\x1f]]" [ ("raw-region", "#t[[\x00\x1f]]", 0, 8) ];
  toks h "C1 control in string" "\"\xc2\x85\"" [ ("string", "\"\xc2\x85\"", 0, 4) ];
  lex_err h "invalid UTF-8 inside a string is still rejected" "\"\xc0\xaf\"" Lex_utf8 (1, 2);
  lex_err h "invalid UTF-8 inside a raw region is still rejected" "#t{\xff}" Lex_utf8 (3, 4);
  lex_err h "invalid UTF-8 inside a comment is still rejected" "-- \xed\xa0\x80" Lex_utf8 (3, 4);

  group h "safe rendering of confusing characters";
  let line input =
    match lex input with
    | Ok o -> Dump.token_line (src input) o.tokens.(0)
    | Error d -> render_diag input d
  in
  let expect name input expected =
    let got = line input in
    report h name (got = expected) (lazy got)
  in
  expect "NUL and ESC escaped in dump" "\"a\x00\x1b\"" {|1:1 [0,5) string "\"a\x00\x1B\""|};
  expect "DEL escaped in dump" "\"\x7f\"" {|1:1 [0,3) string "\"\x7F\""|};
  expect "lone CR escaped in dump" "\"\r\"" {|1:1 [0,3) string "\"\r\""|};
  expect "C1 control escaped in dump" "\"\xc2\x85\"" {|1:1 [0,4) string "\"\u{0085}\""|};
  expect "bidi override escaped in dump" "\"\xe2\x80\xae\"" {|1:1 [0,5) string "\"\u{202E}\""|};
  expect "zero-width no-break space escaped" "--\n\"\xef\xbb\xbf\"" {|2:1 [3,8) string "\"\u{FEFF}\"" space newline|};
  expect "ordinary UTF-8 kept" "\"\xc3\xa9\"" "1:1 [0,4) string \"\\\"\xc3\xa9\\\"\"";
  report h "Escape.quoted escapes invalid bytes" (Escape.quoted "a\xffb" = {|a\xFFb|}) (lazy (Escape.quoted "a\xffb"));
  report h "Escape.display leaves quotes and backslashes" (Escape.display {|a"\b|} = {|a"\b|}) (lazy "");
  (let s = Source.make ~name:"bad\x1bname" "\x00" in
   match Lexer.lex s with
   | Error d ->
       let r = Diagnostic.render s d in
       report h "diagnostic escapes file name"
         (r = "bad\\x1Bname:1:1 [0,1): error[E-LEX-CHAR]: control character U+0000 is not allowed here\n")
         (lazy r)
   | Ok _ -> report h "diagnostic escapes file name" false (lazy "expected error"));

  group h "diagnostic rendering";
  (match lex "x\n  \"abc" with
  | Error d ->
      report h "render string error"
        (render_diag "x\n  \"abc" d
        = "t:2:3 [4,8): error[E-LEX-STRING]: unterminated string literal\n")
        (lazy (render_diag "x\n  \"abc" d))
  | Ok _ -> report h "render string error" false (lazy "expected error"));
  match lex "\"a\nb\"" with
  | Error d ->
      report h "render with note"
        (render_diag "\"a\nb\"" d
        = "t:1:3 [2,3): error[E-LEX-STRING]: line ending (LF) inside string literal\n\
           t:1:1 [0,1): note: string starts here\n")
        (lazy (render_diag "\"a\nb\"" d))
  | Ok _ -> report h "render with note" false (lazy "expected error")
