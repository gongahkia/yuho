#lang racket

(require xml
         net/url
         file/resolve
         (prefix-in xml: xml)
         (prefix-in web: web))

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
  (define (find-struct-by-name name)
    (for/or ([element (in-list parsed-xml)])
      (when (and (list? element)
                  (string=? (first element) 'struct))
        (let ([struct-name (second element)]
              [fields (third element)])
          (when (string=? name struct-name)
            fields)))))

  (define (extract-nested-fields fields)
    (for/list ([field (in-list fields)])
      (when (string-contains? (second field) "struct")
        (let ([nested-type (second field)])
          (list (first field) nested-type (find-struct-by-name nested-type))))))

  (define (generate-struct-nodes fields)
    (apply string-append
           (for/list ([field (in-list fields)])
             (let ([field-name (first field)]
                   [field-type (second field)])
               (if (string-contains? field-type "struct")
                   (string-append
                    (format "    ~a\n" field-name)
                    (generate-struct-nodes (find-struct-by-name field-type)))
                   (format "        ~a: ~a\n" field-name field-type)))))

  (define (extract-all-fields struct-name)
    (let ([fields (find-struct-by-name struct-name)])
      (generate-struct-nodes fields)))

  (extract-all-fields struct-name))

  (define (yuho-to-flowchart yuho-code)
    (let ([structs (extract-structs yuho-code)])
      (convert-to-flowchart structs)))

  (define (yuho-to-mermaid yuho-code)
    (let ([structs (extract-structs yuho-code)])
      (convert-to-mermaid structs)))

  (define (read-yuho-file file-path)
    (file->string file-path))

  (define (write-to-file content file-path)
    (call-with-output-file file-path
      (lambda (out)
        (fprintf out "~a" content))))

  (define (generate-diagram yuho-file output-file format)
    (let ([content (read-yuho-file yuho-file)])
      (cond
        [(equal? format 'flowchart)
         (write-to-file (yuho-to-flowchart content) output-file)]
        [(equal? format 'mermaid)
         (write-to-file (yuho-to-mermaid content) output-file)]
        [else
         (error "Unknown format")])))
  
  (define (open-in-browser file-path)
    (let ([url (format "file://~a" (file->absolute-path file-path))])
      (web:open-url url)))

  (define (main yuho-file output-file format)
    (generate-diagram yuho-file output-file format)
    (open-in-browser output-file))

  (main (car (current-command-line-arguments))
        (cadr (current-command-line-arguments))
        (case (string->symbol (caddr (current-command-line-arguments)))
          [(flowchart) 'flowchart]
          [(mermaid) 'mermaid]
          [else (error "Unknown format")]))
