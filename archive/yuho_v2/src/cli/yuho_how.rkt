#lang racket

(require racket/file
         racket/port
         racket/system)

(define (print-help)
  (printf "\x1b[34mYuho is a Domain-Specific Language (DSL) designed for Criminal Law in Singapore.\x1b[0m\n\n")
  (printf "\x1b[32mCLI Commands:\x1b[0m\n")
  (printf "  \x1b[33m$ yuho -how\x1b[0m\n")
  (printf "    \x1b[36mProvides a guide on how to use Yuho.\x1b[0m\n\n")
  (printf "  \x1b[33m$ yuho -draft\x1b[0m\n")
  (printf "    \x1b[36mGenerates a Yuho struct file with base attributes.\x1b[0m\n\n")
  (printf "  \x1b[33m$ yuho -check <example_yuho_file.yh>\x1b[0m\n")
  (printf "    \x1b[36mValidates a Yuho file's syntax.\x1b[0m\n\n")
  (printf "  \x1b[33m$ yuho -approve <example_yuho_file.yh>\x1b[0m\n")
  (printf "    \x1b[36mGenerates an Alloy file from the given Yuho file and opens it in Alloy CLI.\x1b[0m\n\n")
  (printf "  \x1b[33m$ yuho -draw <example_yuho_file.yh>\x1b[0m\n")
  (printf "    \x1b[36mGenerates Mermaid Flowchart and Mindmap files from the given Yuho file and opens them in the local browser.\x1b[0m\n"))

(define (main args)
  (cond
    [(equal? (first args) "-how")
     (print-help)]
    [(equal? (first args) "-draft")
     (generate-yuho-draft)]
    [(equal? (first args) "-check")
     (when (and (pair? args) (> (length args) 1))
       (validate-yuho-file (second args)))]
    [(equal? (first args) "-approve")
     (when (and (pair? args) (> (length args) 1))
       (generate-alloy-file (second args)))]
    [(equal? (first args) "-draw")
     (when (and (pair? args) (> (length args) 1))
       (generate-draw-files (second args)))]
    [else
     (print-help)]))

(define (generate-yuho-draft)
  (printf "\x1b[32mGenerating a Yuho struct file with base attributes...\x1b[0m\n"))

(define (validate-yuho-file filename)
  (printf "\x1b[32mValidating Yuho file: ~a...\x1b[0m\n" filename))

(define (generate-alloy-file filename)
  (printf "\x1b[32mGenerating Alloy file from: ~a...\x1b[0m\n" filename))

(define (generate-draw-files filename)
  (printf "\x1b[32mGenerating Mermaid files from: ~a...\x1b[0m\n" filename))

(main (current-command-line-arguments))
