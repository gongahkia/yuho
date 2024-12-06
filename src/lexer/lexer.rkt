#lang racket

(require token ast)

(define tokens
    (list
    (list 'TRUE_LITERAL #rx"TRUE")
    (list 'FALSE_LITERAL #rx"FALSE")
    (list 'MATCH #rx"match")
    (list 'CASE #rx"case")
    (list 'CONSEQUENCE #rx"consequence")
    (list 'PASS #rx"pass")
    (list 'STRUCT #rx"struct")
    (list 'FN #rx"fn")
    (list 'PERCENT #rx"%")
    (list 'MONEY_PREFIX #rx"\\$")
    (list 'DAY #rx"day")
    (list 'MONTH #rx"month")
    (list 'YEAR #rx"year")
    (list 'DURATION_UNITS #rx"(day|month|year)")

    (list 'STRING #rx"\"[^\"]*\"")
    (list 'INTEGER #rx"[0-9]+")
    (list 'FLOAT #rx"[0-9]+\\.[0-9]*")
    (list 'PERCENTAGE #rx"[0-9]+%")
    (list 'MONEY #rx"\\$[0-9]+(,[0-9]{3})*(\\.[0-9]{2})?")
    (list 'DATE #rx"[0-9]{2}-[0-9]{2}-[0-9]{4}")
    (list 'DURATION #rx"[0-9]+(day|month|year)(,[0-9]+(day|month|year))*")

    (list 'ID #rx"[a-zA-Z_][a-zA-Z_0-9]*")
    (list 'DOT #rx"\\.")
    (list 'PLUS #rx"\\+")
    (list 'MINUS #rx"-")
    (list 'MULT #rx"\\*")
    (list 'DIV #rx"/")
    (list 'ASSIGN #rx":=")
    (list 'EQUAL #rx"==")
    (list 'NOTEQUAL #rx"!=")
    (list 'GT #rx">")
    (list 'LT #rx"<")
    (list 'AND #rx"&&")
    (list 'OR #rx"\\|\\|")
    (list 'SEMICOLON #rx";")
    (list 'COLON #rx":")
    (list 'LBRACE #rx"\\{")
    (list 'RBRACE #rx"\\}")
    (list 'LPAREN #rx"\\(")
    (list 'RPAREN #rx"\\)")
    (list 'COMMA #rx",")
    (list 'UNDERSCORE #rx"_")
    (list 'WS #rx"[ \t\r\n]+" (lambda (_) 'ignore)))

(define (tokenize input)
    (define (tokenize-aux input)
        (cond
        [(null? input) '()]
        [else
        (define token (find-token (first input)))
        (if token
            (cons token (tokenize-aux (rest input)))
            (tokenize-aux (rest input)))]))

    (define (find-token str)
        (define (check-tokens tokens)
        (cond
            [(null? tokens) #f]
            [(regexp-match? (cadr (first tokens)) str)
            (list (car (first tokens)) str)]
            [else (check-tokens (rest tokens))]))

    (tokenize-aux (string-split input #px"\\s+")))