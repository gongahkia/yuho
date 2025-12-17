//! Enhanced explanation generation for principle verification results

use yuho_core::ast::*;

/// Generate human-readable explanation of a principle
pub fn explain_principle(principle: &PrincipleDefinition) -> String {
    let mut explainer = PrincipleExplainer::new();
    explainer.explain(&principle.body, &principle.name)
}

struct PrincipleExplainer {
    depth: usize,
}

impl PrincipleExplainer {
    fn new() -> Self {
        Self { depth: 0 }
    }

    fn explain(&mut self, expr: &Expr, principle_name: &str) -> String {
        let body_explanation = self.explain_expr(expr);

        format!(
            "Principle '{}' states that:\n\n{}",
            principle_name, body_explanation
        )
    }

    fn explain_expr(&mut self, expr: &Expr) -> String {
        match expr {
            Expr::Forall { var, ty, body } => {
                self.depth += 1;
                let indent = "  ".repeat(self.depth);
                let type_name = self.type_name(ty);
                let body_exp = self.explain_expr(body);
                self.depth -= 1;

                format!(
                    "{}For all {} of type {},\n{}",
                    indent, var, type_name, body_exp
                )
            },
            Expr::Exists { var, ty, body } => {
                self.depth += 1;
                let indent = "  ".repeat(self.depth);
                let type_name = self.type_name(ty);
                let body_exp = self.explain_expr(body);
                self.depth -= 1;

                format!(
                    "{}There exists a {} of type {} such that\n{}",
                    indent, var, type_name, body_exp
                )
            },
            Expr::Binary(left, op, right) => {
                let indent = "  ".repeat(self.depth + 1);
                let left_exp = self.explain_simple_expr(left);
                let right_exp = self.explain_simple_expr(right);
                let op_exp = self.binary_op_name(op);

                format!("{}{} {} {}", indent, left_exp, op_exp, right_exp)
            },
            _ => {
                let indent = "  ".repeat(self.depth + 1);
                format!("{}{:?}", indent, expr)
            },
        }
    }

    fn explain_simple_expr(&self, expr: &Expr) -> String {
        match expr {
            Expr::Identifier(name) => name.clone(),
            Expr::Literal(lit) => format!("{:?}", lit),
            Expr::FieldAccess(base, field) => {
                format!("{}.{}", self.explain_simple_expr(base), field)
            },
            Expr::Binary(left, op, right) => {
                format!(
                    "({} {} {})",
                    self.explain_simple_expr(left),
                    self.binary_op_name(op),
                    self.explain_simple_expr(right)
                )
            },
            _ => format!("{:?}", expr),
        }
    }

    fn type_name(&self, ty: &Type) -> &str {
        match ty {
            Type::Int => "integer",
            Type::Bool => "boolean",
            Type::String => "string",
            Type::Float => "floating-point number",
            Type::Named(n) => n,
            _ => "value",
        }
    }

    fn binary_op_name(&self, op: &BinaryOp) -> &str {
        match op {
            BinaryOp::Add => "+",
            BinaryOp::Sub => "-",
            BinaryOp::Mul => "*",
            BinaryOp::Div => "/",
            BinaryOp::Mod => "%",
            BinaryOp::Eq => "==",
            BinaryOp::Neq => "!=",
            BinaryOp::Lt => "<",
            BinaryOp::Gt => ">",
            BinaryOp::Lte => "<=",
            BinaryOp::Gte => ">=",
            BinaryOp::And => "and",
            BinaryOp::Or => "or",
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_explain_simple_principle() {
        let principle = PrincipleDefinition {
            name: "AllPositive".to_string(),
            body: Expr::Forall {
                var: "x".to_string(),
                ty: Type::Int,
                body: Box::new(Expr::Binary(
                    Box::new(Expr::Identifier("x".to_string())),
                    BinaryOp::Gt,
                    Box::new(Expr::Literal(Literal::Int(0))),
                )),
            },
            span: Span { start: 0, end: 0 },
        };

        let explanation = explain_principle(&principle);
        assert!(explanation.contains("For all"));
        assert!(explanation.contains("integer"));
        assert!(explanation.contains(">"));
    }
}
