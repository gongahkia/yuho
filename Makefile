all:build

build:src/main.go
	@go mod tidy
	@go run src/main.go

debug:src/main.go
	@echo "debug mode"
	@go run src/main.go

config:
	@sudo apt upgrade && sudo apt update && sudo apt autoremove
	@sudo apt install golang
	@sudo apt install gcc
	@go mod init github.com/gongahkia/yuho

clean:
	@rm -rf .git .gitignore README.md

up:
	@git pull
	@git status

history:
	@git log
