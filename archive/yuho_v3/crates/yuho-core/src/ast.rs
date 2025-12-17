use serde::{Deserialize, Serialize};

/// Source location for error reporting
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Span {
    pub start: usize,
    pub end: usize,
}

/// A complete Yuho program
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Program {
    pub imports: Vec<ImportStatement>,
    pub items: Vec<Item>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ImportStatement {
    pub names: Vec<String>,
    pub from: String,
    pub span: Span,
}

/// Top-level items
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum Item {
    Scope(ScopeDefinition),
    Struct(StructDefinition),
    Enum(EnumDefinition),
    Function(FunctionDefinition),
    Declaration(Declaration),
    TypeAlias(TypeAliasDefinition),
    LegalTest(LegalTestDefinition),
    ConflictCheck(ConflictCheckDefinition),
    Principle(PrincipleDefinition),
    Proviso(ProvisoClause),
}

/// Legal test definition for conjunctive requirements
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct LegalTestDefinition {
    pub name: String,
    pub requirements: Vec<LegalRequirement>,
    pub span: Span,
}

/// Individual requirement in a legal test
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct LegalRequirement {
    pub name: String,
    pub ty: Type,
    pub span: Span,
}

/// Conflict check definition to verify no contradictions between files
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ConflictCheckDefinition {
    pub file1: String,
    pub file2: String,
    pub span: Span,
}

/// Principle definition for legal principle verification
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct PrincipleDefinition {
    pub name: String,
    pub body: Expr,
    pub span: Span,
}

/// Proviso clause - adds exceptions or qualifications to rules
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ProvisoClause {
    pub condition: Expr,
    pub exception: Vec<Statement>,
    pub applies_to: Option<String>, // Optional: which rule/struct this proviso modifies
    pub span: Span,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct TypeAliasDefinition {
    pub name: String,
    pub type_params: Vec<String>, // Generic parameters
    pub target: Type,
    pub span: Span,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ScopeDefinition {
    pub name: String,
    pub items: Vec<Item>,
    pub span: Span,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct StructDefinition {
    pub name: String,
    pub type_params: Vec<String>, // Generic type parameters: <T, U>
    pub fields: Vec<Field>,
    pub extends_from: Option<String>,
    pub span: Span,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Field {
    pub name: String,
    pub ty: Type,
    pub constraints: Vec<Constraint>,
    pub annotations: Vec<Annotation>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum Annotation {
    Presumed(String), // @presumed(EnumVariant)
    Precedent {
        citation: String,
    }, // @precedent("Tan Siew Eng v PP [1997] SGHC 123")
    Hierarchy {
        level: String,
        subordinate_to: Option<String>,
    },
    Amended {
        date: String,
        act: String,
    },
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct EnumDefinition {
    pub name: String,
    pub variants: Vec<String>,
    pub mutually_exclusive: bool, // If true, compiler verifies mutual exclusivity
    pub span: Span,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct FunctionDefinition {
    pub name: String,
    pub type_params: Vec<String>, // Generic type parameters: <T, U>
    pub params: Vec<Parameter>,
    pub return_type: Type,
    pub body: Vec<Statement>,
    pub requires_clause: Option<String>, // Burden of proof requirement
    pub span: Span,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Parameter {
    pub name: String,
    pub ty: Type,
}

/// Type representation
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum Type {
    // Primitive types
    Int,
    Float,
    Bool,
    String,
    Money,
    Date,
    Duration,
    Percent,
    Pass, // nullable/unit type
    Named(String),
    Union(Box<Type>, Box<Type>),

    // Dependent types (Phase 1 Enhancement)
    BoundedInt {
        min: i64,
        max: i64,
    },
    NonEmpty(Box<Type>),
    ValidDate {
        after: Option<String>,
        before: Option<String>,
    },
    Positive(Box<Type>), // Numeric > 0
    Citation {
        section: String,
        subsection: String,
        act: String,
    }, // Legal citation

    // Temporal types (Phase 2)
    TemporalValue {
        // Value with effective date range
        inner: Box<Type>,
        valid_from: Option<String>,  // Effective date
        valid_until: Option<String>, // Sunset date
    },

    // Collection types
    Array(Box<Type>),

    // Parametric money type
    MoneyWithCurrency(String), // e.g., money<SGD>, money<USD>

    // Generic types
    TypeVariable(String), // T, U, V - unbound type parameter
    Generic {
        // Container<T>, Result<T, E>
        name: String,
        args: Vec<Type>,
    },
}

/// Type constraints for dependent types and refinement
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum Constraint {
    // Comparison constraints
    GreaterThan(Expr),
    LessThan(Expr),
    GreaterThanOrEqual(Expr),
    LessThanOrEqual(Expr),
    Equal(Expr),
    NotEqual(Expr),

    // Range constraints
    InRange { min: Expr, max: Expr },

    // Logical constraints
    And(Box<Constraint>, Box<Constraint>),
    Or(Box<Constraint>, Box<Constraint>),
    Not(Box<Constraint>),

    // Temporal constraints
    Before(Expr),                       // date must be before given date
    After(Expr),                        // date must be after given date
    Between { start: Expr, end: Expr }, // date must be between start and end

    // Custom predicate
    Custom(String), // For complex predicates
}

/// Statements
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum Statement {
    Declaration(Declaration),
    Assignment(Assignment),
    Return(Expr),
    Match(MatchExpr),
    Pass,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Declaration {
    pub name: String,
    pub ty: Type,
    pub value: Expr,
    pub span: Span,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Assignment {
    pub target: String,
    pub value: Expr,
    pub span: Span,
}

/// Expressions
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum Expr {
    Literal(Literal),
    Identifier(String),
    Binary(Box<Expr>, BinaryOp, Box<Expr>),
    Unary(UnaryOp, Box<Expr>),
    Call(String, Vec<Expr>),
    FieldAccess(Box<Expr>, String),
    StructInit(StructInit),
    Match(Box<MatchExpr>),
    Forall {
        var: String,
        ty: Type,
        body: Box<Expr>,
    },
    Exists {
        var: String,
        ty: Type,
        body: Box<Expr>,
    },
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum Literal {
    Int(i64),
    Float(f64),
    Bool(bool),
    String(String),
    Money(f64),
    Date(String),     // DD-MM-YYYY format
    Duration(String), // e.g., "1y2m3d"
    Percent(f64),
    Pass,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum BinaryOp {
    Add,
    Sub,
    Mul,
    Div,
    Mod,
    Eq,
    Neq,
    Lt,
    Gt,
    Lte,
    Gte,
    And,
    Or,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum UnaryOp {
    Not,
    Neg,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct StructInit {
    pub name: String,
    pub fields: Vec<(String, Expr)>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct MatchExpr {
    pub scrutinee: Box<Expr>,
    pub cases: Vec<MatchCase>,
    pub span: Span,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct MatchCase {
    pub pattern: Pattern,
    pub guard: Option<Expr>, // Optional guard clause: where condition
    pub consequence: Expr,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum Pattern {
    Literal(Literal),
    Identifier(String),
    Wildcard,          // _
    Satisfies(String), // satisfies LegalTestName
}
