let disguising u =
  (u >= 0x80 && u <= 0x9F)
  || u = 0x061C || u = 0x200E || u = 0x200F
  || (u >= 0x202A && u <= 0x202E)
  || (u >= 0x2066 && u <= 0x2069)
  || u = 0x2028 || u = 0x2029 || u = 0xFEFF

let render ~quoted s =
  let b = Buffer.create (String.length s + 8) in
  let n = String.length s in
  let rec go i =
    if i < n then begin
      let c = String.unsafe_get s i in
      let code = Char.code c in
      if code < 0x80 then begin
        (match c with
        | '\\' when quoted -> Buffer.add_string b "\\\\"
        | '"' when quoted -> Buffer.add_string b "\\\""
        | '\n' when quoted -> Buffer.add_string b "\\n"
        | '\r' when quoted -> Buffer.add_string b "\\r"
        | '\t' when quoted -> Buffer.add_string b "\\t"
        | _ when code < 0x20 || code = 0x7F -> Printf.bprintf b "\\x%02X" code
        | _ -> Buffer.add_char b c);
        go (i + 1)
      end
      else
        let d = String.get_utf_8_uchar s i in
        let len = Uchar.utf_decode_length d in
        if not (Uchar.utf_decode_is_valid d) then begin
          Printf.bprintf b "\\x%02X" code;
          go (i + 1)
        end
        else
          let u = Uchar.to_int (Uchar.utf_decode_uchar d) in
          if disguising u then Printf.bprintf b "\\u{%04X}" u
          else Buffer.add_string b (String.sub s i len);
          go (i + len)
    end
  in
  go 0;
  Buffer.contents b

let quoted s = render ~quoted:true s
let display s = render ~quoted:false s
