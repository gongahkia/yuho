use logos::Logos;

#[derive(Logos, Debug, Clone, PartialEq)]
#[logos(skip r"[ \t\r\n\f]+")]
#[logos(skip r"//[^\n]*")]
#[logos(skip r"/\*[^*]*\*+(?:[^/*][^*]*\*+)*/")]
pub enum Token {
    // Keywords
    #[token("scope")]
    Scope,
    #[token("struct")]
    Struct,
    #[token("enum")]
    Enum,
    #[token("func")]
    Func,
    #[token("match")]
    Match,
    #[token("case")]
    Case,
    #[token("consequence")]
    Consequence,
    #[token("referencing")]
    Referencing,
    #[token("from")]
    From,
    #[token("pass")]
    Pass,
    #[token("where")]
    Where,
    #[token("type")]
    Type,
    #[token("legal_test")]
    LegalTest,
    #[token("requires")]
    Requires,
    #[token("satisfies")]
    Satisfies,
    #[token("mutually_exclusive")]
    MutuallyExclusive,
    #[token("verify")]
    Verify,
    #[token("no_conflict")]
    NoConflict,
    #[token("between")]
    Between,
    #[token("effective")]
    Effective,
    #[token("sunset")]
    Sunset,
    #[token("retroactive")]
    Retroactive,
    #[token("presumed")]
    Presumed,
    #[token("with")]
    With,
    #[token("proof")]
    Proof,
    #[token("burden")]
    Burden,
    #[token("precedent")]
    Precedent,
    #[token("extends")]
    Extends,
    #[token("proviso")]
    Proviso,
    #[token("provided")]
    Provided,
    #[token("that")]
    That,
    #[token("principle")]
    Principle,
    #[token("forall")]
    Forall,
    #[token("exists")]
    Exists,

    // Types
    #[token("int")]
    TyInt,
    #[token("integer")]
    TyInteger,
    #[token("float")]
    TyFloat,
    #[token("bool")]
    TyBool,
    #[token("boolean")]
    TyBoolean,
    #[token("string")]
    TyString,
    #[token("money")]
    TyMoney,
    #[token("date")]
    TyDate,
    #[token("duration")]
    TyDuration,
    #[token("percent")]
    TyPercent,

    // Dependent type keywords (Phase 1)
    #[token("BoundedInt")]
    TyBoundedInt,
    #[token("NonEmpty")]
    TyNonEmpty,
    #[token("Positive")]
    TyPositive,
    #[token("ValidDate")]
    TyValidDate,
    #[token("Array")]
    TyArray,
    #[token("Citation")]
    TyCitation,

    // Temporal type keywords (Phase 2)
    #[token("Temporal")]
    TyTemporal,

    // Literals
    #[token("true")]
    True,
    #[token("false")]
    False,

    #[regex(r"\$[0-9]+(\.[0-9]+)?", |lex| {
        lex.slice()[1..].parse::<f64>().ok()
    })]
    Money(f64),

    #[regex(r"[0-9]{2}-[0-9]{2}-[0-9]{4}", |lex| lex.slice().to_string())]
    Date(String),

    #[regex(r"[0-9]+(\.[0-9]+)?%", |lex| {
        let s = lex.slice();
        s[..s.len()-1].parse::<f64>().ok()
    })]
    Percent(f64),

    #[regex(r"[0-9]+\.[0-9]+", |lex| lex.slice().parse::<f64>().ok())]
    Float(f64),

    #[regex(r"[0-9]+", |lex| lex.slice().parse::<i64>().ok())]
    Int(i64),

    #[regex(r#""[^"]*""#, |lex| {
        let s = lex.slice();
        s[1..s.len()-1].to_string()
    })]
    String(String),

    #[regex(r"[a-zA-Z_][a-zA-Z0-9_]*", |lex| lex.slice().to_string(), priority = 1)]
    Ident(String),

    // Operators
    #[token(":=")]
    Assign,
    #[token("=")]
    Equals, // For named parameters in types
    #[token("||")]
    Or,
    #[token("&&")]
    And,
    #[token("==")]
    Eq,
    #[token("!=")]
    Neq,
    #[token("<=")]
    Lte,
    #[token(">=")]
    Gte,
    #[token("<")]
    Lt,
    #[token(">")]
    Gt,
    #[token("+")]
    Plus,
    #[token("-")]
    Minus,
    #[token("*")]
    Star,
    #[token("/")]
    Slash,
    #[token("%")]
    Percent_,
    #[token("!")]
    Not,
    #[token("@")]
    At,

    // Delimiters
    #[token("{")]
    LBrace,
    #[token("}")]
    RBrace,
    #[token("(")]
    LParen,
    #[token(")")]
    RParen,
    #[token("[")]
    LBracket,
    #[token("]")]
    RBracket,
    #[token(",")]
    Comma,
    #[token(".")]
    Dot,
    #[token(":")]
    Colon,
    #[token("_", priority = 2)]
    Underscore,
}

pub fn lex(input: &str) -> Vec<(Token, std::ops::Range<usize>)> {
    Token::lexer(input)
        .spanned()
        .filter_map(|(tok, span)| tok.ok().map(|t| (t, span)))
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_basic_tokens() {
        let tokens = lex("int x := 42");
        assert_eq!(tokens.len(), 4);
    }

    #[test]
    fn test_money() {
        let tokens = lex("$100.50");
        assert!(matches!(tokens[0].0, Token::Money(100.5)));
    }

    #[test]
    fn test_date() {
        let tokens = lex("25-12-2024");
        assert!(matches!(tokens[0].0, Token::Date(_)));
    }

    #[test]
    fn test_comments_single_line() {
        let tokens = lex("int x := 42 // this is a comment");
        assert_eq!(tokens.len(), 4); // Should skip comment
        assert!(matches!(tokens[0].0, Token::TyInt));
    }

    #[test]
    fn test_comments_multi_line() {
        let tokens = lex("int /* comment */ x := 42");
        assert_eq!(tokens.len(), 4);
        assert!(matches!(tokens[0].0, Token::TyInt));
        assert!(matches!(tokens[1].0, Token::Ident(_)));
    }

    #[test]
    fn test_string_literal() {
        let tokens = lex(r#"string s := "hello world""#);
        if let Token::String(s) = &tokens[3].0 {
            assert_eq!(s, "hello world");
        } else {
            panic!("Expected string literal");
        }
    }

    #[test]
    fn test_percent_type_vs_modulo() {
        let tokens = lex("15% + 5 % 2");
        assert!(matches!(tokens[0].0, Token::Percent(_))); // 15% is percent literal
        assert!(matches!(tokens[1].0, Token::Plus));
        assert!(matches!(tokens[2].0, Token::Int(5)));
        assert!(matches!(tokens[3].0, Token::Percent_)); // % is modulo operator
    }

    #[test]
    fn test_dependent_type_tokens() {
        let tokens = lex("BoundedInt<0, 100>");
        assert!(matches!(tokens[0].0, Token::TyBoundedInt));
        assert!(matches!(tokens[1].0, Token::Lt));
        assert!(matches!(tokens[2].0, Token::Int(0)));
        assert!(matches!(tokens[3].0, Token::Comma));
        assert!(matches!(tokens[4].0, Token::Int(100)));
        assert!(matches!(tokens[5].0, Token::Gt));
    }

    #[test]
    fn test_money_with_currency() {
        let tokens = lex("money<SGD>");
        assert!(matches!(tokens[0].0, Token::TyMoney));
        assert!(matches!(tokens[1].0, Token::Lt));
        if let Token::Ident(currency) = &tokens[2].0 {
            assert_eq!(currency, "SGD");
        }
        assert!(matches!(tokens[3].0, Token::Gt));
    }

    #[test]
    fn test_operators_all() {
        let tokens = lex(":= || && == != <= >= < > + - * / % !");
        assert!(matches!(tokens[0].0, Token::Assign));
        assert!(matches!(tokens[1].0, Token::Or));
        assert!(matches!(tokens[2].0, Token::And));
        assert!(matches!(tokens[3].0, Token::Eq));
        assert!(matches!(tokens[4].0, Token::Neq));
        assert!(matches!(tokens[5].0, Token::Lte));
        assert!(matches!(tokens[6].0, Token::Gte));
        assert!(matches!(tokens[7].0, Token::Lt));
        assert!(matches!(tokens[8].0, Token::Gt));
    }

    #[test]
    fn test_float_vs_int() {
        let tokens = lex("42 42.5");
        assert!(matches!(tokens[0].0, Token::Int(42)));
        assert!(matches!(tokens[1].0, Token::Float(_)));
    }

    #[test]
    fn test_whitespace_handling() {
        let tokens = lex("int\n\t x\r\n:= 42");
        assert_eq!(tokens.len(), 4);
        assert!(matches!(tokens[0].0, Token::TyInt));
    }

    #[test]
    fn test_underscore_wildcard() {
        let tokens = lex("case _ := pass");
        assert!(matches!(tokens[0].0, Token::Case));
        assert!(matches!(tokens[1].0, Token::Underscore));
        assert!(matches!(tokens[2].0, Token::Assign));
        assert!(matches!(tokens[3].0, Token::Pass));
    }

    #[test]
    fn test_duration_type_keyword() {
        let tokens = lex("duration contract_duration");
        assert!(matches!(tokens[0].0, Token::TyDuration));
        assert!(matches!(tokens[1].0, Token::Ident(_)));
    }

    #[test]
    fn test_date_formats() {
        let tokens = lex("01-01-2024 31-12-2025 15-06-2030");
        assert!(matches!(tokens[0].0, Token::Date(_)));
        assert!(matches!(tokens[1].0, Token::Date(_)));
        assert!(matches!(tokens[2].0, Token::Date(_)));
    }

    #[test]
    fn test_enum_variant_access() {
        let tokens = lex("Status.Active Color.Red Verdict.Guilty");
        assert!(matches!(tokens[0].0, Token::Ident(_)));
        assert!(matches!(tokens[1].0, Token::Dot));
        assert!(matches!(tokens[2].0, Token::Ident(_)));
    }

    #[test]
    fn test_keywords_not_identifiers() {
        let tokens = lex("struct int bool string match");
        assert!(matches!(tokens[0].0, Token::Struct));
        assert!(matches!(tokens[1].0, Token::TyInt));
        assert!(matches!(tokens[2].0, Token::TyBool));
        assert!(matches!(tokens[3].0, Token::TyString));
        assert!(matches!(tokens[4].0, Token::Match));
        assert!(!matches!(tokens[0].0, Token::Ident(_)));
    }

    #[test]
    fn test_long_identifiers() {
        let tokens = lex("very_long_variable_name_that_is_valid another_long_name_123");
        if let Token::Ident(name) = &tokens[0].0 {
            assert_eq!(name, "very_long_variable_name_that_is_valid");
        }
        if let Token::Ident(name) = &tokens[1].0 {
            assert_eq!(name, "another_long_name_123");
        }
    }

    #[test]
    fn test_consecutive_operators() {
        let tokens = lex("+ - * / %");
        assert!(matches!(tokens[0].0, Token::Plus));
        assert!(matches!(tokens[1].0, Token::Minus));
        assert!(matches!(tokens[2].0, Token::Star));
        assert!(matches!(tokens[3].0, Token::Slash));
        assert!(matches!(tokens[4].0, Token::Percent_));
    }

    #[test]
    fn test_complex_money_literals() {
        let tokens = lex("$0.01 $1000.00 $99.99");
        if let Token::Money(val) = tokens[0].0 {
            assert!((val - 0.01).abs() < 0.001);
        }
        if let Token::Money(val) = tokens[1].0 {
            assert!((val - 1000.0).abs() < 0.001);
        }
    }

    #[test]
    fn test_all_dependent_type_keywords() {
        let tokens = lex("BoundedInt NonEmpty Positive ValidDate Array");
        assert!(matches!(tokens[0].0, Token::TyBoundedInt));
        assert!(matches!(tokens[1].0, Token::TyNonEmpty));
        assert!(matches!(tokens[2].0, Token::TyPositive));
        assert!(matches!(tokens[3].0, Token::TyValidDate));
        assert!(matches!(tokens[4].0, Token::TyArray));
    }

    #[test]
    fn test_type_alias_keyword() {
        let tokens = lex("type UserId := int");
        assert!(matches!(tokens[0].0, Token::Type));
        assert!(matches!(tokens[1].0, Token::Ident(_)));
        assert!(matches!(tokens[2].0, Token::Assign));
        assert!(matches!(tokens[3].0, Token::TyInt));
    }

    #[test]
    fn test_conflict_detection_keywords() {
        let tokens = lex("verify no_conflict between");
        assert!(matches!(tokens[0].0, Token::Verify));
        assert!(matches!(tokens[1].0, Token::NoConflict));
        assert!(matches!(tokens[2].0, Token::Between));
    }
}
