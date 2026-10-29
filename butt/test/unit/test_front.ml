let () =
  let h = Harness.create () in
  Suite_lexer.run h;
  Suite_reader.run h;
  Suite_oracle.run h;
  Suite_generated.run h;
  Printf.printf "%d checks passed, %d failed\n" h.passed h.failed;
  if h.failed > 0 then exit 1
