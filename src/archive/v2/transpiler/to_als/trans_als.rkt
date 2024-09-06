#lang racket

(require xml)

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

;; ----- main execution code -----

;; (define alloy-code (read-yuho-file "example.yh"))
;; (display alloy-code))
