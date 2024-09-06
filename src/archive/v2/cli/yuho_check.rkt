#lang racket

(require parser-tools/lex
         parser-tools/yacc
         racket/file
         racket/format
         racket/cli
         racket/color)

(define (error-message msg)
  (displayln (format "~a ERROR: ~a" (color:red) msg))

(define (success-message msg)
  (displayln (format "~a ~a" (color:green) msg))

(define (reminder-message msg)
  (displayln (format "REMINDER: ~a" msg)))

(define-parser
  (grammar
    (start program)
    
    (rule
      [program (declarations EOF)
               (check-base-syntax declarations)
               (make-program declarations)]
    
      [declarations (declaration declarations)
                    (cons declaration declarations)]
      [declarations () '()]
    
      [declaration (type ID ASSIGN expression SEMICOLON)
                  (check-declaration type ID expression)
                  (make-declaration type ID expression)]
      [declaration (type ID SEMICOLON)
                  (check-declaration type ID #f)
                  (make-declaration type ID #f)]
    
      [type 'int (make-type 'int)]
      [type 'float (make-type 'float)]
      [type 'percent (make-type 'percent)]
      [type 'money (make-type 'money)]
      [type 'date (make-type 'date)]
      [type 'duration (make-type 'duration)]
      [type 'bool (make-type 'bool)]
      [type 'string (make-type 'string)]
      [type ID (make-type ID)]
    
      [expression (logical-expression) (make-expression logical-expression)]
    
      [logical-expression (relational-expression logical-operator relational-expression)
                          (make-logical-expression relational-expression logical-operator relational-expression)]
      [logical-expression (relational-expression)
                          (make-logical-expression relational-expression '() '())]
    
      [relational-expression (additive-expression relational-operator additive-expression)
                            (make-relational-expression additive-expression relational-operator additive-expression)]
      [relational-expression (additive-expression)
                            (make-relational-expression additive-expression '() '())]
    
      [additive-expression (multiplicative-expression additive-operator multiplicative-expression)
                          (make-additive-expression multiplicative-expression additive-operator multiplicative-expression)]
      [additive-expression (multiplicative-expression)
                          (make-additive-expression multiplicative-expression '() '())]
    
      [multiplicative-expression (primary-expression multiplicative-operator primary-expression)
                                  (make-multiplicative-expression primary-expression multiplicative-operator primary-expression)]
      [multiplicative-expression (primary-expression)
                                  (make-multiplicative-expression primary-expression '() '())]
    
      [primary-expression ID (make-primary-expression ID)]
      [primary-expression literal (make-primary-expression literal)]
      [primary-expression LPAREN expression RPAREN (make-primary-expression expression)]
    
      [literal STRING (make-literal (make-token 'STRING))]
      [literal INTEGER (make-literal (make-token 'INTEGER))]
      [literal FLOAT (make-literal (make-token 'FLOAT))]
      [literal PERCENTAGE (make-literal (make-token 'PERCENTAGE))]
      [literal MONEY (make-literal (make-token 'MONEY))]
      [literal DATE (make-literal (make-token 'DATE))]
      [literal DURATION (make-literal (make-token 'DURATION))]
      [literal TRUE_LITERAL (make-literal (make-token 'TRUE_LITERAL))]
      [literal FALSE_LITERAL (make-literal (make-token 'FALSE_LITERAL))]
    
      [statement declaration (make-statement declaration)]
      [statement assignment (make-statement assignment)]
      [statement function-call (make-statement function-call)]
      [statement match-case (make-statement match-case)]
      [statement pass-statement (make-statement pass-statement)]
    
      [assignment ID ASSIGN expression SEMICOLON (make-assignment ID expression)]
    
      [match-case MATCH LPAREN expression RPAREN LBRACE case-clause* RBRACE
                  (check-match-case expression case-clause)
                  (make-match-case expression case-clause)]
      [match-case MATCH LBRACE case-clause* RBRACE
                  (check-match-case #f case-clause)
                  (make-match-case #f case-clause)]
    
      [case-clause CASE expression ASSIGN CONSEQUENCE expression SEMICOLON
                    (make-case-clause expression expression)]
      [case-clause CASE UNDERSCORE ASSIGN CONSEQUENCE pass-statement SEMICOLON
                    (make-case-clause #f pass-statement)]
    
      [pass-statement PASS SEMICOLON (make-pass-statement)]
    
      [function-definition FN ID LPAREN parameter-list RPAREN COLON type LBRACE statement* RBRACE
                          (check-function-definition ID parameter-list type statement)
                          (make-function-definition ID parameter-list type statement)]
    
      [parameter-list (parameter parameter-list) (cons parameter parameter-list)]
      [parameter-list () '()]
    
      [parameter type ID (make-parameter type ID)]
    
      [function-call ID LPAREN argument-list RPAREN SEMICOLON
                      (make-function-call ID argument-list)]
    
      [argument-list (expression argument-list) (cons expression argument-list)]
      [argument-list () '()]
    
      [struct-definition STRUCT ID LBRACE struct-member* RBRACE
                          (check-struct-definition ID struct-member)
                          (make-struct-definition ID struct-member)]
    
      [struct-member type ID (make-struct-member type ID)]
    
      [entry-point 'main LBRACE statement* RBRACE
                  (make-entry-point statement)]
    
      [EOF () '()]
    
      [error (make-error "Syntax error")])
    
  (lexer
    (start program)
    (ignore
      [WS '()]
      [COMMENT '()]
      [MULTILINE_COMMENT '()])
    
    [TRUE_LITERAL (make-token 'TRUE_LITERAL)]
    [FALSE_LITERAL (make-token 'FALSE_LITERAL)]
    [MATCH (make-token 'MATCH)]
    [CASE (make-token 'CASE)]
    [CONSEQUENCE (make-token 'CONSEQUENCE)]
    [PASS (make-token 'PASS)]
    [STRUCT (make-token 'STRUCT)]
    [FN (make-token 'FN)]
    [PERCENT (make-token 'PERCENT)]
    [MONEY_PREFIX (make-token 'MONEY_PREFIX)]
    [DAY (make-token 'DAY)]
    [MONTH (make-token 'MONTH)]
    [YEAR (make-token 'YEAR)]
    [ID (make-token 'ID)]
    [STRING (make-token 'STRING')]
    [INTEGER (make-token 'INTEGER')]
    [FLOAT (make-token 'FLOAT')]
    [PERCENTAGE (make-token 'PERCENTAGE')]
    [MONEY (make-token 'MONEY')]
    [DATE (make-token 'DATE')]
    [DURATION (make-token 'DURATION')]
    [PLUS (make-token 'PLUS')]
    [MINUS (make-token 'MINUS')]
    [MULT (make-token 'MULT')]
    [DIV (make-token 'DIV')]
    [ASSIGN (make-token 'ASSIGN')]
    [EQUAL (make-token 'EQUAL')]
    [NOTEQUAL (make-token 'NOTEQUAL')]
    [GT (make-token 'GT')]
    [LT (make-token 'LT')]
    [AND (make-token 'AND')]
    [OR (make-token 'OR')]
    [SEMICOLON (make-token 'SEMICOLON')]
    [COLON (make-token 'COLON')]
    [LBRACE (make-token 'LBRACE')]
    [RBRACE (make-token 'RBRACE')]
    [LPAREN (make-token 'LPAREN')]
    [RPAREN (make-token 'RPAREN')]
    [COMMA (make-token 'COMMA')]
    [UNDERSCORE (make-token 'UNDERSCORE')]
    [error (make-error "Lexical error")]))


(define (check-base-syntax ast)
  (for ([node ast])
    (match node
      [(declaration _ _ (some expr))
       (when (not (valid-expression? expr))
         (error-message "Invalid expression in declaration."))]
      [(function-definition _ _ _ statements)
       (for ([stmt statements])
         (when (not (valid-statement? stmt))
           (error-message "Invalid statement in function definition.")))]
      [(match-case _ clauses)
       (for ([clause clauses])
         (when (not (valid-case-clause? clause))
           (error-message "Invalid case clause in match-case.")))]
      [(struct-definition _ members)
       (for ([member members])
         (when (not (valid-struct-member? member))
           (error-message "Invalid struct member.")))])))  

(define (valid-declaration? id)
  (symbol? id))

(define (valid-struct-definition? id members)
  (and (symbol? id) (every struct-member-valid? members)))

(define (struct-member-valid? member)
  (match member
    [(struct-member type id) (and (symbol? type) (symbol? id))]
    [_ #f]))

(define (check-declaration type id expression)
  (unless (valid-type? type)
    (error-message (format "Invalid type: ~a" type)))
  (unless (or (not expression) (valid-expression? expression))
    (error-message (format "Invalid expression for declaration: ~a" id))))

(define (valid-type? type)
  (member type '(int float percent money date duration bool string)))

(define (valid-expression? expr)
  (match expr
    [(literal _) #t]
    [(primary-expression _) #t]
    [(additive-expression _ _ _ ) #t]
    [(multiplicative-expression _ _ _ ) #t]
    [(relational-expression _ _ _ ) #t]
    [(logical-expression _ _ _ ) #t]
    [_ #f]))

(define (check-function-definition id parameters return-type statements)
  (unless (valid-id? id)
    (error-message (format "Invalid function ID: ~a" id)))
  (unless (every parameter-valid? parameters)
    (error-message (format "Invalid parameter in function: ~a" id)))
  (unless (valid-type? return-type)
    (error-message (format "Invalid return type in function: ~a" id)))
  (unless (every valid-statement? statements)
    (error-message (format "Invalid statement in function: ~a" id))))

(define (valid-id? id)
  (symbol? id))

(define (parameter-valid? param)
  (match param
    [(parameter type id) (and (valid-type? type) (valid-id? id))]
    [_ #f]))

(define (valid-statement? stmt)
  (match stmt
    [(declaration _ _ _) #t]
    [(assignment _ _) #t]
    [(function-call _ _) #t]
    [(match-case _ _) #t]
    [(pass-statement) #t]
    [_ #f]))

(define (check-struct-definition id members)
  (unless (valid-struct-definition? id members)
    (error-message (format "Invalid struct definition: ~a" id))
    (for ([member members])
      (match member
        [(struct-member type id)
         (unless (valid-type? type)
           (error-message (format "Invalid type in struct member: ~a" type)))]))))

(define (check-match-case expression case-clauses)
  (unless (valid-match-case-syntax? case-clauses)
    (error-message "Invalid match-case syntax"))
  (when (and expression (not (valid-expression? expression)))
    (error-message "Invalid expression in match-case"))
  (for ([case-clause case-clauses])
    (match case-clause
      [(case-clause (list literal) _)
       (unless (valid-enum-literal? (car (case-clause-predicate case-clause)))
         (error-message "Invalid ENUM literal in case-clause"))]
      [(case-clause _ pass-statement)
       (unless (valid-pass-statement? pass-statement)
         (error-message "Invalid pass-statement in case-clause"))]
      [_ #f]))
  '())

(define (valid-match-case-syntax? case-clauses)
  (not (null? case-clauses)))

(define (valid-enum-literal? literal)
  (match literal
    [(literal value) (symbol? value)]
    [_ #f]))

(define (valid-pass-statement? pass-statement)
  (match pass-statement
    [(pass-statement) #t]
    [_ #f]))

(define (check-declaration-errors type id expression)
  (when (not (valid-type? type))
    (error-message (format "Invalid type in declaration: ~a" type)))
  (when (and expression (not (valid-expression? expression)))
    (error-message "Invalid expression in declaration.")))

(define (check-function-definition-errors id parameters return-type statements)
  (when (not (valid-function-name? id))
    (error-message (format "Invalid function name: ~a" id)))
  (for ([param parameters])
    (when (not (valid-parameter? param))
      (error-message "Invalid parameter in function definition.")))
  (when (not (valid-type? return-type))
    (error-message (format "Invalid return type: ~a" return-type)))
  (for ([stmt statements])
    (when (not (valid-statement? stmt))
      (error-message "Invalid statement in function definition."))))

(define (check-struct-definition-reminders id members)
  (when (not (ends-with-na? members))
    (reminder-message (format "Struct ~a does not end with an 'NA' option." id)))
  (for ([member members])
    (when (and (struct-member-refers-to-undefined? member))
      (error-message (format "Struct ~a refers to undefined struct in member ~a." id member)))))

(define (check-match-case-reminders expression case-clauses)
  (for ([clause case-clauses])
    (match clause
      [(case-clause _ consequence)
       (when (not (valid-consequence? consequence))
         (error-message "Invalid consequence in case clause."))]
      [(case-clause _ pass-statement)
       (when (not (valid-pass-statement? pass-statement))
         (error-message "Invalid pass statement in case clause."))])))

(define (parse-file filename)
  (with-input-from-file filename
    (lambda ()
      (let ([input (port->string (current-input-port))])
        (let ([tokens (tokenize input)])
          (let ([parse-result (parse tokens)])
            (if (error? parse-result)
                (error-message "Failed to parse input")
                (begin
                  (displayln "Parsing successful")
                  (check-for-errors parse-result)
                  (check-for-reminders parse-result))))))))

(define (check-for-errors ast)
  (check-base-syntax ast)
  (for ([node ast])
    (match node
      [(declaration type id expression)
       (check-declaration-errors type id expression)]
      [(function-definition id parameters return-type statements)
       (check-function-definition-errors id parameters return-type statements)]
      [(match-case expression case-clauses)
       (check-match-case-reminders expression case-clauses)]
      [(struct-definition id members)
       (check-struct-definition-reminders id members)])))

(define (check-for-reminders ast)
  (for ([node ast])
    (match node
      [(struct-definition id members)
       (check-struct-definition-reminders id members)]
      [(match-case expression case-clauses)
       (check-match-case-reminders expression case-clauses)])))

(define (main args)
  (define (print-error-msg line)
    (displayln (format "~a Error hit! Go see Line ~a" (color:red) line))
    (exit 1))
  
  (define (print-success-msg)
    (displayln (format "~a Looks good! Have confidence your Yuho file is correct" (color:green)))
    (exit 0))
  
  (match (length args)
    [1
     (let ([filename (first args)])
       (parse-file filename)
       (print-success-msg))]
    [_ (displayln "Usage: <program> <filename>") (exit 1)]))

(main (command-line))
