open Token

type output = { tokens : Token.t array; warnings : Diagnostic.t list }

exception Lex_error of Diagnostic.t

let is_digit c = c >= '0' && c <= '9'
let is_hex c = is_digit c || (c >= 'a' && c <= 'f') || (c >= 'A' && c <= 'F')
let is_ident_start c = (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || c = '_'
let is_ident_char c = is_ident_start c || is_digit c
let is_ws = function ' ' | '\t' | '\r' | '\n' -> true | _ -> false

let is_op_char = function
  | '+' | '-' | '*' | '/' | '%' | '^' | '<' | '>' | '=' | '~' | '!' | '&' | '|'
  | '?' | '@' | '$' | '#' | ':' | '.' ->
      true
  | _ -> false

let utf8_length s i =
  let n = String.length s in
  let byte j = Char.code (String.unsafe_get s j) in
  let cont j = j < n && byte j land 0xC0 = 0x80 in
  let in_range j lo hi = j < n && byte j >= lo && byte j <= hi in
  let b0 = byte i in
  if b0 < 0x80 then Some 1
  else if b0 < 0xC2 then None
  else if b0 < 0xE0 then if cont (i + 1) then Some 2 else None
  else if b0 < 0xF0 then
    let ok1 =
      if b0 = 0xE0 then in_range (i + 1) 0xA0 0xBF
      else if b0 = 0xED then in_range (i + 1) 0x80 0x9F
      else cont (i + 1)
    in
    if ok1 && cont (i + 2) then Some 3 else None
  else if b0 < 0xF5 then
    let ok1 =
      if b0 = 0xF0 then in_range (i + 1) 0x90 0xBF
      else if b0 = 0xF4 then in_range (i + 1) 0x80 0x8F
      else cont (i + 1)
    in
    if ok1 && cont (i + 2) && cont (i + 3) then Some 4 else None
  else None

let first_invalid_utf8 s =
  let n = String.length s in
  let rec go i =
    if i >= n then None
    else match utf8_length s i with Some k -> go (i + k) | None -> Some i
  in
  go 0

let is_operand tok =
  match tok.kind with
  | Ident | Raw_ident _ | Int _ | Float _ | String | Raw_region _ | Close _ ->
      true
  | Op | Punct | Open _ | Eof -> false

let lex src =
  let s = Source.text src in
  let n = String.length s in
  let span start stop = Source.span src ~start ~stop in
  let fail ?notes code start stop msg =
    raise (Lex_error (Diagnostic.make ?notes code (span start stop) msg))
  in
  let char_is i p = i < n && p (String.unsafe_get s i) in
  let char_eq i c = i < n && String.unsafe_get s i = c in
  let scan_while i p =
    let j = ref i in
    while char_is !j p do incr j done;
    !j
  in
  let scan_ident i = scan_while (i + 1) is_ident_char in
  let scan_digits i = scan_while (i + 1) (fun c -> is_digit c || c = '_') in
  (* [i] points just after "--" or "#tag": returns (level, body_start) for an
     opener [=ⁿ[. *)
  let long_bracket i =
    if char_eq i '[' then
      let j = scan_while (i + 1) (fun c -> c = '=') in
      if char_eq j '[' then Some (j - i - 1, j + 1) else None
    else None
  in
  (* Linear search for the first ]=ⁿ] at or after [i]; returns its end. *)
  let find_long_close i level =
    let rec go k =
      if k >= n then None
      else if String.unsafe_get s k <> ']' then go (k + 1)
      else
        let e = scan_while (k + 1) (fun c -> c = '=') in
        if e - k - 1 = level && char_eq e ']' then Some (e + 1) else go e
    in
    go i
  in
  let raw_opener i =
    if char_eq i '#' && char_is (i + 1) is_ident_start then
      let tag_stop = scan_ident (i + 1) in
      if char_eq tag_stop '{' then Some (tag_stop, `Brace)
      else
        match long_bracket tag_stop with
        | Some (level, body) -> Some (tag_stop, `Long (level, body))
        | None -> None
    else None
  in
  let contains_lf start stop =
    let rec go k = k < stop && (String.unsafe_get s k = '\n' || go (k + 1)) in
    go start
  in
  let warnings = ref [] in
  let tokens = ref [] in
  let prev = ref None in
  let pos = ref 0 in
  let scan_trivia () =
    let acc = ref [] and newline = ref false and stop = ref false in
    let add kind start stop =
      acc :=
        {
          trivia_kind = kind;
          trivia_span = span start stop;
          trivia_text = String.sub s start (stop - start);
        }
        :: !acc
    in
    while (not !stop) && !pos < n do
      let st = !pos in
      let c = String.unsafe_get s st in
      if is_ws c then begin
        pos := scan_while st is_ws;
        if contains_lf st !pos then newline := true;
        add Whitespace st !pos
      end
      else if c = '-' && char_eq (st + 1) '-' then begin
        (match (!acc, !prev) with
        | [], Some p when is_operand p ->
            warnings :=
              Diagnostic.make Lex_comment_after_operand (span st (st + 2))
                "`--` directly after an operand starts a comment; separate \
                 the characters with spaces if operators were intended"
              :: !warnings
        | _ -> ());
        match long_bracket (st + 2) with
        | Some (level, body) -> (
            match find_long_close body level with
            | Some e ->
                pos := e;
                if contains_lf st e then newline := true;
                add (Long_comment level) st e
            | None ->
                fail Lex_comment st body
                  (Printf.sprintf
                     "unterminated long comment: no closing `]%s]`"
                     (String.make level '=')))
        | None ->
            pos := scan_while st (fun c -> c <> '\n');
            add Line_comment st !pos
      end
      else stop := true
    done;
    (List.rev !acc, !newline)
  in
  let scan_string st =
    let rec go k =
      if k >= n then fail Lex_string st n "unterminated string literal"
      else
        match String.unsafe_get s k with
        | '"' -> k + 1
        | '\n' ->
            fail Lex_string k (k + 1)
              ~notes:[ Diagnostic.note (span st (st + 1)) "string starts here" ]
              "line ending (LF) inside string literal"
        | '\r' when char_eq (k + 1) '\n' ->
            fail Lex_string k (k + 2)
              ~notes:[ Diagnostic.note (span st (st + 1)) "string starts here" ]
              "line ending (CRLF) inside string literal"
        | '\\' -> (
            if k + 1 >= n then fail Lex_string st n "unterminated string literal"
            else
              match String.unsafe_get s (k + 1) with
              | 'n' | 't' | 'r' | '\\' | '"' | '0' -> go (k + 2)
              | 'u' -> go (scan_unicode_escape k)
              | _ ->
                  let len = Option.value (utf8_length s (k + 1)) ~default:1 in
                  fail Lex_escape k (k + 1 + len)
                    "unknown escape sequence; expected one of \\n \\t \\r \
                     \\\\ \\\" \\0 \\u{...}")
        | _ -> go (k + 1)
    and scan_unicode_escape k =
      let lb = k + 2 in
      if not (char_eq lb '{') then
        fail Lex_escape k (min n (lb + 1))
          "malformed unicode escape: expected `{` after `\\u`"
      else
        let digits_end = scan_while (lb + 1) is_hex in
        let ndigits = digits_end - lb - 1 in
        if ndigits = 0 || ndigits > 6 then
          fail Lex_escape k (min n (digits_end + 1))
            "malformed unicode escape: expected 1 to 6 hexadecimal digits"
        else if not (char_eq digits_end '}') then
          fail Lex_escape k (min n (digits_end + 1))
            "malformed unicode escape: expected `}`"
        else
          let v = int_of_string ("0x" ^ String.sub s (lb + 1) ndigits) in
          if v > 0x10FFFF || (v >= 0xD800 && v <= 0xDFFF) then
            fail Lex_escape k (digits_end + 1)
              "unicode escape is not a Unicode scalar value"
          else digits_end + 1
    in
    go (st + 1)
  in
  let finish_number j make_kind =
    if char_is j is_ident_start then
      let e = scan_ident j in
      (make_kind (Some (span j e)), e)
    else (make_kind None, j)
  in
  let scan_number st =
    if
      String.unsafe_get s st = '0'
      && char_eq (st + 1) 'x'
      && char_is (st + 2) (fun c -> is_hex c || c = '_')
    then
      let j = scan_while (st + 2) (fun c -> is_hex c || c = '_') in
      finish_number j (fun suffix -> Int { hex = true; suffix })
    else
      let j = scan_digits st in
      let is_float = ref false in
      let j =
        if char_eq j '.' && char_is (j + 1) is_digit then (
          is_float := true;
          scan_digits (j + 1))
        else j
      in
      let j =
        if char_is j (fun c -> c = 'e' || c = 'E') then
          if char_is (j + 1) is_digit then (
            is_float := true;
            scan_digits (j + 1))
          else if
            char_is (j + 1) (fun c -> c = '+' || c = '-')
            && char_is (j + 2) is_digit
          then (
            is_float := true;
            scan_digits (j + 2))
          else j
        else j
      in
      if !is_float then finish_number j (fun suffix -> Float { suffix })
      else finish_number j (fun suffix -> Int { hex = false; suffix })
  in
  let scan_raw st tag_stop form =
    let tag = span (st + 1) tag_stop in
    match form with
    | `Brace ->
        let rec go k depth =
          if k >= n then
            fail Lex_raw st (tag_stop + 1)
              "unterminated raw region: no `}` balances the opening `{`"
          else
            match String.unsafe_get s k with
            | '{' -> go (k + 1) (depth + 1)
            | '}' -> if depth = 1 then k + 1 else go (k + 1) (depth - 1)
            | _ -> go (k + 1) depth
        in
        let e = go (tag_stop + 1) 1 in
        ( Raw_region { tag; form = Brace_form; content = span (tag_stop + 1) (e - 1) },
          e )
    | `Long (level, body) -> (
        match find_long_close body level with
        | Some e ->
            ( Raw_region
                { tag; form = Long_form level; content = span body (e - level - 2) },
              e )
        | None ->
            fail Lex_raw st body
              (Printf.sprintf "unterminated raw region: no closing `]%s]`"
                 (String.make level '=')))
  in
  let scan_op st =
    let rec go j =
      if
        j < n
        && is_op_char (String.unsafe_get s j)
        && (not (String.unsafe_get s j = '-' && char_eq (j + 1) '-'))
        && Option.is_none (raw_opener j)
      then go (j + 1)
      else j
    in
    go (st + 1)
  in
  let bad_char st =
    let c = String.unsafe_get s st in
    let code = Char.code c in
    let len = Option.value (utf8_length s st) ~default:1 in
    let msg =
      if code >= 0x80 then
        "non-ASCII character outside a string, comment, or raw region"
      else if code < 0x20 || code = 0x7F then
        Printf.sprintf "control character U+%04X is not allowed here" code
      else Printf.sprintf "character `%c` is not allowed here" c
    in
    fail Lex_char st (st + len) msg
  in
  let rec loop () =
    let trivia, newline = scan_trivia () in
    let st = !pos in
    let kind, stop =
      if st >= n then (Eof, n)
      else
        let c = String.unsafe_get s st in
        if is_ident_start c then (Ident, scan_ident st)
        else if is_digit c then scan_number st
        else if c = '"' then (String, scan_string st)
        else if c = '`' then
          if char_is (st + 1) is_ident_start then
            let e = scan_ident (st + 1) in
            if char_eq e '`' then (Raw_ident { name = span (st + 1) e }, e + 1)
            else
              fail Lex_raw_ident st e
                "unterminated raw identifier: expected a closing backtick"
          else
            fail Lex_raw_ident st (st + 1)
              "a backtick must be followed by an identifier and a closing \
               backtick"
        else
          match raw_opener st with
          | Some (tag_stop, form) -> scan_raw st tag_stop form
          | None -> (
              if is_op_char c then (Op, scan_op st)
              else
                match c with
                | ',' | ';' -> (Punct, st + 1)
                | '(' -> (Open Paren, st + 1)
                | '[' -> (Open Bracket, st + 1)
                | '{' -> (Open Brace, st + 1)
                | ')' -> (Close Paren, st + 1)
                | ']' -> (Close Bracket, st + 1)
                | '}' -> (Close Brace, st + 1)
                | _ -> bad_char st)
    in
    let tok =
      {
        kind;
        text = String.sub s st (stop - st);
        span = span st stop;
        space_before = trivia <> [];
        newline_before = newline;
        leading_trivia = trivia;
      }
    in
    tokens := tok :: !tokens;
    prev := Some tok;
    pos := stop;
    match kind with Eof -> () | _ -> loop ()
  in
  match first_invalid_utf8 s with
  | Some i ->
      Error
        (Diagnostic.make Lex_utf8 (span i (i + 1))
           (Printf.sprintf "invalid UTF-8: byte 0x%02X does not start a \
                            well-formed sequence"
              (Char.code s.[i])))
  | None -> (
      match loop () with
      | () ->
          Ok
            {
              tokens = Array.of_list (List.rev !tokens);
              warnings = List.rev !warnings;
            }
      | exception Lex_error d -> Error d)
