OCAML_VERSION := 5.3.0
OCAMLOPT := ocamlopt
SOURCES := src/json.ml src/sha256.ml src/kernel.ml src/main.ml

.PHONY: all clean
all:
	@test "$$($(OCAMLOPT) -version)" = "$(OCAML_VERSION)" || { echo "requires OCaml $(OCAML_VERSION)" >&2; exit 1; }
	$(OCAMLOPT) -w +a-4-42-70 -warn-error +a-4-42-70 -O3 -I src -o yuho-kernel-ocaml $(SOURCES)

clean:
	rm -f src/*.cmi src/*.cmx src/*.o yuho-kernel-ocaml
