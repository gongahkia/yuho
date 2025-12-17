use yuho_core::lex;
use yuho_core::lexer::Token;

#[test]
fn test_lex_money_with_currency() {
    let source = "money<SGD> amt := $100.50";
    let tokens = lex(source);

    assert!(tokens.iter().any(|(t, _)| matches!(t, Token::TyMoney)));
    assert!(tokens.iter().any(|(t, _)| matches!(t, Token::Lt)));
    assert!(tokens
        .iter()
        .any(|(t, _)| matches!(t, Token::Ident(s) if s == "SGD")));
    assert!(tokens.iter().any(|(t, _)| matches!(t, Token::Gt)));
}

#[test]
fn test_lex_multiple_currencies() {
    let source = r#"
        money<USD> usd := $50.00
        money<EUR> eur := $75.50
        money<GBP> gbp := $100.25
    "#;
    let tokens = lex(source);

    let currency_count = tokens
        .iter()
        .filter(|(t, _)| matches!(t, Token::TyMoney))
        .count();
    assert_eq!(currency_count, 3);
}

#[test]
fn test_lex_date_format() {
    let source = r#"date start := 01-01-2024"#;
    let tokens = lex(source);

    assert!(tokens.iter().any(|(t, _)| matches!(t, Token::TyDate)));
    assert!(tokens.iter().any(|(t, _)| matches!(t, Token::Date(_))));
}

#[test]
fn test_lex_percent_type() {
    let source = "percent interest := 5.5%";
    let tokens = lex(source);

    assert!(tokens.iter().any(|(t, _)| matches!(t, Token::TyPercent)));
    assert!(tokens.iter().any(|(t, _)| matches!(t, Token::Percent(_))));
}

#[test]
fn test_lex_bounded_int() {
    let source = "BoundedInt<0, 100> age";
    let tokens = lex(source);

    assert!(tokens.iter().any(|(t, _)| matches!(t, Token::TyBoundedInt)));
    assert!(tokens.iter().any(|(t, _)| matches!(t, Token::Lt)));
    assert!(tokens.iter().any(|(t, _)| matches!(t, Token::Int(0))));
    assert!(tokens.iter().any(|(t, _)| matches!(t, Token::Comma)));
    assert!(tokens.iter().any(|(t, _)| matches!(t, Token::Int(100))));
}

#[test]
fn test_lex_temporal_keywords() {
    let source = "effective sunset retroactive";
    let tokens = lex(source);

    assert!(tokens.iter().any(|(t, _)| matches!(t, Token::Effective)));
    assert!(tokens.iter().any(|(t, _)| matches!(t, Token::Sunset)));
    assert!(tokens.iter().any(|(t, _)| matches!(t, Token::Retroactive)));
}

#[test]
fn test_lex_principle_keywords() {
    let source = "principle forall exists";
    let tokens = lex(source);

    assert!(tokens.iter().any(|(t, _)| matches!(t, Token::Principle)));
    assert!(tokens.iter().any(|(t, _)| matches!(t, Token::Forall)));
    assert!(tokens.iter().any(|(t, _)| matches!(t, Token::Exists)));
}
