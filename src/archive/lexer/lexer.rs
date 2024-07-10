use nom::{
    branch::alt,
    bytes::complete::{tag, take_while1},
    character::complete::{char, digit1, multispace0},
    combinator::{map, opt},
    error::ErrorKind,
    multi::many0,
    sequence::{delimited, pair, preceded, terminated},
    IResult,
};

#[derive(Debug, PartialEq)]
pub enum Token {
    TIdentifier(String),
    TIntLiteral(i64),
    TFloatLiteral(f64),
    TStringLiteral(String),
    TBooleanLiteral(bool),
    TPercent(i64),
    TMoney(f64),
    TDate(String),
    TDuration(String),
    TPass,
    TScope,
    TColonEquals,
    TUnion,
    TDot,
    TPlus,
    TMinus,
    TMultiply,
    TDivide,
    TIntDivide,
    TModulo,
    TEquals,
    TNotEquals,
    TGreaterThan,
    TLessThan,
    TGreaterOrEqual,
    TLessOrEqual,
    TAnd,
    TOr,
    TNot,
    TMatch,
    TCase,
    TConsequence,
    TFunc,
    TLParen,
    TRParen,
    TLBrace,
    TRBrace,
    TAssert,
    TEOF,
}

fn identifier(input: &str) -> IResult<&str, Token> {
    map(nom::alpha1, |s: &str| Token::TIdentifier(s.to_string()))(input)
}

fn int_literal(input: &str) -> IResult<&str, Token> {
    map(digit1, |s: &str| Token::TIntLiteral(s.parse().unwrap()))(input)
}

fn float_literal(input: &str) -> IResult<&str, Token> {
    map(
        pair(digit1, preceded(char('.'), digit1)),
        |(integer, fraction): (&str, &str)| {
            Token::TFloatLiteral(format!("{}.{}", integer, fraction).parse().unwrap())
        },
    )(input)
}

fn string_literal(input: &str) -> IResult<&str, Token> {
    map(
        delimited(char('"'), take_while1(|c| c != '"'), char('"')),
        |s: &str| Token::TStringLiteral(s.to_string()),
    )(input)
}

fn boolean_literal(input: &str) -> IResult<&str, Token> {
    alt((
        map(tag("true"), |_| Token::TBooleanLiteral(true)),
        map(tag("false"), |_| Token::TBooleanLiteral(false)),
    ))(input)
}

fn percent_literal(input: &str) -> IResult<&str, Token> {
    map(
        terminated(digit1, char('%')),
        |s: &str| Token::TPercent(s.parse().unwrap()),
    )(input)
}

fn money_literal(input: &str) -> IResult<&str, Token> {
    map(preceded(tag("$"), digit1), |s: &str| {
        Token::TMoney(s.parse().unwrap())
    })(input)
}

fn date_literal(input: &str) -> IResult<&str, Token> {
    map(many0(alt((digit1, char('-')))), |s: Vec<&str>| {
        Token::TDate(s.concat())
    })(input)
}

fn duration_literal(input: &str) -> IResult<&str, Token> {
    map(many0(alt((nom::alpha1, char(' ')))), |s: Vec<&str>| {
        Token::TDuration(s.concat())
    })(input)
}

fn reserved(input: &str, keyword: &str) -> IResult<&str, Token> {
    map(tag(keyword), |_| match keyword {
        "pass" => Token::TPass,
        "scope" => Token::TScope,
        "func" => Token::TFunc,
        "match" => Token::TMatch,
        "case" => Token::TCase,
        "assert" => Token::TAssert,
        _ => unreachable!(),
    })(input)
}

fn reserved_op(input: &str, op: &str) -> IResult<&str, Token> {
    map(tag(op), |_| match op {
        ":=" => Token::TColonEquals,
        "|" => Token::TUnion,
        "." => Token::TDot,
        "+" => Token::TPlus,
        "-" => Token::TMinus,
        "*" => Token::TMultiply,
        "/" => Token::TDivide,
        "//" => Token::TIntDivide,
        "%" => Token::TModulo,
        "==" => Token::TEquals,
        "!=" => Token::TNotEquals,
        ">" => Token::TGreaterThan,
        "<" => Token::TLessThan,
        ">=" => Token::TGreaterOrEqual,
        "<=" => Token::TLessOrEqual,
        "and" => Token::TAnd,
        "or" => Token::TOr,
        "not" => Token::TNot,
        _ => unreachable!(),
    })(input)
}

fn symbol(input: &str, sym: &str) -> IResult<&str, Token> {
    map(tag(sym), |_| match sym {
        "(" => Token::TLParen,
        ")" => Token::TRParen,
        "{" => Token::TLBrace,
        "}" => Token::TRBrace,
        _ => unreachable!(),
    })(input)
}

fn lexeme<F>(input: &str, f: F) -> IResult<&str, Token>
where
    F: Fn(&str) -> IResult<&str, Token>,
{
    delimited(multispace0, f, multispace0)(input)
}

fn tokenize(input: &str) -> IResult<&str, Vec<Token>> {
    many0(alt((
        lexeme(identifier),
        lexeme(int_literal),
        lexeme(float_literal),
        lexeme(string_literal),
        lexeme(boolean_literal),
        lexeme(percent_literal),
        lexeme(money_literal),
        lexeme(date_literal),
        lexeme(duration_literal),
        lexeme(|i| reserved(i, "pass")),
        lexeme(|i| reserved(i, "scope")),
        lexeme(|i| reserved(i, "func")),
        lexeme(|i| reserved(i, "match")),
        lexeme(|i| reserved(i, "case")),
        lexeme(|i| reserved(i, "assert")),
        lexeme(|i| reserved_op(i, ":=")),
        lexeme(|i| reserved_op(i, "|")),
        lexeme(|i| reserved_op(i, ".")),
        lexeme(|i| reserved_op(i, "+")),
        lexeme(|i| reserved_op(i, "-")),
        lexeme(|i| reserved_op(i, "*")),
        lexeme(|i| reserved_op(i, "/")),
        lexeme(|i| reserved_op(i, "//")),
        lexeme(|i| reserved_op(i, "%")),
        lexeme(|i| reserved_op(i, "==")),
        lexeme(|i| reserved_op(i, "!=")),
        lexeme(|i| reserved_op(i, ">")),
        lexeme(|i| reserved_op(i, "<")),
        lexeme(|i| reserved_op(i, ">=")),
        lexeme(|i| reserved_op(i, "<=")),
        lexeme(|i| reserved_op(i, "and")),
        lexeme(|i| reserved_op(i, "or")),
        lexeme(|i| reserved_op(i, "not")),
        lexeme(|i| symbol(i, "(")),
        lexeme(|i| symbol(i, ")")),
        lexeme(|i| symbol(i, "{")),
        lexeme(|i| symbol(i, "}")),
    )))(input)
}
