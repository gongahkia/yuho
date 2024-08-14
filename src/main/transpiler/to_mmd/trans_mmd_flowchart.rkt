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

  (define (convert-to-flowchart structs)
    (string-append
     "flowchart TD\n"
     (apply string-append
            (for/list ([struct (in-list structs)])
              (generate-struct-nodes (first struct) (second struct))))))

  (define (generate-struct-nodes name fields)
    (string-append
     (format "    ~a[~a]\n" name name)
     (apply string-append
            (for/list ([field (in-list fields)])
              (let ([field-name (first field)]
                    [field-type (second field)])
                (if (string-contains? field-type "struct")
                    (generate-nested-struct name field-name field-type)
                    (format "    ~a --> ~a: ~a\n" name field-name field-type))))))))

  (define (generate-nested-struct parent-name name type)
    (string-append
     (format "    ~a[~a]\n" name name)
     (format "    ~a --> ~a\n" parent-name name)
     (let ([nested-structs (extract-structs-for-type type)])
       (apply string-append
              (for/list ([nested-struct (in-list nested-structs)])
                (generate-struct-nodes (first nested-struct) (second nested-struct)))))))

  (define (extract-structs-for-type type)
    (define (find-struct-by-type name)
      (for/or ([element (in-list parsed-xml)])
        (when (and (list? element)
                    (string=? (first element) 'struct))
          (let ([struct-name (second element)]
                [fields (third element)])
            (when (string=? name struct-name)
              (map extract-field fields))))))

    (define (extract-all-nested-structs type)
      (let ([structs (find-struct-by-type type)])
        (map (lambda (field)
               (when (string-contains? (second field) "struct")
                 (let ([nested-type (second field)])
                   (list (symbol->string (string->symbol nested-type))
                         (find-struct-by-type nested-type)))))
             structs)))

    (extract-all-nested-structs type))

  (define (yuho-to-flowchart yuho-code)
    (let ([structs (extract-structs yuho-code)])
      (convert-to-flowchart structs)))

  (define (read-yuho-file file-path)
    (let ([yuho-code (file->string file-path)])
      (yuho-to-flowchart yuho-code)))

  (define (write-flowchart-to-file flowchart-code file-path)
    (call-with-output-file file-path
      (lambda (out)
        (fprintf out "~a" flowchart-code))))

  (define (generate-flowchart-for-file yuho-file output-file)
    (let ([flowchart-code (read-yuho-file yuho-file)])
      (write-flowchart-to-file flowchart-code output-file)))
