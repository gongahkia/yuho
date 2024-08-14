#lang racket

(require racket/file
         racket/string
         racket/format)

(define (to-snake-case str)
  (string-join (map string-downcase (string-split str #"[^a-zA-Z0-9]")) "_"))

(define (get-struct-name)
  (display "Enter the name for your struct: ")
  (flush-output)
  (let ([input (read-line)])
    (to-snake-case input)))

(define struct-name (get-struct-name))
(define file-name (format "~a.yh" struct-name))

(define template-content
  (format
   "scope s415~aDefinition {\n\n"
   struct-name
   "    struct Party { \n"
   "        Accused,\n"
   "        Victim,\n"
   "    }\n\n"
   "    struct AttributionType { \n"
   "        SoleInducment,\n"
   "        NotSoleInducement,\n"
   "        NA,\n"
   "    }\n\n"
   "    struct DeceptionType { \n"
   "        Fraudulently,\n"
   "        Dishonestly,\n"
   "        NA,\n"
   "    }\n\n"
   "    struct InducementType { \n"
   "        DeliverProperty,\n"
   "        ConsentRetainProperty,\n"
   "        DoOrOmit,\n"
   "        NA,\n"
   "    }\n\n"
   "    struct DamageHarmType { \n"
   "        Body,\n"
   "        Mind, \n"
   "        Reputation,\n"
   "        Property,\n"
   "        NA,\n"
   "    }\n\n"
   "    struct ConsequenceDefinition { \n"
   "        SaidToCheat,\n"
   "        NotSaidToCheat,\n"
   "    }\n\n"
   "    struct ~a { \n"
   "        string || Party accused,\n"
   "        string action,\n"
   "        string || Party victim,\n"
   "        AttributionType attribution,\n"
   "        DeceptionType deception,\n"
   "        InducementType inducement,\n"
   "        boolean causesDamageHarm,\n"
   "        {DamageHarmType} || DamageHarmType damageHarmResult, \n"
   "        ConsequenceDefinition definition,\n"
   "    }\n\n"
   "    ~a ~aDefinition := { \n\n"
   "    }\n\n"
   "}\n"
   struct-name
   struct-name))

(define (write-template-to-file)
  (call-with-output-file file-name
    (lambda (out)
      (fprintf out "~a" template-content))
    #:exists 'replace))

(define (main)
  (write-template-to-file)
  (displayln (format "File '~a' created with base struct template." file-name)))

(main)
