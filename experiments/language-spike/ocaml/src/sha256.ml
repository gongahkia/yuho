let constants =
  [|
    0x428a2f98l; 0x71374491l; 0xb5c0fbcfl; 0xe9b5dba5l;
    0x3956c25bl; 0x59f111f1l; 0x923f82a4l; 0xab1c5ed5l;
    0xd807aa98l; 0x12835b01l; 0x243185bel; 0x550c7dc3l;
    0x72be5d74l; 0x80deb1fel; 0x9bdc06a7l; 0xc19bf174l;
    0xe49b69c1l; 0xefbe4786l; 0x0fc19dc6l; 0x240ca1ccl;
    0x2de92c6fl; 0x4a7484aal; 0x5cb0a9dcl; 0x76f988dal;
    0x983e5152l; 0xa831c66dl; 0xb00327c8l; 0xbf597fc7l;
    0xc6e00bf3l; 0xd5a79147l; 0x06ca6351l; 0x14292967l;
    0x27b70a85l; 0x2e1b2138l; 0x4d2c6dfcl; 0x53380d13l;
    0x650a7354l; 0x766a0abbl; 0x81c2c92el; 0x92722c85l;
    0xa2bfe8a1l; 0xa81a664bl; 0xc24b8b70l; 0xc76c51a3l;
    0xd192e819l; 0xd6990624l; 0xf40e3585l; 0x106aa070l;
    0x19a4c116l; 0x1e376c08l; 0x2748774cl; 0x34b0bcb5l;
    0x391c0cb3l; 0x4ed8aa4al; 0x5b9cca4fl; 0x682e6ff3l;
    0x748f82eel; 0x78a5636fl; 0x84c87814l; 0x8cc70208l;
    0x90befffal; 0xa4506cebl; 0xbef9a3f7l; 0xc67178f2l;
  |]

let initial =
  [|
    0x6a09e667l; 0xbb67ae85l; 0x3c6ef372l; 0xa54ff53al;
    0x510e527fl; 0x9b05688cl; 0x1f83d9abl; 0x5be0cd19l;
  |]

let add = Int32.add
let xor = Int32.logxor
let and_ = Int32.logand
let not_ = Int32.lognot

let rotate_right value shift =
  Int32.logor
    (Int32.shift_right_logical value shift)
    (Int32.shift_left value (32 - shift))

let small0 value =
  xor (xor (rotate_right value 7) (rotate_right value 18))
    (Int32.shift_right_logical value 3)

let small1 value =
  xor (xor (rotate_right value 17) (rotate_right value 19))
    (Int32.shift_right_logical value 10)

let big0 value =
  xor (xor (rotate_right value 2) (rotate_right value 13))
    (rotate_right value 22)

let big1 value =
  xor (xor (rotate_right value 6) (rotate_right value 11))
    (rotate_right value 25)

let padded source =
  let length = String.length source in
  let zeros = (56 - ((length + 1) mod 64) + 64) mod 64 in
  let total = length + 1 + zeros + 8 in
  let bytes = Bytes.make total '\000' in
  Bytes.blit_string source 0 bytes 0 length;
  Bytes.set bytes length '\128';
  let bits = Int64.mul (Int64.of_int length) 8L in
  for index = 0 to 7 do
    let value =
      Int64.to_int
        (Int64.logand (Int64.shift_right_logical bits ((7 - index) * 8)) 0xffL)
    in
    Bytes.set bytes (total - 8 + index) (Char.chr value)
  done;
  bytes

let sha256 source =
  let data = padded source in
  let state = Array.copy initial in
  let words = Array.make 64 0l in
  let byte index = Char.code (Bytes.get data index) in
  for block = 0 to (Bytes.length data / 64) - 1 do
    let offset = block * 64 in
    for index = 0 to 15 do
      let base = offset + (index * 4) in
      let value = ref 0l in
      for part = 0 to 3 do
        value :=
          Int32.logor (Int32.shift_left !value 8)
            (Int32.of_int (byte (base + part)))
      done;
      words.(index) <- !value
    done;
    for index = 16 to 63 do
      words.(index) <-
        add
          (add (small1 words.(index - 2)) words.(index - 7))
          (add (small0 words.(index - 15)) words.(index - 16))
    done;
    let a = ref state.(0) in
    let b = ref state.(1) in
    let c = ref state.(2) in
    let d = ref state.(3) in
    let e = ref state.(4) in
    let f = ref state.(5) in
    let g = ref state.(6) in
    let h = ref state.(7) in
    for index = 0 to 63 do
      let choice = xor (and_ !e !f) (and_ (not_ !e) !g) in
      let majority = xor (xor (and_ !a !b) (and_ !a !c)) (and_ !b !c) in
      let temp1 =
        add (add (add (add !h (big1 !e)) choice) constants.(index))
          words.(index)
      in
      let temp2 = add (big0 !a) majority in
      h := !g;
      g := !f;
      f := !e;
      e := add !d temp1;
      d := !c;
      c := !b;
      b := !a;
      a := add temp1 temp2
    done;
    state.(0) <- add state.(0) !a;
    state.(1) <- add state.(1) !b;
    state.(2) <- add state.(2) !c;
    state.(3) <- add state.(3) !d;
    state.(4) <- add state.(4) !e;
    state.(5) <- add state.(5) !f;
    state.(6) <- add state.(6) !g;
    state.(7) <- add state.(7) !h
  done;
  Array.to_list state
  |> List.map (Printf.sprintf "%08lx")
  |> String.concat ""
