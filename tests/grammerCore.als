module YUHO_Test

open util/ordering[Time]
open util/boolean

// ----- ABSTRACT SYNTAX DEFINITION VIA SIGNATURES -----

abstract sig Keyword {}
one sig If, Else, ElseIf, For, Fn, StatuteSpec, Charge, Client, Party extends Keyword {}

sig Statute {}
sig Section, Subsection, StatuteBody, Damage, Punishment, PartyName, Identifier, Char, String, Digit, Integer, Float, Boolean {}
sig NonMonetaryDamage, MonetaryDamage extends Damage {}
sig Plaintiff, Defendant, ThirdParty, OtherParty extends Party {}
sig AssignmentOperator, MathematicalOperator, ComparisonOperator, Operator {}
sig Expression, GenericExpression, MathematicalExpression, Term, Factor, Statement, StatementBody, Comment, Program {}

// ----- CHECKS VIA ASSERTIONS -----

assert Keywords {
    If in Keyword and Else in Keyword and ElseIf in Keyword and For in Keyword and Fn in Keyword
    StatuteSpec in Keyword and Charge in Keyword and Client in Keyword and Party in Keyword
}

assert IdentifierDefinition {
    all id: Identifier | id in Char -> Char || Digit || "_"
}

assert StatementSyntax {
    all s: Statement | s in Identifier -> Expression or Keyword -> StatementBody
}

assert ExpressionSyntax {
    all e: Expression | e in GenericExpression || MathematicalExpression || Expression
}

assert ProgramSyntax {
    all p: Program | p in Statement || StatementBody
}

// ----- CHECKS -----

run Keywords, IdentifierDefinition, StatementSyntax, ExpressionSyntax, ProgramSyntax for 5 but 3 Int

assert IfIsKeyword {
    If in Keyword
}
