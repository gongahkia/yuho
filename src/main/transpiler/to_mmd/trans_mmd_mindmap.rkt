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

  (define (convert-to-mermaid structs)
    (string-append
     "mindmap\n"
     (apply string-append
            (for/list ([struct (in-list structs)])
              (generate-struct-nodes (first struct) (second struct)))))

  (define (generate-struct-nodes name fields)
    (string-append
     (format "    ~a\n" name)
     (apply string-append
            (for/list ([field (in-list fields)])
              (let ([field-name (first field)]
                    [field-type (second field)])
                (if (string-contains? field-type "struct")
                    (generate-nested-struct field-name field-type)
                    (format "        ~a: ~a\n" field-name field-type)))))))

  (define (generate-nested-struct name type)
    (string-append
     (format "    ~a\n" name)
     (string-append
      (format "        %s\n" type)
      (generate-struct-nodes type (extract-subfields type)))))

  (define (extract-subfields struct-name)
    '())

  (define (yuho-to-mermaid yuho-code)
    (let ([structs (extract-structs yuho-code)])
      (convert-to-mermaid structs)))
)
