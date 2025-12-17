use yuho_core::lexer::{lex, Token};

#[test]
fn test_lex_money_literal() {
    let source = "$100.50";
    let tokens = lex(source);
    assert_eq!(tokens.len(), 1);
    assert!(matches!(tokens[0].0, Token::Money(_)));
}

#[test]
fn test_lex_money_with_currency() {
    let source = "money<SGD> amount := $500.00";
    let tokens = lex(source);

    // Should have: money, <, Ident(SGD), >, Ident(amount), :=, Money
    assert!(tokens.iter().any(|(t, _)| matches!(t, Token::TyMoney)));
    assert!(tokens.iter().any(|(t, _)| matches!(t, Token::Money(_))));
}

#[test]
fn test_lex_multiple_currencies() {
    let source = r#"
        money<USD> usd := $100
        money<EUR> eur := $200
        money<SGD> sgd := $300
    "#;
    let tokens = lex(source);

    let money_count = tokens
        .iter()
        .filter(|(t, _)| matches!(t, Token::Money(_)))
        .count();
    assert_eq!(money_count, 3);
}

#[test]
fn test_lex_negative_money() {
    let source = "-$50.00";
    let tokens = lex(source);

    // Should have minus and money
    assert!(tokens.iter().any(|(t, _)| matches!(t, Token::Minus)));
    assert!(tokens.iter().any(|(t, _)| matches!(t, Token::Money(_))));
}
