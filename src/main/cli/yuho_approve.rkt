#lang racket

(require xml
         racket/process
         racket/cmdline
         racket/file
         racket/list)

(define (parse-yuho-struct yuho-code)
  (define parsed-xml (xml->list (string->xml yuho-code)))
  
  (define (extract-structs xml)
    (for/list ([element (in-list xml)])
      (when (and (list? element)
                  (string=? (first element) 'struct))
        (let ([name (second element)]
              [fields (third element)])
          (list name (map extract-field fields))))))
  
  (define (extract-field field)
    (when (and (list? field)
                (string=? (first field) 'field))
      (let ([name (second field)]
            [type (third field)])
        (list name type))))

  (define (convert-to-alloy structs)
    (string-append
     "module dynamic_struct\n\n"
     (apply string-append
            (for/list ([struct (in-list structs)])
              (let ([name (first struct)]
                    [fields (second struct)])
                (string-append
                 (format "abstract sig ~a {\n" name)
                 (apply string-append
                        (for/list ([field (in-list fields)])
                          (string-append
                           (format "    ~a: one ~a\n" (first field) (second field)))))
                 "}\n\n"))))
  
  (define (yuho-to-alloy yuho-code)
    (let ([structs (extract-structs yuho-code)])
      (convert-to-alloy structs)))
  
  (define (read-yuho-file filename)
    (with-input-from-file filename
      (lambda ()
        (let ([content (port->string)])
          (yuho-to-alloy content)))))

(define (run-alloy-analysis alloy-code)
  (define alloy-file "generated.als")
  (define result-file "result.xml")

  (with-output-to-file alloy-file
    (lambda ()
      (display alloy-code)))
  
  (define alloy-command (format "alloy -o ~a ~a" result-file alloy-file))
  (define alloy-process (subprocess #f #f #f (string->path alloy-command)))

  (define (check-alloy-output)
    (if (file-exists? result-file)
        (begin
          (displayln "Alloy analysis complete. Checking results...")
          (with-input-from-file result-file
            (lambda ()
              (let ([result (port->string)])
                (cond
                  [(string-contains? result "satisfiable")
                   (displayln "Looks good! Have confidence your Yuho file is correct.")]
                  [(string-contains? result "unsatisfiable")
                   (displayln "Error hit! The Alloy model is unsatisfiable.")]
                  [else
                   (displayln "Unexpected result from Alloy analysis.")])))))
        (displayln "Alloy output file not found.")))

  (check-alloy-output)
  (delete-file alloy-file)
  (delete-file result-file))

(define (main args)
  (cond
    [(and (not (null? args)) (file-exists? (car args)))
     (let ([filename (car args)])
       (let ([yuho-code (read-yuho-file filename)])
         (run-alloy-analysis yuho-code)))]
    [else
     (displayln "Usage: racket script.rkt <filename.yh>")]))
  
(main (command-line))
