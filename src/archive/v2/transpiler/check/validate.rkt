#lang racket
(require racket/file)

(define COLOR-CYAN "\033[96m")
(define COLOR-GREEN "\033[92m")
(define COLOR-RED "\033[91m")
(define COLOR-RESET "\033[0m")

(define (read-json file-path)
  (with-input-from-file file-path
    (λ () (read-json))))

;; this isn't used currently so the racket/json library does not need to be included
;; anyway it's given issues currently lol

(define (validate-json-files dep-json-dir out-json-dir)
  (printf "~a~a~a~n" COLOR-CYAN "~ JSON FILES ~" COLOR-RESET)
  (define dep-json-files
    (set (filter (λ (f) (string-suffix? ".json" (path->string f)))
                 (directory-list dep-json-dir))))
  (define out-json-files
    (set (filter (λ (f) (string-suffix? ".json" (path->string f)))
                 (directory-list out-json-dir))))
  (for-each (λ (file-name)
              (define dep-file-path (build-path dep-json-dir file-name))
              (if (set-member? out-json-files file-name)
                  (let ([out-file-path (build-path out-json-dir file-name)])
                    (with-handlers ([exn:fail:read? (λ (_) (printf "~a: ~aError in JSON format~a~n" file-name COLOR-RED COLOR-RESET))]
                                    [exn? (λ (e) (printf "~a: ~aError - ~a~a~n" file-name COLOR-RED (exn-message e) COLOR-RESET))])
                      (let ([dep-data (read-json dep-file-path)]
                            [out-data (read-json out-file-path)])
                        (if (equal? dep-data out-data)
                            (printf "~a: ~aMatch~a~n" file-name COLOR-GREEN COLOR-RESET)
                            (printf "~a: ~aMismatch~a~n" file-name COLOR-RED COLOR-RESET)))))
                  (printf "~a: ~aFile not found in output directory~a~n" file-name COLOR-RED COLOR-RESET)))
            (set->list dep-json-files))
  (for-each (λ (file-name)
              (unless (set-member? dep-json-files file-name)
                (printf "~a: ~aFile not found in dependency directory~a~n" file-name COLOR-RED COLOR-RESET)))
            (set->list out-json-files)))

(define (validate-mmd-files dep-mmd-dir out-mmd-dir)
  (printf "~a~a~a~n" COLOR-CYAN "~ MMD FILES ~" COLOR-RESET)
  (define dep-mmd-files
    (set (filter (λ (f) (string-suffix? ".mmd" (path->string f)))
                 (directory-list dep-mmd-dir))))
  (define out-mmd-files
    (set (filter (λ (f) (string-suffix? ".mmd" (path->string f)))
                 (directory-list out-mmd-dir))))
  (for-each (λ (file-name)
              (define dep-file-path (build-path dep-mmd-dir file-name))
              (if (set-member? out-mmd-files file-name)
                  (let ([out-file-path (build-path out-mmd-dir file-name)])
                    (if (= (file-size dep-file-path) (file-size out-file-path))
                        (printf "~a: ~aMatch~a~n" file-name COLOR-GREEN COLOR-RESET)
                        (printf "~a: ~aMismatch~a~n" file-name COLOR-RED COLOR-RESET)))
                  (printf "~a: ~aFile not found in output directory~a~n" file-name COLOR-RED COLOR-RESET)))
            (set->list dep-mmd-files))
  (for-each (λ (file-name)
              (unless (set-member? dep-mmd-files file-name)
                (printf "~a: ~aFile not found in dependency directory~a~n" file-name COLOR-RED COLOR-RESET)))
            (set->list out-mmd-files)))

(define (validate-html-files dep-html-dir out-html-dir)
  (printf "~a~a~a~n" COLOR-CYAN "~ HTML FILES ~" COLOR-RESET)
  (define dep-html-files
    (set (filter (λ (f) (string-suffix? ".html" (path->string f)))
                 (directory-list dep-html-dir))))
  (define out-html-files
    (set (filter (λ (f) (string-suffix? ".html" (path->string f)))
                 (directory-list out-html-dir))))
  (for-each (λ (file-name)
              (define dep-file-path (build-path dep-html-dir file-name))
              (if (set-member? out-html-files file-name)
                  (let ([out-file-path (build-path out-html-dir file-name)])
                    (with-handlers ([exn? (λ (e) (printf "~a: ~aError - ~a~a~n" file-name COLOR-RED (exn-message e) COLOR-RESET))])
                      (let ([dep-content (file->string dep-file-path)]
                            [out-content (file->string out-file-path)])
                        (if (string=? dep-content out-content)
                            (printf "~a: ~aMatch~a~n" file-name COLOR-GREEN COLOR-RESET)
                            (printf "~a: ~aMismatch~a~n" file-name COLOR-RED COLOR-RESET)))))
                  (printf "~a: ~aFile not found in output directory~a~n" file-name COLOR-RED COLOR-RESET)))
            (set->list dep-html-files))
  (for-each (λ (file-name)
              (unless (set-member? dep-html-files file-name)
                (printf "~a: ~aFile not found in dependency directory~a~n" file-name COLOR-RED COLOR-RESET)))
            (set->list out-html-files)))

;; ----- MAIN EXECUTION CODE -----

(let ([dep-mmd-dir-mindmap (build-path "check" "dep" "mmd_mindmap")]
      [out-mmd-dir-mindmap (build-path "check" "out" "mmd_mindmap")]
      [dep-mmd-dir-flowchart (build-path "check" "dep" "mmd_flowchart")]
      [out-mmd-dir-flowchart (build-path "check" "out" "mmd_flowchart")])
  (validate-mmd-files dep-mmd-dir-mindmap out-mmd-dir-mindmap)
  (validate-mmd-files dep-mmd-dir-flowchart out-mmd-dir-flowchart))
