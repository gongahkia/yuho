let valid_utf8 text =
  let length = String.length text in
  let byte index = Char.code text.[index] in
  let continuation index =
    index < length && byte index land 0xc0 = 0x80
  in
  let bounded index lower upper =
    index < length && byte index >= lower && byte index <= upper
  in
  let rec scan index =
    if index = length then true
    else
      let first = byte index in
      if first < 0x80 then scan (index + 1)
      else if first >= 0xc2 && first <= 0xdf
      then continuation (index + 1) && scan (index + 2)
      else if first = 0xe0
      then bounded (index + 1) 0xa0 0xbf
           && continuation (index + 2) && scan (index + 3)
      else if (first >= 0xe1 && first <= 0xec)
              || (first >= 0xee && first <= 0xef)
      then continuation (index + 1) && continuation (index + 2)
           && scan (index + 3)
      else if first = 0xed
      then bounded (index + 1) 0x80 0x9f
           && continuation (index + 2) && scan (index + 3)
      else if first = 0xf0
      then bounded (index + 1) 0x90 0xbf
           && continuation (index + 2) && continuation (index + 3)
           && scan (index + 4)
      else if first >= 0xf1 && first <= 0xf3
      then continuation (index + 1) && continuation (index + 2)
           && continuation (index + 3) && scan (index + 4)
      else if first = 0xf4
      then bounded (index + 1) 0x80 0x8f
           && continuation (index + 2) && continuation (index + 3)
           && scan (index + 4)
      else false
  in
  scan 0

let rec loop () =
  match input_line stdin with
  | line ->
      let response =
        if not (valid_utf8 line) then Kernel.decode_failure "invalid UTF-8"
        else
          match Json.parse line with
          | Ok request -> Kernel.run request
          | Error message -> Kernel.decode_failure message
      in
      print_endline (Json.encode response);
      flush stdout;
      loop ()
  | exception End_of_file -> ()

let () = loop ()
