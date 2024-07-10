mod ast {

    pub type Identifier = String;

    #[derive(Debug, PartialEq, Eq)]
    pub enum Literal {
        LInt(i32),
        LFloat(f64),
        LString(String),
        LBoolean(bool),
        LPercent(i32),
        LMoney(f64),
        LDate(String),
        LDuration(String),
        LPass,
    }

    #[derive(Debug, PartialEq, Eq)]
    pub enum Type {
        TInt,
        TFloat,
        TString,
        TBoolean,
        TPercent,
        TMoney,
        TDate,
        TDuration,
        TPass,
        TUnion(Vec<Type>),
        TScope,
        TStruct(Vec<(Type, Identifier)>),
    }

    #[derive(Debug, PartialEq, Eq)]
    pub enum Expr {
        EVar(Identifier),
        ELit(Literal),
        EBinOp(BinOp, Box<Expr>, Box<Expr>),
        EFuncCall(Identifier, Vec<Expr>),
        EMatch(Box<Expr>, Vec<(Pattern, Expr)>),
    }

    #[derive(Debug, PartialEq, Eq)]
    pub enum BinOp {
        Add,
        Subtract,
        Multiply,
        Divide,
        IntDivide,
        Modulo,
        Equals,
        NotEquals,
        GreaterThan,
        LessThan,
        GreaterOrEqual,
        LessOrEqual,
        And,
        Or,
        Not,
    }

    #[derive(Debug, PartialEq, Eq)]
    pub enum Pattern {
        PInt(i32),
        PFloat(f64),
        PString(String),
        PBoolean(bool),
        PPercent(i32),
        PMoney(f64),
        PDate(String),
        PDuration(String),
        PPass,
        PDefault,
    }

    #[derive(Debug, PartialEq, Eq)]
    pub enum Statement {
        SVarDecl(Type, Identifier, Expr),
        SFuncDecl(Type, Identifier, Vec<(Type, Identifier)>, Expr),
        SAssert(Expr),
        SScope(Identifier, Vec<Statement>),
    }

    #[derive(Debug, PartialEq, Eq)]
    pub struct Program(pub Vec<Statement>);

}
