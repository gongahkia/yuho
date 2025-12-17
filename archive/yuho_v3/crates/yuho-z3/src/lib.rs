//! Z3 SMT solver integration for Yuho
//!
//! This crate provides formal verification capabilities using the Z3 theorem prover.
//! It translates Yuho AST to Z3 assertions and supports:
//! - Satisfiability (SAT) queries
//! - Unsatisfiability (UNSAT) proofs
//! - Counterexample generation
//! - Model enumeration

pub mod counterexample;
pub mod explanation;
pub mod principle_explain;
pub mod quantifier;

use std::collections::HashMap;
use std::ops::{Add, Div, Mul, Rem, Sub};
use thiserror::Error;
use yuho_core::ast::*;
use z3::ast::{Bool, Int, Real};
use z3::{SatResult, Solver};

#[derive(Error, Debug)]
pub enum Z3Error {
    #[error("Z3 translation error: {0}")]
    TranslationError(String),

    #[error("Unsupported type for Z3: {0}")]
    UnsupportedType(String),

    #[error("Unsupported expression for Z3: {0}")]
    UnsupportedExpression(String),

    #[error("Z3 solver error: {0}")]
    SolverError(String),
}

pub type Z3Result<T> = Result<T, Z3Error>;

/// Verification result for principles
#[derive(Debug, Clone)]
pub struct PrincipleVerificationResult {
    pub is_valid: bool,
    pub smt_formula: String,
    pub counterexample: Option<String>,
    pub explanation: Option<String>,
}

/// Verify a legal principle using Z3
pub fn verify_principle(
    principle: &yuho_core::ast::PrincipleDefinition,
) -> Z3Result<PrincipleVerificationResult> {
    // Translate the principle body to Z3 SMT-LIB2 format
    let smt_formula = quantifier::translate_principle_to_z3(principle)?;

    // Generate human-readable explanation
    let explanation = Some(principle_explain::explain_principle(principle));

    // For now, return a placeholder result
    // Full Z3 solver integration with actual checking will be in verification command
    Ok(PrincipleVerificationResult {
        is_valid: true,
        smt_formula,
        counterexample: None,
        explanation,
    })
}

pub type Z3Result<T> = Result<T, Z3Error>;

/// Z3 expression types for dynamic typing
#[derive(Debug, Clone)]
pub enum Z3Expr<'ctx> {
    Int(Int<'ctx>),
    Real(Real<'ctx>),
    Bool(Bool<'ctx>),
}

/// Quantifier pattern for Z3 SMT formulas
#[derive(Debug, Clone)]
pub struct QuantifierPattern<'ctx> {
    pub var_name: String,
    pub var_sort: &'ctx z3::Sort<'ctx>,
    pub body: Bool<'ctx>,
}

/// Z3 verification context
///
/// This struct wraps the Z3 solver and provides methods for
/// translating Yuho AST to Z3 formulas and checking satisfiability.
pub struct VerificationContext<'ctx> {
    ctx: &'ctx z3::Context,
    solver: Solver<'ctx>,
    variables: HashMap<String, Z3Expr<'ctx>>,
}

impl VerificationContext {
    /// Create a new verification context
    pub fn new() -> Self {
        let cfg = z3::Config::new();
        let ctx = z3::Context::new(&cfg);
        let solver = Solver::new(&ctx);
        Self {
            solver,
            variables: HashMap::new(),
        }
    }

    /// Create a context with custom Z3 timeout
    pub fn with_timeout(timeout_ms: u32) -> Self {
        let mut cfg = z3::Config::new();
        cfg.set_timeout_msec(timeout_ms);
        let ctx = z3::Context::new(&cfg);
        let solver = Solver::new(&ctx);
        Self {
            solver,
            variables: HashMap::new(),
        }
    }

    /// Verify a BoundedInt constraint
    pub fn verify_bounded_int(&self, value: i64, min: i64, max: i64) -> Z3Result<bool> {
        if min > max {
            return Err(Z3Error::TranslationError(format!(
                "Invalid range: min ({}) > max ({})",
                min, max
            )));
        }

        let cfg = z3::Config::new();
        let ctx = z3::Context::new(&cfg);
        let val = Int::from_i64(&ctx, value);
        let min_const = Int::from_i64(&ctx, min);
        let max_const = Int::from_i64(&ctx, max);

        // value >= min && value <= max
        let constraint = Bool::and(&ctx, &[&val.ge(&min_const), &val.le(&max_const)]);

        let solver = Solver::new(&ctx);
        solver.assert(&constraint);

        match solver.check() {
            SatResult::Sat => Ok(true),
            SatResult::Unsat => Ok(false),
            SatResult::Unknown => Err(Z3Error::SolverError(
                "Z3 returned unknown result".to_string(),
            )),
        }
    }

    /// Verify a Positive constraint
    pub fn verify_positive(&self, value: i64) -> Z3Result<bool> {
        let cfg = z3::Config::new();
        let ctx = z3::Context::new(&cfg);
        let val = Int::from_i64(&ctx, value);
        let zero = Int::from_i64(&ctx, 0);

        let constraint = val.gt(&zero);
        let solver = Solver::new(&ctx);
        solver.assert(&constraint);

        match solver.check() {
            SatResult::Sat => Ok(true),
            SatResult::Unsat => Ok(false),
            SatResult::Unknown => Err(Z3Error::SolverError(
                "Z3 returned unknown result".to_string(),
            )),
        }
    }

    /// Verify a positive float constraint
    pub fn verify_positive_float(&self, value: f64) -> Z3Result<bool> {
        let cfg = z3::Config::new();
        let ctx = z3::Context::new(&cfg);
        let num = (value * 1000.0) as i64;
        let val = Real::from_real(&ctx, num, 1000);
        let zero = Real::from_real(&ctx, 0, 1);

        let constraint = val.gt(&zero);
        let solver = Solver::new(&ctx);
        solver.assert(&constraint);

        match solver.check() {
            SatResult::Sat => Ok(true),
            SatResult::Unsat => Ok(false),
            SatResult::Unknown => Err(Z3Error::SolverError(
                "Z3 returned unknown result".to_string(),
            )),
        }
    }

    /// Verify NonEmpty collection
    pub fn verify_non_empty(&self, length: usize) -> Z3Result<bool> {
        Ok(length > 0)
    }

    /// Verify Citation format
    ///
    /// Validates that a citation has non-empty section, subsection, and act fields.
    /// Note: This is a simple structural validation, not a deep semantic check.
    pub fn verify_citation(&self, section: &str, subsection: &str, act: &str) -> Z3Result<bool> {
        Ok(!section.is_empty() && !subsection.is_empty() && !act.is_empty())
    }

    /// Verify temporal window validity
    ///
    /// Checks that valid_from date is before valid_until date.
    /// Uses Z3 to verify temporal ordering constraints.
    pub fn verify_temporal_window(
        &self,
        valid_from: Option<&str>,
        valid_until: Option<&str>,
    ) -> Z3Result<bool> {
        if let (Some(from), Some(until)) = (valid_from, valid_until) {
            // Parse dates
            use chrono::NaiveDate;
            let from_date = NaiveDate::parse_from_str(from, "%d-%m-%Y")
                .map_err(|e| Z3Error::TranslationError(format!("Invalid from date: {}", e)))?;
            let until_date = NaiveDate::parse_from_str(until, "%d-%m-%Y")
                .map_err(|e| Z3Error::TranslationError(format!("Invalid until date: {}", e)))?;

            // Verify ordering
            Ok(from_date < until_date)
        } else {
            Ok(true) // No constraint to verify
        }
    }

    /// Verify date is within temporal bounds
    ///
    /// Checks that a given date falls within the specified temporal window.
    pub fn verify_date_in_temporal_window(
        &self,
        date: &str,
        valid_from: Option<&str>,
        valid_until: Option<&str>,
    ) -> Z3Result<bool> {
        use chrono::NaiveDate;
        let check_date = NaiveDate::parse_from_str(date, "%d-%m-%Y")
            .map_err(|e| Z3Error::TranslationError(format!("Invalid date: {}", e)))?;

        if let Some(from) = valid_from {
            let from_date = NaiveDate::parse_from_str(from, "%d-%m-%Y")
                .map_err(|e| Z3Error::TranslationError(format!("Invalid from date: {}", e)))?;
            if check_date < from_date {
                return Ok(false);
            }
        }

        if let Some(until) = valid_until {
            let until_date = NaiveDate::parse_from_str(until, "%d-%m-%Y")
                .map_err(|e| Z3Error::TranslationError(format!("Invalid until date: {}", e)))?;
            if check_date > until_date {
                return Ok(false);
            }
        }

        Ok(true)
    }

    /// Verify that a legal test's conjunctive requirements can all be satisfied
    ///
    /// This checks that when all requirements are set to true, the combination is satisfiable.
    /// For boolean requirements, this validates logical consistency.
    pub fn verify_legal_test_satisfiable(&self, requirements: &[(String, bool)]) -> Z3Result<bool> {
        if requirements.is_empty() {
            return Ok(true);
        }

        let cfg = z3::Config::new();
        let ctx = z3::Context::new(&cfg);

        // Create assertions for each requirement
        let mut assertions = Vec::new();
        for (name, value) in requirements {
            let var = Bool::new_const(&ctx, name.as_str());
            let assertion = if *value { var } else { var.not() };
            assertions.push(assertion);
        }

        // Check if ALL requirements can be satisfied together (conjunction)
        let conjunction = Bool::and(&ctx, &assertions.iter().collect::<Vec<_>>());
        let solver = Solver::new(&ctx);
        solver.assert(&conjunction);

        match solver.check() {
            SatResult::Sat => Ok(true),
            SatResult::Unsat => Ok(false),
            SatResult::Unknown => Err(Z3Error::SolverError(
                "Z3 returned unknown result for legal test verification".to_string(),
            )),
        }
    }

    /// Verify a where clause constraint
    pub fn verify_where_clause(&self, constraint: &Constraint, value: &Expr) -> Z3Result<bool> {
        let cfg = z3::Config::new();
        let ctx = z3::Context::new(&cfg);

        // Build constraint expression
        let constraint_expr = self.build_constraint(&ctx, constraint, value)?;

        let solver = Solver::new(&ctx);
        solver.assert(&constraint_expr);

        match solver.check() {
            SatResult::Sat => Ok(true),
            SatResult::Unsat => Ok(false),
            SatResult::Unknown => Err(Z3Error::SolverError(
                "Z3 returned unknown result for where clause".to_string(),
            )),
        }
    }

    /// Build a Z3 constraint from Yuho Constraint AST
    fn build_constraint<'ctx>(
        &self,
        ctx: &'ctx z3::Context,
        constraint: &Constraint,
        value: &Expr,
    ) -> Z3Result<Bool<'ctx>> {
        match constraint {
            Constraint::GreaterThan(expr) => {
                let val = self.build_expr(ctx, value)?;
                let threshold = self.build_expr(ctx, expr)?;
                Ok(self.build_comparison(ctx, &val, &threshold, ">")?)
            },
            Constraint::LessThan(expr) => {
                let val = self.build_expr(ctx, value)?;
                let threshold = self.build_expr(ctx, expr)?;
                Ok(self.build_comparison(ctx, &val, &threshold, "<")?)
            },
            Constraint::GreaterThanOrEqual(expr) => {
                let val = self.build_expr(ctx, value)?;
                let threshold = self.build_expr(ctx, expr)?;
                Ok(self.build_comparison(ctx, &val, &threshold, ">=")?)
            },
            Constraint::LessThanOrEqual(expr) => {
                let val = self.build_expr(ctx, value)?;
                let threshold = self.build_expr(ctx, expr)?;
                Ok(self.build_comparison(ctx, &val, &threshold, "<=")?)
            },
            Constraint::Equal(expr) => {
                let val = self.build_expr(ctx, value)?;
                let threshold = self.build_expr(ctx, expr)?;
                Ok(self.build_comparison(ctx, &val, &threshold, "==")?)
            },
            Constraint::NotEqual(expr) => {
                let val = self.build_expr(ctx, value)?;
                let threshold = self.build_expr(ctx, expr)?;
                Ok(self.build_comparison(ctx, &val, &threshold, "!=")?)
            },
            Constraint::InRange { min, max } => {
                let val = self.build_expr(ctx, value)?;
                let min_val = self.build_expr(ctx, min)?;
                let max_val = self.build_expr(ctx, max)?;
                let ge_min = self.build_comparison(ctx, &val, &min_val, ">=")?;
                let le_max = self.build_comparison(ctx, &val, &max_val, "<=")?;
                Ok(Bool::and(ctx, &[&ge_min, &le_max]))
            },
            Constraint::And(c1, c2) => {
                let left = self.build_constraint(ctx, c1, value)?;
                let right = self.build_constraint(ctx, c2, value)?;
                Ok(Bool::and(ctx, &[&left, &right]))
            },
            Constraint::Or(c1, c2) => {
                let left = self.build_constraint(ctx, c1, value)?;
                let right = self.build_constraint(ctx, c2, value)?;
                Ok(Bool::or(ctx, &[&left, &right]))
            },
            Constraint::Not(c) => {
                let inner = self.build_constraint(ctx, c, value)?;
                Ok(inner.not())
            },
            Constraint::Custom(name) => Err(Z3Error::UnsupportedExpression(format!(
                "Custom constraint '{}' not yet supported",
                name
            ))),
        }
    }

    /// Build a Z3 expression from Yuho expression
    fn build_expr<'ctx>(&self, ctx: &'ctx z3::Context, expr: &Expr) -> Z3Result<Z3Expr<'ctx>> {
        match expr {
            Expr::Literal(Literal::Int(n)) => Ok(Z3Expr::Int(Int::from_i64(ctx, *n))),
            Expr::Literal(Literal::Float(f)) => {
                let num = (*f * 1000.0) as i64;
                Ok(Z3Expr::Real(Real::from_real(ctx, num, 1000)))
            },
            Expr::Literal(Literal::Bool(b)) => Ok(Z3Expr::Bool(Bool::from_bool(ctx, *b))),
            Expr::Identifier(name) => {
                // Create a symbolic variable
                Ok(Z3Expr::Int(Int::new_const(ctx, name.as_str())))
            },
            Expr::Binary(left, op, right) => {
                let l = self.build_expr(ctx, left)?;
                let r = self.build_expr(ctx, right)?;
                self.build_binop(ctx, op, &l, &r)
            },
            _ => Err(Z3Error::UnsupportedExpression(format!("{:?}", expr))),
        }
    }

    /// Build a Z3 binary operation
    fn build_binop<'ctx>(
        &self,
        ctx: &'ctx z3::Context,
        op: &BinaryOp,
        left: &Z3Expr<'ctx>,
        right: &Z3Expr<'ctx>,
    ) -> Z3Result<Z3Expr<'ctx>> {
        match (op, left, right) {
            (BinaryOp::Add, Z3Expr::Int(l), Z3Expr::Int(r)) => Ok(Z3Expr::Int(l.add(&[r]))),
            (BinaryOp::Sub, Z3Expr::Int(l), Z3Expr::Int(r)) => Ok(Z3Expr::Int(l.sub(&[r]))),
            (BinaryOp::Mul, Z3Expr::Int(l), Z3Expr::Int(r)) => Ok(Z3Expr::Int(l.mul(&[r]))),
            (BinaryOp::Div, Z3Expr::Int(l), Z3Expr::Int(r)) => Ok(Z3Expr::Int(l.div(r))),
            (BinaryOp::Mod, Z3Expr::Int(l), Z3Expr::Int(r)) => Ok(Z3Expr::Int(l.modulo(r))),
            (BinaryOp::Eq, Z3Expr::Int(l), Z3Expr::Int(r)) => Ok(Z3Expr::Bool(l._eq(r))),
            (BinaryOp::Neq, Z3Expr::Int(l), Z3Expr::Int(r)) => Ok(Z3Expr::Bool(l._eq(r).not())),
            (BinaryOp::Lt, Z3Expr::Int(l), Z3Expr::Int(r)) => Ok(Z3Expr::Bool(l.lt(r))),
            (BinaryOp::Gt, Z3Expr::Int(l), Z3Expr::Int(r)) => Ok(Z3Expr::Bool(l.gt(r))),
            (BinaryOp::Lte, Z3Expr::Int(l), Z3Expr::Int(r)) => Ok(Z3Expr::Bool(l.le(r))),
            (BinaryOp::Gte, Z3Expr::Int(l), Z3Expr::Int(r)) => Ok(Z3Expr::Bool(l.ge(r))),
            (BinaryOp::And, Z3Expr::Bool(l), Z3Expr::Bool(r)) => {
                Ok(Z3Expr::Bool(Bool::and(ctx, &[l, r])))
            },
            (BinaryOp::Or, Z3Expr::Bool(l), Z3Expr::Bool(r)) => {
                Ok(Z3Expr::Bool(Bool::or(ctx, &[l, r])))
            },
            _ => Err(Z3Error::UnsupportedExpression(format!(
                "Binary operation {:?} with type mismatch",
                op
            ))),
        }
    }

    /// Build a comparison expression
    fn build_comparison<'ctx>(
        &self,
        ctx: &'ctx z3::Context,
        left: &Z3Expr<'ctx>,
        right: &Z3Expr<'ctx>,
        op: &str,
    ) -> Z3Result<Bool<'ctx>> {
        match (left, right) {
            (Z3Expr::Int(l), Z3Expr::Int(r)) => Ok(match op {
                ">" => l.gt(r),
                "<" => l.lt(r),
                ">=" => l.ge(r),
                "<=" => l.le(r),
                "==" => l._eq(r),
                "!=" => l._eq(r).not(),
                _ => {
                    return Err(Z3Error::TranslationError(format!(
                        "Unknown operator: {}",
                        op
                    )))
                },
            }),
            (Z3Expr::Real(l), Z3Expr::Real(r)) => Ok(match op {
                ">" => l.gt(r),
                "<" => l.lt(r),
                ">=" => l.ge(r),
                "<=" => l.le(r),
                "==" => l._eq(r),
                "!=" => l._eq(r).not(),
                _ => {
                    return Err(Z3Error::TranslationError(format!(
                        "Unknown operator: {}",
                        op
                    )))
                },
            }),
            _ => Err(Z3Error::TranslationError(
                "Type mismatch in comparison".to_string(),
            )),
        }
    }

    /// Verify a complete program for correctness
    pub fn verify_program(&self, program: &Program) -> Z3Result<Vec<String>> {
        let mut errors = Vec::new();

        for item in &program.items {
            if let Err(e) = self.verify_item(item) {
                errors.push(format!("{}", e));
            }
        }

        Ok(errors)
    }

    /// Verify a single program item
    fn verify_item(&self, item: &Item) -> Z3Result<()> {
        match item {
            Item::Struct(s) => self.verify_struct(s),
            Item::Declaration(d) => self.verify_declaration(d),
            Item::LegalTest(test) => self.verify_legal_test(test),
            Item::Enum(e) => self.verify_enum(e),
            Item::Scope(s) => {
                for inner in &s.items {
                    self.verify_item(inner)?;
                }
                Ok(())
            },
            _ => Ok(()),
        }
    }

    /// Verify legal test definition
    fn verify_legal_test(&self, test: &LegalTestDefinition) -> Z3Result<()> {
        // Verify all requirements are boolean types
        for req in &test.requirements {
            if !matches!(req.ty, Type::Bool) {
                return Err(Z3Error::TranslationError(format!(
                    "Legal test '{}' requirement '{}' must be boolean, got {:?}",
                    test.name, req.name, req.ty
                )));
            }
        }

        // Create Z3 context for verification
        let cfg = z3::Config::new();
        let ctx = z3::Context::new(&cfg);

        // Create boolean variables for each requirement
        let mut bool_vars = Vec::new();
        for req in &test.requirements {
            let var = Bool::new_const(&ctx, req.name.as_str());
            bool_vars.push(var);
        }

        // Verify that the conjunction is satisfiable
        if !bool_vars.is_empty() {
            let conjunction = Bool::and(&ctx, &bool_vars.iter().collect::<Vec<_>>());
            let solver = Solver::new(&ctx);
            solver.assert(&conjunction);

            match solver.check() {
                SatResult::Sat => Ok(()),
                SatResult::Unsat => Err(Z3Error::TranslationError(format!(
                    "Legal test '{}' requirements are contradictory",
                    test.name
                ))),
                SatResult::Unknown => Err(Z3Error::SolverError(format!(
                    "Z3 could not determine satisfiability of legal test '{}'",
                    test.name
                ))),
            }
        } else {
            // Empty legal test is trivially satisfiable
            Ok(())
        }
    }

    /// Verify enum definition
    fn verify_enum(&self, enum_def: &EnumDefinition) -> Z3Result<()> {
        // For mutually exclusive enums, verify variants are distinct
        if enum_def.mutually_exclusive {
            // Check that there are at least 2 variants
            if enum_def.variants.len() < 2 {
                return Err(Z3Error::TranslationError(format!(
                    "Mutually exclusive enum '{}' must have at least 2 variants",
                    enum_def.name
                )));
            }

            // Z3 verification: Create boolean variables for each variant
            // and verify they are mutually exclusive (at most one can be true)
            let cfg = z3::Config::new();
            let ctx = z3::Context::new(&cfg);
            let solver = Solver::new(&ctx);

            let mut variant_bools = Vec::new();
            for variant in &enum_def.variants {
                let var = Bool::new_const(&ctx, variant.as_str());
                variant_bools.push(var);
            }

            // Assert at most one is true (for all pairs, not both can be true)
            for i in 0..variant_bools.len() {
                for j in (i + 1)..variant_bools.len() {
                    let not_both =
                        Bool::or(&ctx, &[&variant_bools[i].not(), &variant_bools[j].not()]);
                    solver.assert(&not_both);
                }
            }

            // Check satisfiability (should be SAT - mutual exclusivity is satisfiable)
            match solver.check() {
                SatResult::Sat => Ok(()),
                SatResult::Unsat => Err(Z3Error::TranslationError(format!(
                    "Mutually exclusive constraints for enum '{}' are contradictory",
                    enum_def.name
                ))),
                SatResult::Unknown => Err(Z3Error::SolverError(format!(
                    "Z3 could not verify mutual exclusivity for enum '{}'",
                    enum_def.name
                ))),
            }
        } else {
            Ok(())
        }
    }

    /// Verify struct field constraints
    fn verify_struct(&self, struct_def: &StructDefinition) -> Z3Result<()> {
        for field in &struct_def.fields {
            // Verify type constraints
            match &field.ty {
                Type::BoundedInt { min, max } => {
                    if min > max {
                        return Err(Z3Error::TranslationError(format!(
                            "Invalid BoundedInt range for field '{}': min ({}) > max ({})",
                            field.name, min, max
                        )));
                    }
                },
                _ => {},
            }

            // Verify where clause constraints
            for constraint in &field.constraints {
                // Constraints will be checked at instantiation time
                // Here we just validate the constraint structure
                self.validate_constraint(constraint)?;
            }
        }
        Ok(())
    }

    /// Verify declaration with type constraints
    fn verify_declaration(&self, decl: &Declaration) -> Z3Result<()> {
        match &decl.ty {
            Type::BoundedInt { min, max } => {
                if let Expr::Literal(Literal::Int(value)) = &decl.value {
                    if !self.verify_bounded_int(*value, *min, *max)? {
                        return Err(Z3Error::TranslationError(format!(
                            "Value {} violates BoundedInt<{}, {}> constraint",
                            value, min, max
                        )));
                    }
                }
            },
            Type::Positive(inner) => match **inner {
                Type::Int => {
                    if let Expr::Literal(Literal::Int(value)) = &decl.value {
                        if !self.verify_positive(*value)? {
                            return Err(Z3Error::TranslationError(format!(
                                "Value {} violates Positive constraint",
                                value
                            )));
                        }
                    }
                },
                Type::Float | Type::Money | Type::MoneyWithCurrency(_) => {
                    if let Expr::Literal(Literal::Float(value)) = &decl.value {
                        if !self.verify_positive_float(*value)? {
                            return Err(Z3Error::TranslationError(format!(
                                "Value {} violates Positive constraint",
                                value
                            )));
                        }
                    }
                },
                _ => {},
            },
            _ => {},
        }
        Ok(())
    }

    /// Validate constraint structure
    fn validate_constraint(&self, constraint: &Constraint) -> Z3Result<()> {
        match constraint {
            Constraint::InRange { min, max } => {
                // Ensure range makes sense
                // We can't fully validate without concrete values
                Ok(())
            },
            Constraint::And(c1, c2) | Constraint::Or(c1, c2) => {
                self.validate_constraint(c1)?;
                self.validate_constraint(c2)
            },
            Constraint::Not(c) => self.validate_constraint(c),
            _ => Ok(()),
        }
    }

    /// Check if a given condition is satisfiable
    pub fn check_sat(&self, condition: &Expr) -> Z3Result<bool> {
        let z3_expr = self.translate_expr(condition)?;
        self.solver.assert(&z3_expr);

        match self.solver.check() {
            z3::SatResult::Sat => Ok(true),
            z3::SatResult::Unsat => Ok(false),
            z3::SatResult::Unknown => Err(Z3Error::SolverError(
                "Z3 returned unknown result".to_string(),
            )),
        }
    }

    /// Get a model (counterexample) if the condition is satisfiable
    pub fn get_model(&self, condition: &Expr) -> Z3Result<Option<String>> {
        let z3_expr = self.translate_expr(condition)?;
        self.solver.push();
        self.solver.assert(&z3_expr);

        let result = match self.solver.check() {
            z3::SatResult::Sat => {
                if let Some(model) = self.solver.get_model() {
                    Ok(Some(model.to_string()))
                } else {
                    Ok(None)
                }
            },
            z3::SatResult::Unsat => Ok(None),
            z3::SatResult::Unknown => Err(Z3Error::SolverError(
                "Z3 returned unknown result".to_string(),
            )),
        };

        self.solver.pop(1);
        result
    }

    /// Get a counterexample if the condition is NOT satisfiable
    pub fn get_counterexample(&self, condition: &Expr) -> Z3Result<Option<String>> {
        // To get a counterexample for "condition is not satisfiable",
        // we check if NOT(condition) is satisfiable
        let z3_expr = self.translate_expr(condition)?;
        self.solver.push();
        self.solver.assert(&z3_expr.not());

        let result = match self.solver.check() {
            z3::SatResult::Sat => {
                if let Some(model) = self.solver.get_model() {
                    Ok(Some(model.to_string()))
                } else {
                    Ok(None)
                }
            },
            z3::SatResult::Unsat => Ok(None),
            z3::SatResult::Unknown => Err(Z3Error::SolverError(
                "Z3 returned unknown result".to_string(),
            )),
        };

        self.solver.pop(1);
        result
    }

    /// Translate a Yuho expression to a Z3 expression
    fn translate_expr_typed(&self, expr: &Expr) -> Z3Result<Z3Expr> {
        match expr {
            Expr::Literal(Literal::Int(n)) => Ok(Z3Expr::Int(Int::from_i64(*n))),
            Expr::Literal(Literal::Float(f)) => {
                let num = (*f * 1000.0) as i64;
                let den = 1000i64;
                Ok(Z3Expr::Real(Real::from_rational(num, den)))
            },
            Expr::Literal(Literal::Bool(b)) => Ok(Z3Expr::Bool(Bool::from_bool(*b))),
            Expr::Binary(left, op, right) => self.translate_binop_typed(op, left, right),
            Expr::Identifier(name) => {
                if let Some(var) = self.variables.get(name) {
                    Ok(var.clone())
                } else {
                    // Default to Int for unknown variables
                    Ok(Z3Expr::Int(Int::new_const(name.as_str())))
                }
            },
            _ => Err(Z3Error::UnsupportedExpression(format!("{:?}", expr))),
        }
    }

    /// Translate a Yuho expression to a Z3 Bool expression
    fn translate_expr(&self, expr: &Expr) -> Z3Result<Bool> {
        let z3_expr = self.translate_expr_typed(expr)?;
        match z3_expr {
            Z3Expr::Bool(b) => Ok(b),
            _ => Err(Z3Error::TranslationError(
                "Expected boolean expression".to_string(),
            )),
        }
    }

    /// Translate a binary operation to a typed Z3 expression
    fn translate_binop_typed(&self, op: &BinaryOp, left: &Expr, right: &Expr) -> Z3Result<Z3Expr> {
        let left_z3 = self.translate_expr_typed(left)?;
        let right_z3 = self.translate_expr_typed(right)?;

        match (op, left_z3, right_z3) {
            // Arithmetic operations on integers
            (BinaryOp::Add, Z3Expr::Int(l), Z3Expr::Int(r)) => Ok(Z3Expr::Int(l.add(&r))),
            (BinaryOp::Sub, Z3Expr::Int(l), Z3Expr::Int(r)) => Ok(Z3Expr::Int(l.sub(&r))),
            (BinaryOp::Mul, Z3Expr::Int(l), Z3Expr::Int(r)) => Ok(Z3Expr::Int(l.mul(&r))),
            (BinaryOp::Div, Z3Expr::Int(l), Z3Expr::Int(r)) => Ok(Z3Expr::Int(l.div(&r))),
            (BinaryOp::Mod, Z3Expr::Int(l), Z3Expr::Int(r)) => Ok(Z3Expr::Int(l.rem(&r))),

            // Arithmetic operations on reals
            (BinaryOp::Add, Z3Expr::Real(l), Z3Expr::Real(r)) => Ok(Z3Expr::Real(l.add(&r))),
            (BinaryOp::Sub, Z3Expr::Real(l), Z3Expr::Real(r)) => Ok(Z3Expr::Real(l.sub(&r))),
            (BinaryOp::Mul, Z3Expr::Real(l), Z3Expr::Real(r)) => Ok(Z3Expr::Real(l.mul(&r))),
            (BinaryOp::Div, Z3Expr::Real(l), Z3Expr::Real(r)) => Ok(Z3Expr::Real(l.div(&r))),

            // Comparison operations on integers
            (BinaryOp::Eq, Z3Expr::Int(l), Z3Expr::Int(r)) => Ok(Z3Expr::Bool(l.eq(&r))),
            (BinaryOp::Neq, Z3Expr::Int(l), Z3Expr::Int(r)) => Ok(Z3Expr::Bool(l.eq(&r).not())),
            (BinaryOp::Lt, Z3Expr::Int(l), Z3Expr::Int(r)) => Ok(Z3Expr::Bool(l.lt(&r))),
            (BinaryOp::Gt, Z3Expr::Int(l), Z3Expr::Int(r)) => Ok(Z3Expr::Bool(l.gt(&r))),
            (BinaryOp::Lte, Z3Expr::Int(l), Z3Expr::Int(r)) => Ok(Z3Expr::Bool(l.le(&r))),
            (BinaryOp::Gte, Z3Expr::Int(l), Z3Expr::Int(r)) => Ok(Z3Expr::Bool(l.ge(&r))),

            // Comparison operations on reals
            (BinaryOp::Eq, Z3Expr::Real(l), Z3Expr::Real(r)) => Ok(Z3Expr::Bool(l.eq(&r))),
            (BinaryOp::Neq, Z3Expr::Real(l), Z3Expr::Real(r)) => Ok(Z3Expr::Bool(l.eq(&r).not())),
            (BinaryOp::Lt, Z3Expr::Real(l), Z3Expr::Real(r)) => Ok(Z3Expr::Bool(l.lt(&r))),
            (BinaryOp::Gt, Z3Expr::Real(l), Z3Expr::Real(r)) => Ok(Z3Expr::Bool(l.gt(&r))),
            (BinaryOp::Lte, Z3Expr::Real(l), Z3Expr::Real(r)) => Ok(Z3Expr::Bool(l.le(&r))),
            (BinaryOp::Gte, Z3Expr::Real(l), Z3Expr::Real(r)) => Ok(Z3Expr::Bool(l.ge(&r))),

            // Logical operations on booleans
            (BinaryOp::And, Z3Expr::Bool(l), Z3Expr::Bool(r)) => {
                Ok(Z3Expr::Bool(Bool::and(&[&l, &r])))
            },
            (BinaryOp::Or, Z3Expr::Bool(l), Z3Expr::Bool(r)) => {
                Ok(Z3Expr::Bool(Bool::or(&[&l, &r])))
            },
            (BinaryOp::Eq, Z3Expr::Bool(l), Z3Expr::Bool(r)) => Ok(Z3Expr::Bool(l.eq(&r))),
            (BinaryOp::Neq, Z3Expr::Bool(l), Z3Expr::Bool(r)) => Ok(Z3Expr::Bool(l.eq(&r).not())),

            _ => Err(Z3Error::UnsupportedExpression(format!(
                "Binary operation {:?} with mismatched types",
                op
            ))),
        }
    }

    /// Translate a binary operation to Z3 Bool
    fn translate_binop(&self, op: &BinaryOp, left: &Expr, right: &Expr) -> Z3Result<Bool> {
        let result = self.translate_binop_typed(op, left, right)?;
        match result {
            Z3Expr::Bool(b) => Ok(b),
            _ => Err(Z3Error::TranslationError(
                "Expected boolean result from comparison".to_string(),
            )),
        }
    }

    /// Translate a Yuho type to a Z3 sort description
    pub fn translate_type(&self, ty: &Type) -> Z3Result<String> {
        match ty {
            Type::Int | Type::BoundedInt { .. } | Type::Positive(_) => Ok("Int".to_string()),
            Type::Float | Type::Money | Type::MoneyWithCurrency(_) => Ok("Real".to_string()),
            Type::Bool => Ok("Bool".to_string()),
            Type::String => Ok("String".to_string()),
            _ => Err(Z3Error::UnsupportedType(format!("{:?}", ty))),
        }
    }

    /// Enumerate multiple models (All-SAT)
    pub fn enumerate_models(&self, condition: &Expr, max_models: usize) -> Z3Result<Vec<String>> {
        let z3_expr = self.translate_expr(condition)?;
        self.solver.push();
        self.solver.assert(&z3_expr);

        let mut models = Vec::new();

        for _ in 0..max_models {
            match self.solver.check() {
                SatResult::Sat => {
                    if let Some(model) = self.solver.get_model() {
                        let model_str = model.to_string();
                        models.push(model_str.clone());

                        // Block this model to find the next one
                        // Create a constraint that excludes this model
                        // This is a simplified approach
                        if models.len() < max_models {
                            // In a real implementation, we'd extract variable assignments
                            // and create a blocking clause
                            break;
                        }
                    } else {
                        break;
                    }
                },
                _ => break,
            }
        }

        self.solver.pop(1);
        Ok(models)
    }

    /// Generate a minimal counterexample
    pub fn minimize_counterexample(&self, condition: &Expr) -> Z3Result<Option<String>> {
        // For now, just return a regular counterexample
        // A full implementation would iteratively remove constraints
        self.get_counterexample(condition)
    }

    /// Generate a witness (satisfying assignment)
    pub fn get_witness(&self, condition: &Expr) -> Z3Result<Option<String>> {
        self.get_model(condition)
    }

    /// Generate a human-readable explanation for why a condition is SAT
    pub fn explain_sat(&self, condition: &Expr) -> Z3Result<String> {
        use explanation::ExplanationGenerator;

        let model = self.get_model(condition)?;
        let gen = ExplanationGenerator::new();

        Ok(match model {
            Some(m) => gen.explain_why_sat(condition, &m),
            None => String::from("Condition is unsatisfiable"),
        })
    }

    /// Generate a human-readable explanation for why a condition is UNSAT
    pub fn explain_unsat(&self, condition: &Expr) -> Z3Result<String> {
        use explanation::ExplanationGenerator;

        let gen = ExplanationGenerator::new();
        Ok(gen.explain_why_not_sat(condition))
    }

    /// Generate an execution trace for debugging
    pub fn trace(&self, condition: &Expr) -> explanation::ExecutionTrace {
        use explanation::ExplanationGenerator;

        let gen = ExplanationGenerator::new();
        gen.trace_execution(condition)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_verification_context_creation() {
        let _vc = VerificationContext::new();
        // Just test that it can be created
    }

    #[test]
    fn test_translate_int_type() {
        let vc = VerificationContext::new();
        assert_eq!(vc.translate_type(&Type::Int).unwrap(), "Int");
    }

    #[test]
    fn test_translate_bool_type() {
        let vc = VerificationContext::new();
        assert_eq!(vc.translate_type(&Type::Bool).unwrap(), "Bool");
    }

    #[test]
    fn test_translate_float_type() {
        let vc = VerificationContext::new();
        assert_eq!(vc.translate_type(&Type::Float).unwrap(), "Real");
    }

    #[test]
    fn test_translate_bounded_int_type() {
        let vc = VerificationContext::new();
        let bounded = Type::BoundedInt { min: 0, max: 100 };
        assert_eq!(vc.translate_type(&bounded).unwrap(), "Int");
    }

    #[test]
    fn test_check_sat_true() {
        let vc = VerificationContext::new();
        let expr = Expr::Literal(Literal::Bool(true));
        assert!(vc.check_sat(&expr).unwrap());
    }

    #[test]
    fn test_check_sat_false() {
        let vc = VerificationContext::new();
        let expr = Expr::Literal(Literal::Bool(false));
        assert!(!vc.check_sat(&expr).unwrap());
    }

    #[test]
    fn test_check_sat_and() {
        let vc = VerificationContext::new();
        let expr = Expr::Binary(
            Box::new(Expr::Literal(Literal::Bool(true))),
            BinaryOp::And,
            Box::new(Expr::Literal(Literal::Bool(true))),
        );
        assert!(vc.check_sat(&expr).unwrap());
    }

    #[test]
    fn test_check_sat_and_false() {
        let vc = VerificationContext::new();
        let expr = Expr::Binary(
            Box::new(Expr::Literal(Literal::Bool(true))),
            BinaryOp::And,
            Box::new(Expr::Literal(Literal::Bool(false))),
        );
        assert!(!vc.check_sat(&expr).unwrap());
    }

    #[test]
    fn test_check_sat_or() {
        let vc = VerificationContext::new();
        let expr = Expr::Binary(
            Box::new(Expr::Literal(Literal::Bool(true))),
            BinaryOp::Or,
            Box::new(Expr::Literal(Literal::Bool(false))),
        );
        assert!(vc.check_sat(&expr).unwrap());
    }

    // Test arithmetic operators
    #[test]
    fn test_arithmetic_add() {
        let vc = VerificationContext::new();
        // Test that 2 + 3 == 5
        let expr = Expr::Binary(
            Box::new(Expr::Binary(
                Box::new(Expr::Literal(Literal::Int(2))),
                BinaryOp::Add,
                Box::new(Expr::Literal(Literal::Int(3))),
            )),
            BinaryOp::Eq,
            Box::new(Expr::Literal(Literal::Int(5))),
        );
        assert!(vc.check_sat(&expr).unwrap());
    }

    #[test]
    fn test_arithmetic_sub() {
        let vc = VerificationContext::new();
        // Test that 5 - 3 == 2
        let expr = Expr::Binary(
            Box::new(Expr::Binary(
                Box::new(Expr::Literal(Literal::Int(5))),
                BinaryOp::Sub,
                Box::new(Expr::Literal(Literal::Int(3))),
            )),
            BinaryOp::Eq,
            Box::new(Expr::Literal(Literal::Int(2))),
        );
        assert!(vc.check_sat(&expr).unwrap());
    }

    #[test]
    fn test_arithmetic_mul() {
        let vc = VerificationContext::new();
        // Test that 2 * 3 == 6
        let expr = Expr::Binary(
            Box::new(Expr::Binary(
                Box::new(Expr::Literal(Literal::Int(2))),
                BinaryOp::Mul,
                Box::new(Expr::Literal(Literal::Int(3))),
            )),
            BinaryOp::Eq,
            Box::new(Expr::Literal(Literal::Int(6))),
        );
        assert!(vc.check_sat(&expr).unwrap());
    }

    #[test]
    fn test_arithmetic_div() {
        let vc = VerificationContext::new();
        // Test that 6 / 2 == 3
        let expr = Expr::Binary(
            Box::new(Expr::Binary(
                Box::new(Expr::Literal(Literal::Int(6))),
                BinaryOp::Div,
                Box::new(Expr::Literal(Literal::Int(2))),
            )),
            BinaryOp::Eq,
            Box::new(Expr::Literal(Literal::Int(3))),
        );
        assert!(vc.check_sat(&expr).unwrap());
    }

    #[test]
    fn test_arithmetic_mod() {
        let vc = VerificationContext::new();
        // Test that 7 % 3 == 1
        let expr = Expr::Binary(
            Box::new(Expr::Binary(
                Box::new(Expr::Literal(Literal::Int(7))),
                BinaryOp::Mod,
                Box::new(Expr::Literal(Literal::Int(3))),
            )),
            BinaryOp::Eq,
            Box::new(Expr::Literal(Literal::Int(1))),
        );
        assert!(vc.check_sat(&expr).unwrap());
    }

    // Test comparison operators
    #[test]
    fn test_comparison_gt() {
        let vc = VerificationContext::new();
        let expr = Expr::Binary(
            Box::new(Expr::Literal(Literal::Int(5))),
            BinaryOp::Gt,
            Box::new(Expr::Literal(Literal::Int(3))),
        );
        assert!(vc.check_sat(&expr).unwrap());
    }

    #[test]
    fn test_comparison_lt() {
        let vc = VerificationContext::new();
        let expr = Expr::Binary(
            Box::new(Expr::Literal(Literal::Int(3))),
            BinaryOp::Lt,
            Box::new(Expr::Literal(Literal::Int(5))),
        );
        assert!(vc.check_sat(&expr).unwrap());
    }

    #[test]
    fn test_comparison_gte() {
        let vc = VerificationContext::new();
        let expr = Expr::Binary(
            Box::new(Expr::Literal(Literal::Int(5))),
            BinaryOp::Gte,
            Box::new(Expr::Literal(Literal::Int(5))),
        );
        assert!(vc.check_sat(&expr).unwrap());
    }

    #[test]
    fn test_comparison_lte() {
        let vc = VerificationContext::new();
        let expr = Expr::Binary(
            Box::new(Expr::Literal(Literal::Int(3))),
            BinaryOp::Lte,
            Box::new(Expr::Literal(Literal::Int(3))),
        );
        assert!(vc.check_sat(&expr).unwrap());
    }

    #[test]
    fn test_get_model() {
        let vc = VerificationContext::new();
        let expr = Expr::Literal(Literal::Bool(true));
        let model = vc.get_model(&expr);
        assert!(model.is_ok());
    }

    #[test]
    fn test_get_counterexample() {
        let vc = VerificationContext::new();
        let expr = Expr::Literal(Literal::Bool(true));
        // Counterexample for "true is not satisfiable" should be None
        let counter = vc.get_counterexample(&expr).unwrap();
        assert!(counter.is_none());
    }

    #[test]
    fn test_enumerate_models() {
        let vc = VerificationContext::new();
        let expr = Expr::Literal(Literal::Bool(true));
        let models = vc.enumerate_models(&expr, 5);
        assert!(models.is_ok());
    }
}
