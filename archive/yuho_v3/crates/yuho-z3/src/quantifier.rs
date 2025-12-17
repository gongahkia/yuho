//! Z3 quantifier translation module
//!
//! Translates Yuho forall/exists expressions to Z3 quantified formulas

use crate::{Z3Error, Z3Result};
use yuho_core::ast::*;

/// Translate a Yuho principle to Z3 SMT formula
pub fn translate_principle_to_z3(principle: &PrincipleDefinition) -> Z3Result<String> {
    let mut translator = QuantifierTranslator::new();
    translator.translate_expr(&principle.body)
}

struct QuantifierTranslator {
    depth: usize,
    var_counter: usize,
}

impl QuantifierTranslator {
    fn new() -> Self {
        Self {
            depth: 0,
            var_counter: 0,
        }
    }

    fn translate_expr(&mut self, expr: &Expr) -> Z3Result<String> {
        match expr {
            Expr::Forall { var, ty, body } => {
                self.depth += 1;
                let type_str = self.translate_type(ty)?;
                let body_str = self.translate_expr(body)?;
                self.depth -= 1;

                Ok(format!("(forall (({} {})) {})", var, type_str, body_str))
            },
            Expr::Exists { var, ty, body } => {
                self.depth += 1;
                let type_str = self.translate_type(ty)?;
                let body_str = self.translate_expr(body)?;
                self.depth -= 1;

                Ok(format!("(exists (({} {})) {})", var, type_str, body_str))
            },
            Expr::Binary(left, op, right) => {
                let left_str = self.translate_expr(left)?;
                let right_str = self.translate_expr(right)?;
                let op_str = self.translate_binary_op(op)?;

                Ok(format!("({} {} {})", op_str, left_str, right_str))
            },
            Expr::Unary(op, expr) => {
                let expr_str = self.translate_expr(expr)?;
                let op_str = self.translate_unary_op(op)?;

                Ok(format!("({} {})", op_str, expr_str))
            },
            Expr::Identifier(name) => Ok(name.clone()),
            Expr::Literal(lit) => self.translate_literal(lit),
            Expr::FieldAccess(base, field) => {
                let base_str = self.translate_expr(base)?;
                Ok(format!("(select {} {})", base_str, field))
            },
            Expr::Call(func, args) => {
                let arg_strs: Result<Vec<_>, _> =
                    args.iter().map(|a| self.translate_expr(a)).collect();
                let arg_strs = arg_strs?;

                Ok(format!("({} {})", func, arg_strs.join(" ")))
            },
            _ => Err(Z3Error::UnsupportedExpression(format!(
                "Expression type not yet supported in Z3 translation: {:?}",
                expr
            ))),
        }
    }

    fn translate_type(&self, ty: &Type) -> Z3Result<String> {
        match ty {
            Type::Int => Ok("Int".to_string()),
            Type::Bool => Ok("Bool".to_string()),
            Type::Float => Ok("Real".to_string()),
            Type::String => Ok("String".to_string()),
            Type::BoundedInt { .. } => Ok("Int".to_string()),
            Type::Positive(_) => Ok("Int".to_string()),
            Type::Named(name) => Ok(name.clone()),
            _ => Err(Z3Error::UnsupportedType(format!(
                "Type not supported in Z3 translation: {:?}",
                ty
            ))),
        }
    }

    fn translate_binary_op(&self, op: &BinaryOp) -> Z3Result<String> {
        Ok(match op {
            BinaryOp::Add => "+",
            BinaryOp::Sub => "-",
            BinaryOp::Mul => "*",
            BinaryOp::Div => "div",
            BinaryOp::Mod => "mod",
            BinaryOp::Eq => "=",
            BinaryOp::Neq => "distinct",
            BinaryOp::Lt => "<",
            BinaryOp::Gt => ">",
            BinaryOp::Lte => "<=",
            BinaryOp::Gte => ">=",
            BinaryOp::And => "and",
            BinaryOp::Or => "or",
        }
        .to_string())
    }

    fn translate_unary_op(&self, op: &UnaryOp) -> Z3Result<String> {
        Ok(match op {
            UnaryOp::Not => "not",
            UnaryOp::Neg => "-",
        }
        .to_string())
    }

    fn translate_literal(&self, lit: &Literal) -> Z3Result<String> {
        Ok(match lit {
            Literal::Int(n) => n.to_string(),
            Literal::Bool(b) => b.to_string(),
            Literal::Float(f) => f.to_string(),
            Literal::String(s) => format!("\"{}\"", s),
            Literal::Pass => "null".to_string(),
            _ => {
                return Err(Z3Error::UnsupportedExpression(format!(
                    "Literal type not supported: {:?}",
                    lit
                )))
            },
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_simple_forall() {
        let principle = PrincipleDefinition {
            name: "Test".to_string(),
            body: Expr::Forall {
                var: "x".to_string(),
                ty: Type::Int,
                body: Box::new(Expr::Binary(
                    Box::new(Expr::Identifier("x".to_string())),
                    BinaryOp::Gt,
                    Box::new(Expr::Literal(Literal::Int(0))),
                )),
            },
            span: yuho_core::ast::Span { start: 0, end: 0 },
        };

        let result = translate_principle_to_z3(&principle);
        assert!(result.is_ok());
        let smt = result.unwrap();
        assert!(smt.contains("forall"));
        assert!(smt.contains("Int"));
    }
}
