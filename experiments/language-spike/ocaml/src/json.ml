type t =
  | Null
  | Bool of bool
  | Num of int
  | Str of string
  | Arr of t list
  | Obj of (string * t) list

exception Syntax of string

let parse input =
  let length = String.length input in
  let position = ref 0 in
  let fail message = raise (Syntax message) in
  let peek () = if !position < length then Some input.[!position] else None in
  let take () =
    match peek () with
    | None -> fail "unexpected end of JSON"
    | Some character ->
        incr position;
        character
  in
  let expect wanted =
    if take () <> wanted then fail "unexpected JSON delimiter"
  in
  let rec white () =
    match peek () with
    | Some (' ' | '\t' | '\r' | '\n') ->
        incr position;
        white ()
    | _ -> ()
  in
  let literal expected result =
    String.iter expect expected;
    result
  in
  let hex_value character =
    match character with
    | '0' .. '9' -> Char.code character - Char.code '0'
    | 'a' .. 'f' -> Char.code character - Char.code 'a' + 10
    | 'A' .. 'F' -> Char.code character - Char.code 'A' + 10
    | _ -> fail "invalid Unicode escape"
  in
  let add_codepoint buffer value =
    if value >= 0xd800 && value <= 0xdfff then fail "surrogate escape is unsupported";
    if value < 0x80 then Buffer.add_char buffer (Char.chr value)
    else if value < 0x800 then (
      Buffer.add_char buffer (Char.chr (0xc0 lor (value lsr 6)));
      Buffer.add_char buffer (Char.chr (0x80 lor (value land 0x3f))))
    else (
      Buffer.add_char buffer (Char.chr (0xe0 lor (value lsr 12)));
      Buffer.add_char buffer (Char.chr (0x80 lor ((value lsr 6) land 0x3f)));
      Buffer.add_char buffer (Char.chr (0x80 lor (value land 0x3f))))
  in
  let string_value () =
    expect '"';
    let buffer = Buffer.create 32 in
    let rec loop () =
      match take () with
      | '"' -> Buffer.contents buffer
      | '\\' ->
          (match take () with
           | '"' -> Buffer.add_char buffer '"'
           | '\\' -> Buffer.add_char buffer '\\'
           | '/' -> Buffer.add_char buffer '/'
           | 'b' -> Buffer.add_char buffer '\b'
           | 'f' -> Buffer.add_char buffer '\012'
           | 'n' -> Buffer.add_char buffer '\n'
           | 'r' -> Buffer.add_char buffer '\r'
           | 't' -> Buffer.add_char buffer '\t'
           | 'u' ->
               let value = ref 0 in
               for _ = 1 to 4 do
                 value := (!value * 16) + hex_value (take ())
               done;
               add_codepoint buffer !value
           | _ -> fail "invalid JSON escape");
          loop ()
      | character ->
          if Char.code character < 32 then fail "unescaped control byte";
          Buffer.add_char buffer character;
          loop ()
    in
    loop ()
  in
  let number () =
    let start = !position in
    (match peek () with Some '-' -> incr position | _ -> ());
    (match peek () with
     | Some '0' -> incr position
     | Some ('1' .. '9') ->
         incr position;
         while
           match peek () with Some ('0' .. '9') -> true | _ -> false
         do
           incr position
         done
     | _ -> fail "invalid JSON integer");
    let value = String.sub input start (!position - start) in
    match int_of_string_opt value with
    | Some integer -> Num integer
    | None -> fail "JSON integer outside host range"
  in
  let rec value () =
    white ();
    let result =
      match peek () with
      | Some 'n' -> literal "null" Null
      | Some 't' -> literal "true" (Bool true)
      | Some 'f' -> literal "false" (Bool false)
      | Some '"' -> Str (string_value ())
      | Some '[' -> array ()
      | Some '{' -> object_value ()
      | Some ('-' | '0' .. '9') -> number ()
      | _ -> fail "invalid JSON value"
    in
    white ();
    result
  and array () =
    expect '[';
    white ();
    if peek () = Some ']' then (incr position; Arr [])
    else
      let rec items accumulated =
        let item = value () in
        match take () with
        | ']' -> Arr (List.rev (item :: accumulated))
        | ',' -> items (item :: accumulated)
        | _ -> fail "invalid JSON array delimiter"
      in
      items []
  and object_value () =
    expect '{';
    white ();
    if peek () = Some '}' then (incr position; Obj [])
    else
      let rec pairs accumulated =
        white ();
        let key = string_value () in
        white ();
        expect ':';
        let item = value () in
        if List.mem_assoc key accumulated then fail "duplicate JSON object key";
        match take () with
        | '}' -> Obj (List.rev ((key, item) :: accumulated))
        | ',' -> pairs ((key, item) :: accumulated)
        | _ -> fail "invalid JSON object delimiter"
      in
      pairs []
  in
  try
    let result = value () in
    if !position <> length then Error "trailing JSON bytes" else Ok result
  with
  | Syntax message -> Error message
  | Stack_overflow -> Error "JSON nesting exceeds process stack"

let encode value =
  let buffer = Buffer.create 512 in
  let add = Buffer.add_string buffer in
  let encode_string text =
    Buffer.add_char buffer '"';
    String.iter
      (fun character ->
        match character with
        | '"' -> add "\\\""
        | '\\' -> add "\\\\"
        | '\b' -> add "\\b"
        | '\012' -> add "\\f"
        | '\n' -> add "\\n"
        | '\r' -> add "\\r"
        | '\t' -> add "\\t"
        | c when Char.code c < 32 -> add (Printf.sprintf "\\u%04x" (Char.code c))
        | c -> Buffer.add_char buffer c)
      text;
    Buffer.add_char buffer '"'
  in
  let rec emit = function
    | Null -> add "null"
    | Bool true -> add "true"
    | Bool false -> add "false"
    | Num integer -> add (string_of_int integer)
    | Str text -> encode_string text
    | Arr items ->
        Buffer.add_char buffer '[';
        List.iteri
          (fun index item ->
            if index > 0 then Buffer.add_char buffer ',';
            emit item)
          items;
        Buffer.add_char buffer ']'
    | Obj pairs ->
        Buffer.add_char buffer '{';
        List.iteri
          (fun index (key, item) ->
            if index > 0 then Buffer.add_char buffer ',';
            encode_string key;
            Buffer.add_char buffer ':';
            emit item)
          (List.sort (fun (left, _) (right, _) -> String.compare left right) pairs);
        Buffer.add_char buffer '}'
  in
  emit value;
  Buffer.contents buffer

let field key = function
  | Obj pairs ->
      (match List.assoc_opt key pairs with
       | Some item -> Ok item
       | None -> Error ("missing field " ^ key))
  | _ -> Error "expected object"
