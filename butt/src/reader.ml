open Token

type tree = Leaf of Token.t | Group of group

and group = {
  delim : Token.delim;
  open_tok : Token.t;
  close_tok : Token.t;
  children : tree list;
  env : Grammar_env.t;
  span : Span.t;
}

type t = { trees : tree list; eof : Token.t; env : Grammar_env.t }
type input_error = Missing_eof | Eof_not_last of { index : int }
type error = Unbalanced of Diagnostic.t | Invalid_input of input_error

let describe_input_error = function
  | Missing_eof -> "token array does not end with an Eof token"
  | Eof_not_last { index } ->
      Printf.sprintf "Eof token at index %d is not the last token" index

type frame = { f_open : Token.t; f_delim : delim; f_children : tree list }

let unbalanced ?notes (tok : Token.t) msg =
  Error (Unbalanced (Diagnostic.make ?notes Diagnostic.Lex_unbalanced tok.span msg))

let check_input tokens =
  let len = Array.length tokens in
  let rec go i =
    if i >= len - 1 then
      match tokens.(len - 1).kind with Eof -> Ok () | _ -> Error Missing_eof
    else match tokens.(i).kind with Eof -> Error (Eof_not_last { index = i }) | _ -> go (i + 1)
  in
  if len = 0 then Error Missing_eof else go 0

let read_checked tokens =
  let env = Grammar_env.source in
  let push child stack top =
    match stack with
    | [] -> (stack, child :: top)
    | f :: rest -> ({ f with f_children = child :: f.f_children } :: rest, top)
  in
  let rec go i stack top =
    let tok = tokens.(i) in
    match tok.kind with
    | Open d -> go (i + 1) ({ f_open = tok; f_delim = d; f_children = [] } :: stack) top
    | Close d -> (
        match stack with
        | [] ->
            unbalanced tok
              (Printf.sprintf "unmatched closing delimiter `%c`" (close_char d))
        | f :: rest when f.f_delim = d ->
            let g =
              Group
                {
                  delim = d;
                  open_tok = f.f_open;
                  close_tok = tok;
                  children = List.rev f.f_children;
                  env;
                  span =
                    Span.make ~file:f.f_open.span.file ~start:f.f_open.span.start
                      ~stop:tok.span.stop;
                }
            in
            let stack, top = push g rest top in
            go (i + 1) stack top
        | f :: _ ->
            unbalanced tok
              ~notes:
                [
                  Diagnostic.note f.f_open.span
                    (Printf.sprintf "`%c` opened here" (open_char f.f_delim));
                ]
              (Printf.sprintf
                 "mismatched closing delimiter `%c`: expected `%c` to close `%c`"
                 (close_char d) (close_char f.f_delim) (open_char f.f_delim)))
    | Eof -> (
        match stack with
        | [] -> Ok { trees = List.rev top; eof = tok; env }
        | f :: _ ->
            unbalanced f.f_open
              ~notes:[ Diagnostic.note tok.span "end of input reached here" ]
              (Printf.sprintf "unclosed delimiter `%c`" (open_char f.f_delim)))
    | Ident | Raw_ident _ | Int _ | Float _ | String | Op | Punct | Raw_region _
      ->
        let stack, top = push (Leaf tok) stack top in
        go (i + 1) stack top
  in
  go 0 [] []

let read tokens =
  match check_input tokens with
  | Error e -> Error (Invalid_input e)
  | Ok () -> read_checked tokens
