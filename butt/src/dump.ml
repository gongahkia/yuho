open Token

let max_indent = 32
let escape = Escape.quoted

let position src offset =
  let line, col = Source.line_col src offset in
  Printf.sprintf "%d:%d" line col

let opt_span label = function
  | None -> ""
  | Some sp -> Printf.sprintf " %s=%s" label (Span.to_string sp)

let details = function
  | Int { hex; suffix } -> (if hex then " hex" else "") ^ opt_span "suffix" suffix
  | Float { suffix } -> opt_span "suffix" suffix
  | Raw_ident { name } -> " name=" ^ Span.to_string name
  | Raw_region { tag; form; content } ->
      Printf.sprintf " tag=%s form=%s content=%s" (Span.to_string tag)
        (match form with
        | Brace_form -> "brace"
        | Long_form n -> Printf.sprintf "long/%d" n)
        (Span.to_string content)
  | Ident | String | Op | Punct | Open _ | Close _ | Eof -> ""

let token_line src tok =
  Printf.sprintf "%s %s %s \"%s\"%s%s%s"
    (position src tok.span.start)
    (Span.to_string tok.span) (kind_name tok.kind) (escape tok.text)
    (details tok.kind)
    (if tok.space_before then " space" else "")
    (if tok.newline_before then " newline" else "")

let trivia_line tv =
  Printf.sprintf "  trivia %s %s \"%s\""
    (match tv.trivia_kind with
    | Whitespace -> "whitespace"
    | Line_comment -> "line-comment"
    | Long_comment n -> Printf.sprintf "long-comment/%d" n)
    (Span.to_string tv.trivia_span)
    (escape tv.trivia_text)

let tokens ?(trivia = false) src toks =
  let b = Buffer.create 4096 in
  Printf.bprintf b "format tokens/2 file=%s\n" (escape (Source.name src));
  Array.iter
    (fun tok ->
      if trivia then
        List.iter
          (fun tv -> Printf.bprintf b "%s\n" (trivia_line tv))
          tok.leading_trivia;
      Printf.bprintf b "%s\n" (token_line src tok))
    toks;
  Buffer.contents b

type work = Enter of int * Reader.tree | Leave of int * Token.t

let trees src (r : Reader.t) =
  let b = Buffer.create 4096 in
  Printf.bprintf b "format trees/2 file=%s env=%s\n" (escape (Source.name src))
    (Grammar_env.to_string r.env);
  let line depth prefix tok =
    for _ = 1 to 2 * min depth max_indent do
      Buffer.add_char b ' '
    done;
    if depth > max_indent then Printf.bprintf b "depth=%d " depth;
    Printf.bprintf b "%s%s\n" prefix (token_line src tok)
  in
  let rec go = function
    | [] -> ()
    | Enter (d, Reader.Leaf tok) :: rest ->
        line d "" tok;
        go rest
    | Enter (d, Reader.Group g) :: rest ->
        line d ("group env=" ^ Grammar_env.to_string g.env ^ " ") g.open_tok;
        go
          (List.rev_append
             (List.rev_map (fun c -> Enter (d + 1, c)) g.children)
             (Leave (d, g.close_tok) :: rest))
    | Leave (d, tok) :: rest ->
        line d "end " tok;
        go rest
  in
  go (List.map (fun t -> Enter (0, t)) r.trees);
  line 0 "" r.eof;
  Buffer.contents b
