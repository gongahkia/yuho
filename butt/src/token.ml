type delim = Paren | Bracket | Brace
type raw_form = Brace_form | Long_form of int

type kind =
  | Ident
  | Raw_ident of { name : Span.t }
  | Int of { hex : bool; suffix : Span.t option }
  | Float of { suffix : Span.t option }
  | String
  | Op
  | Punct
  | Open of delim
  | Close of delim
  | Raw_region of { tag : Span.t; form : raw_form; content : Span.t }
  | Eof

type trivia_kind = Whitespace | Line_comment | Long_comment of int

type trivia = {
  trivia_kind : trivia_kind;
  trivia_span : Span.t;
  trivia_text : string;
}

type t = {
  kind : kind;
  text : string;
  span : Span.t;
  space_before : bool;
  newline_before : bool;
  leading_trivia : trivia list;
}

let kind_name = function
  | Ident -> "ident"
  | Raw_ident _ -> "raw-ident"
  | Int _ -> "int"
  | Float _ -> "float"
  | String -> "string"
  | Op -> "op"
  | Punct -> "punct"
  | Open _ -> "open"
  | Close _ -> "close"
  | Raw_region _ -> "raw-region"
  | Eof -> "eof"

let delim_name = function
  | Paren -> "paren"
  | Bracket -> "bracket"
  | Brace -> "brace"

let open_char = function Paren -> '(' | Bracket -> '[' | Brace -> '{'
let close_char = function Paren -> ')' | Bracket -> ']' | Brace -> '}'

let reconstruct tokens =
  let b = Buffer.create 4096 in
  Array.iter
    (fun tok ->
      List.iter (fun tv -> Buffer.add_string b tv.trivia_text) tok.leading_trivia;
      Buffer.add_string b tok.text)
    tokens;
  Buffer.contents b
