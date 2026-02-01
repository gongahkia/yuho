all: install

# Yuho v4.0 (Python) commands
install:
	@echo "Installing Yuho v4.0 (Python)..."
	@pip install -r requirements.txt
	@pip install -e .

test:
	@echo "Running Yuho v4.0 tests..."
	@python3 -m pytest yuho_v4/tests/ -v

check-example:
	@echo "Checking example files..."
	@python3 yuho_v4/cli/main.py check example/cheating/cheating_illustration_A.yh

repl:
	@echo "Starting Yuho REPL..."
	@python3 yuho_v4/repl.py

# Legacy Rust/Racket commands (require installation)
build-legacy: src/main.rs
	@echo "Building legacy Rust version (requires Rust)..."
	@rustup update
	@cargo build --release
	@cargo run

debug-legacy: src/main.rs
	@echo "Debug mode for legacy version..."
	@cargo run

config:

	@sudo apt update && sudo apt upgrade && sudo apt autoremove

	# for Rust
	@curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
	@source $HOME/.cargo/env
	@rustup update

	# for Haskell
	@curl -sSL https://get.haskellstack.org/ | sh
	@stack upgrade
	@stack setup

	# for OCaml and ML
	@sudo apt install -y ocaml opam
	@opam init -y --disable-sandboxing
	@eval $(opam env)
	@opam switch create 4.14.0
	@eval $(opam env)

	# for Yacc
	@sudo apt install -y bison flex

	# for Alloy
	@sudo apt install -y default-jre
	@wget https://github.com/AlloyTools/org.alloytools.alloy/releases/download/v6.0.0/alloy6.jar -O /usr/local/bin/alloy6.jar

	# for F*
	@git clone --depth 1 https://github.com/FStarLang/FStar.git
	@cd FStar && make -C src/ocaml-output

	# for EBNF 
	@curl -O https://www.antlr.org/download/antlr-4.9.2-complete.jar
	@sudo mv antlr-4.9.2-complete.jar /usr/local/lib/

lang:lsp/base
	@cd lsp/base && chmod +x start-lsp.sh
	@./start-lsp.sh

clean:
	@rm -rf .git .gitignore README.md

up:
	@git pull
	@git status

history:
	@git log
