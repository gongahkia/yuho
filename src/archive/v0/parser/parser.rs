use nom::{
    branch::alt,
    bytes::complete::tag,
    character::complete::{char, digit1},
    combinator::{map, opt},
    multi::{many0, separated_list},
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

#[derive(Debug, PartialEq)]
pub enum Type {
    TInt,
    TFloat,
    TString,
    TBoolean,
    TPercent,
    TMoney,
    TDate,
    TDuration,
}

#[derive(Debug, PartialEq)]
pub enum Expression {
    Var(String),
    Lit(Literal),
    UnaryOp(UnaryOperator, Box<Expression>),
    BinaryOp(BinaryOperator, Box<Expression>, Box<Expression>),
}

#[derive(Debug, PartialEq)]
pub enum Literal {
    LInt(i64),
    LFloat(f64),
    LString(String),
    LBoolean(bool),
}

#[derive(Debug, PartialEq)]
pub enum Statement {
    VariableDeclaration(Type, String, Expression),
    FunctionDeclaration(Type, String, Vec<(Type, String)>, Expression),
    Scope(String, Vec<Statement>),
    Struct(String, Vec<(Type, String)>),
    Assertion(Expression),
}

#[derive(Debug, PartialEq)]
pub enum UnaryOperator {
    Neg,
}

#[derive(Debug, PartialEq)]
pub enum BinaryOperator {
    Add,
    Sub,
    Mul,
    Div,
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
        delimited(char('"'), take_until("\""), char('"')),
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
    map(
        preceded(tag("$"), digit1),
        |s: &str| Token::TMoney(s.parse().unwrap()),
    )(input)
}

fn date_literal(input: &str) -> IResult<&str, Token> {
    map(take_until(" "), |s: &str| Token::TDate(s.to_string()))(input)
}

fn duration_literal(input: &str) -> IResult<&str, Token> {
    map(take_until(" "), |s: &str| Token::TDuration(s.to_string()))(input)
}

fn parse_literal(input: &str) -> IResult<&str, Literal> {
    alt((
        map(int_literal, |t| Literal::LInt(t)),
        map(float_literal, |t| Literal::LFloat(t)),
        map(string_literal, |t| Literal::LString(t)),
        map(boolean_literal, |t| Literal::LBoolean(t)),
    ))(input)
}

fn parse_type(input: &str) -> IResult<&str, Type> {
    alt((
        map(tag("int"), |_| Type::TInt),
        map(tag("float"), |_| Type::TFloat),
        map(tag("string"), |_| Type::TString),
        map(tag("boolean"), |_| Type::TBoolean),
        map(tag("money"), |_| Type::TMoney),
        map(tag("date"), |_| Type::TDate),
        map(tag("duration"), |_| Type::TDuration),
    ))(input)
}

fn parse_expression(input: &str) -> IResult<&str, Expression> {
    alt((
        map(identifier, |id| Expression::Var(id)),
        map(parse_literal, |lit| Expression::Lit(lit)),
    ))(input)
}

fn parse_variable_declaration(input: &str) -> IResult<&str, Statement> {
    let (input, typ) = parse_type(input)?;
    let (input, name) = identifier(input)?;
    let (input, _) = tag(":=")(input)?;
    let (input, value) = parse_expression(input)?;
    Ok((input, Statement::VariableDeclaration(typ, name, value)))
}

fn parse_function_declaration(input: &str) -> IResult<&str, Statement> {
    let (input, ret_type) = parse_type(input)?;
    let (input, _) = tag("func")(input)?;
    let (input, name) = identifier(input)?;
    let (input, params) = delimited(tag("("), separated_list(tag(","), parse_param), tag(")"))(input)?;
    let (input, body) = parse_expression(input)?;
    Ok((input, Statement::FunctionDeclaration(ret_type, name, params, body)))
}

fn parse_param(input: &str) -> IResult<&str, (Type, String)> {
    let (input, typ) = parse_type(input)?;
    let (input, name) = identifier(input)?;
    Ok((input, (typ, name)))
}

fn parse_scope(input: &str) -> IResult<&str, Statement> {
    let (input, _) = tag("scope")(input)?;
    let (input, name) = identifier(input)?;
    let (input, body) = braces(many0(parse_statement))(input)?;
    Ok((input, Statement::Scope(name, body)))
}

fn parse_struct(input: &str) -> IResult<&str, Statement> {
    let (input, _) = tag("struct")(input)?;
    let (input, name) = identifier(input)?;
    let (input, fields) = braces(separated_list(tag(","), parse_field))(input)?;
    Ok((input, Statement::Struct(name, fields)))
}

fn parse_field(input: &str) -> IResult<&str, (Type, String)> {
    let (input, typ) = parse_type(input)?;
    let (input, name) = identifier(input)?;
    Ok((input, (typ, name)))
}

fn parse_assertion(input: &str) -> IResult<&str, Statement> {
    let (input, _) = tag("assert")(input)?;
    let (input, expr) = parse_expression(input)?;
    Ok((input, Statement::Assertion(expr)))
}

fn parse_statement(input: &str) -> IResult<&str, Statement> {
    alt((
        parse_variable_declaration,
        parse_function_declaration,
        parse_scope,
        parse_struct,
        parse_assertion,
    ))(input)
}

pub fn parse_program(input: &str) -> IResult<&str, Vec<Statement>> {
    many0(parse_statement)(input)
}
