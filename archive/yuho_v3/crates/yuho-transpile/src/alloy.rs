use yuho_core::ast::*;

/// Generate Alloy formal specification from Yuho program
pub fn to_alloy(program: &Program) -> String {
    let mut gen = AlloyGenerator::new();
    gen.generate(program)
}

struct AlloyGenerator {
    output: String,
    indent: usize,
}

impl AlloyGenerator {
    fn new() -> Self {
        Self {
            output: String::new(),
            indent: 0,
        }
    }

    fn line(&mut self, s: &str) {
        let indent = "  ".repeat(self.indent);
        self.output.push_str(&format!("{}{}\n", indent, s));
    }

    fn blank(&mut self) {
        self.output.push('\n');
    }

    fn generate(&mut self, program: &Program) -> String {
        self.line("// Alloy specification generated from Yuho");
        self.line("// Use Alloy Analyzer to verify properties");
        self.blank();

        // Emit signatures for structs
        for item in &program.items {
            self.emit_item(item);
        }

        std::mem::take(&mut self.output)
    }

    fn emit_item(&mut self, item: &Item) {
        match item {
            Item::Struct(s) => self.emit_struct(s),
            Item::Enum(e) => self.emit_enum(e),
            Item::Scope(s) => self.emit_scope(s),
            Item::Function(f) => self.emit_function(f),
            Item::Declaration(d) => self.emit_declaration(d),
            Item::TypeAlias(_) => {
                // Type aliases are compile-time only, don't emit in Alloy
            },
            Item::LegalTest(test) => self.emit_legal_test(test),
            Item::ConflictCheck(_) => {
                // Conflict checks are compile-time directives
            },
            Item::Principle(_) => {},
            Item::Proviso(_) => {
                // Proviso clauses are treated as compile-time directives
            },
            Item::Proviso(_) => { // For now, principles are not transpiled to this target
                 // Full Z3 verification support coming in future commits
            },
        }
    }

    fn emit_struct(&mut self, s: &StructDefinition) {
        self.line(&format!("sig {} {{", s.name));
        self.indent += 1;

        for (i, field) in s.fields.iter().enumerate() {
            let alloy_type = self.type_to_alloy(&field.ty);
            let comma = if i < s.fields.len() - 1 { "," } else { "" };
            self.line(&format!("{}: {}{}", field.name, alloy_type, comma));
        }

        self.indent -= 1;
        self.line("}");

        // Generate constraints for dependent types
        let constraints = self.collect_struct_constraints(s);
        if !constraints.is_empty() {
            self.line("{");
            self.indent += 1;
            for constraint in constraints {
                self.line(&constraint);
            }
            self.indent -= 1;
            self.line("}");
        }

        self.blank();
    }

    fn collect_struct_constraints(&self, s: &StructDefinition) -> Vec<String> {
        let mut constraints = Vec::new();

        for field in &s.fields {
            match &field.ty {
                Type::BoundedInt { min, max } => {
                    constraints.push(format!(
                        "{} >= {} and {} <= {}",
                        field.name, min, field.name, max
                    ));
                },
                Type::Positive(_) => {
                    constraints.push(format!("{} > 0", field.name));
                },
                Type::ValidDate { after, before } => {
                    if let Some(after_date) = after {
                        constraints.push(format!("{} > \"{}\"", field.name, after_date));
                    }
                    if let Some(before_date) = before {
                        constraints.push(format!("{} < \"{}\"", field.name, before_date));
                    }
                },
                Type::NonEmpty(_) => {
                    constraints.push(format!("#{} > 0", field.name));
                },
                _ => {},
            }

            // Add where clause constraints
            for constraint in &field.constraints {
                if let Some(alloy_constraint) = self.constraint_to_alloy(constraint, &field.name) {
                    constraints.push(alloy_constraint);
                }
            }
        }

        constraints
    }

    fn constraint_to_alloy(&self, constraint: &Constraint, field_name: &str) -> Option<String> {
        match constraint {
            Constraint::GreaterThan(expr) => {
                Some(format!("{} > {}", field_name, self.expr_to_alloy(expr)))
            },
            Constraint::LessThan(expr) => {
                Some(format!("{} < {}", field_name, self.expr_to_alloy(expr)))
            },
            Constraint::GreaterThanOrEqual(expr) => {
                Some(format!("{} >= {}", field_name, self.expr_to_alloy(expr)))
            },
            Constraint::LessThanOrEqual(expr) => {
                Some(format!("{} <= {}", field_name, self.expr_to_alloy(expr)))
            },
            Constraint::Equal(expr) => {
                Some(format!("{} = {}", field_name, self.expr_to_alloy(expr)))
            },
            Constraint::NotEqual(expr) => {
                Some(format!("{} != {}", field_name, self.expr_to_alloy(expr)))
            },
            Constraint::InRange { min, max } => Some(format!(
                "{} >= {} and {} <= {}",
                field_name,
                self.expr_to_alloy(min),
                field_name,
                self.expr_to_alloy(max)
            )),
            Constraint::And(left, right) => {
                let left_str = self.constraint_to_alloy(left, field_name)?;
                let right_str = self.constraint_to_alloy(right, field_name)?;
                Some(format!("({}) and ({})", left_str, right_str))
            },
            Constraint::Or(left, right) => {
                let left_str = self.constraint_to_alloy(left, field_name)?;
                let right_str = self.constraint_to_alloy(right, field_name)?;
                Some(format!("({}) or ({})", left_str, right_str))
            },
            Constraint::Not(inner) => {
                let inner_str = self.constraint_to_alloy(inner, field_name)?;
                Some(format!("not ({})", inner_str))
            },
            Constraint::Before(expr) => {
                Some(format!("{} < {}", field_name, self.expr_to_alloy(expr)))
            },
            Constraint::After(expr) => {
                Some(format!("{} > {}", field_name, self.expr_to_alloy(expr)))
            },
            Constraint::Between { start, end } => Some(format!(
                "{} >= {} and {} <= {}",
                field_name,
                self.expr_to_alloy(start),
                field_name,
                self.expr_to_alloy(end)
            )),
            Constraint::Custom(name) => Some(format!("{}[{}]", name, field_name)),
        }
    }

    fn emit_enum(&mut self, e: &EnumDefinition) {
        self.line(&format!("abstract sig {} {{}}", e.name));
        for variant in &e.variants {
            self.line(&format!("one sig {} extends {} {{}}", variant, e.name));
        }
        self.blank();

        // For mutually exclusive enums, add verification predicate
        if e.mutually_exclusive {
            self.line(&format!("// Mutual exclusivity constraint for {}", e.name));
            self.line(&format!("fact MutuallyExclusive{} {{", e.name));
            self.indent += 1;
            self.line(&format!("// All {} instances are disjoint", e.name));
            for i in 0..e.variants.len() {
                for j in (i + 1)..e.variants.len() {
                    self.line(&format!("no ({} & {})", e.variants[i], e.variants[j]));
                }
            }
            self.indent -= 1;
            self.line("}");
            self.blank();
        }
    }

    fn emit_legal_test(&mut self, test: &LegalTestDefinition) {
        // Generate predicate for conjunctive requirements
        let params: Vec<String> = test
            .requirements
            .iter()
            .map(|req| format!("{}: {}", req.name, self.type_to_alloy(&req.ty)))
            .collect();

        self.line(&format!("pred {}[{}] {{", test.name, params.join(", ")));
        self.indent += 1;

        if test.requirements.is_empty() {
            self.line("// No requirements");
        } else {
            // All requirements must be true (conjunctive)
            let conditions: Vec<String> = test
                .requirements
                .iter()
                .map(|req| req.name.clone())
                .collect();
            self.line(&format!("{}", conditions.join(" and ")));
        }

        self.indent -= 1;
        self.line("}");
        self.blank();
    }

    fn emit_scope(&mut self, s: &ScopeDefinition) {
        self.line(&format!("// Scope: {}", s.name));
        for item in &s.items {
            self.emit_item(item);
        }
    }

    fn emit_function(&mut self, f: &FunctionDefinition) {
        let params: Vec<_> = f
            .params
            .iter()
            .map(|p| format!("{}: {}", p.name, self.type_to_alloy(&p.ty)))
            .collect();
        let return_type = self.type_to_alloy(&f.return_type);

        self.line(&format!(
            "fun {}[{}]: {} {{",
            f.name,
            params.join(", "),
            return_type
        ));
        self.indent += 1;

        // Emit body (simplified)
        for stmt in &f.body {
            if let Statement::Return(expr) = stmt {
                self.line(&self.expr_to_alloy(expr));
            }
        }

        self.indent -= 1;
        self.line("}");
        self.blank();
    }

    fn emit_declaration(&mut self, d: &Declaration) {
        if let Expr::Match(m) = &d.value {
            self.emit_match_predicate(&d.name, m);
        } else {
            // Emit as a fact
            let expr = self.expr_to_alloy(&d.value);
            self.line(&format!("// {} := {}", d.name, expr));
        }
    }

    fn emit_match_predicate(&mut self, name: &str, m: &MatchExpr) {
        let scrutinee = self.expr_to_alloy(&m.scrutinee);

        self.line(&format!("pred {}[] {{", name));
        self.indent += 1;

        for (i, case) in m.cases.iter().enumerate() {
            let condition = match &case.pattern {
                Pattern::Literal(lit) => format!("{} = {}", scrutinee, self.literal_to_alloy(lit)),
                Pattern::Identifier(id) => format!("{} = {}", scrutinee, id),
                Pattern::Wildcard => "else".to_string(),
                Pattern::Satisfies(test_name) => format!("{}[{}]", test_name, scrutinee),
            };
            let consequence = self.expr_to_alloy(&case.consequence);

            if i == 0 {
                self.line(&format!("{} implies {}", condition, consequence));
            } else if matches!(case.pattern, Pattern::Wildcard) {
                self.line(&format!("else {}", consequence));
            } else {
                self.line(&format!("else ({} implies {})", condition, consequence));
            }
        }

        self.indent -= 1;
        self.line("}");
        self.blank();
    }

    fn type_to_alloy(&self, ty: &Type) -> String {
        match ty {
            Type::Int => "Int".to_string(),
            Type::Float => "Int".to_string(), // Alloy doesn't have floats
            Type::Bool => "Bool".to_string(),
            Type::String => "String".to_string(),
            Type::Money => "Int".to_string(),
            Type::Date => "Date".to_string(),
            Type::Duration => "Int".to_string(),
            Type::Percent => "Int".to_string(),
            Type::Pass => "none".to_string(),
            Type::Named(name) => name.clone(),
            Type::Union(a, b) => format!("{} + {}", self.type_to_alloy(a), self.type_to_alloy(b)),

            // Dependent types (Phase 1)
            // Note: Constraints are generated separately in emit_struct
            Type::BoundedInt { .. } => "Int".to_string(),
            Type::NonEmpty(inner) => format!("set {}", self.type_to_alloy(inner)),
            Type::ValidDate { .. } => "Date".to_string(),
            Type::Positive(_) => "Int".to_string(),
            Type::Array(inner) => format!("set {}", self.type_to_alloy(inner)),
            Type::MoneyWithCurrency(_) => "Int".to_string(),
            Type::Citation {
                section,
                subsection,
                act,
            } => {
                format!(
                    "Citation_{}_{}_{}",
                    section.replace(".", "_"),
                    subsection.replace(".", "_"),
                    act.replace(" ", "_").replace("/", "_")
                )
            },
            Type::TemporalValue { inner, .. } => {
                // In Alloy, represent temporal values with a sig that has time bounds
                format!("Temporal_{}", self.type_to_alloy(inner))
            },
            Type::TypeVariable(name) => name.clone(),
            Type::Generic { name, .. } => {
                // Alloy doesn't have generic types, use base name
                name.clone()
            },
        }
    }

    fn expr_to_alloy(&self, expr: &Expr) -> String {
        match expr {
            Expr::Literal(lit) => self.literal_to_alloy(lit),
            Expr::Identifier(name) => name.clone(),
            Expr::Binary(l, op, r) => {
                let op_str = match op {
                    BinaryOp::Add => "plus",
                    BinaryOp::Sub => "minus",
                    BinaryOp::Mul => "mul",
                    BinaryOp::Div => "div",
                    BinaryOp::Mod => "rem",
                    BinaryOp::Eq => "=",
                    BinaryOp::Neq => "!=",
                    BinaryOp::Lt => "<",
                    BinaryOp::Gt => ">",
                    BinaryOp::Lte => "<=",
                    BinaryOp::Gte => ">=",
                    BinaryOp::And => "and",
                    BinaryOp::Or => "or",
                };
                if matches!(
                    op,
                    BinaryOp::Eq
                        | BinaryOp::Neq
                        | BinaryOp::Lt
                        | BinaryOp::Gt
                        | BinaryOp::Lte
                        | BinaryOp::Gte
                        | BinaryOp::And
                        | BinaryOp::Or
                ) {
                    format!(
                        "({} {} {})",
                        self.expr_to_alloy(l),
                        op_str,
                        self.expr_to_alloy(r)
                    )
                } else {
                    format!(
                        "{}.{}[{}]",
                        self.expr_to_alloy(l),
                        op_str,
                        self.expr_to_alloy(r)
                    )
                }
            },
            Expr::Unary(op, e) => {
                let op_str = match op {
                    UnaryOp::Not => "not",
                    UnaryOp::Neg => "negate",
                };
                format!("{}[{}]", op_str, self.expr_to_alloy(e))
            },
            Expr::Call(name, args) => {
                let arg_strs: Vec<_> = args.iter().map(|a| self.expr_to_alloy(a)).collect();
                format!("{}[{}]", name, arg_strs.join(", "))
            },
            Expr::FieldAccess(obj, field) => {
                format!("{}.{}", self.expr_to_alloy(obj), field)
            },
            Expr::StructInit(init) => {
                format!("some {}", init.name)
            },
            Expr::Match(_) => "/* match expr */".to_string(),
            Expr::Forall { var, ty, body } => {
                format!(
                    "all {}: {} | {}",
                    var,
                    self.type_to_alloy(ty),
                    self.expr_to_alloy(body)
                )
            },
            Expr::Exists { var, ty, body } => {
                format!(
                    "some {}: {} | {}",
                    var,
                    self.type_to_alloy(ty),
                    self.expr_to_alloy(body)
                )
            },
        }
    }

    fn literal_to_alloy(&self, lit: &Literal) -> String {
        match lit {
            Literal::Int(n) => n.to_string(),
            Literal::Float(n) => format!("{}", *n as i64),
            Literal::Bool(b) => if *b { "True" } else { "False" }.to_string(),
            Literal::String(s) => format!("\"{}\"", s),
            Literal::Money(n) => format!("{}", (*n * 100.0) as i64),
            Literal::Date(_) => "Date".to_string(),
            Literal::Duration(_) => "0".to_string(),
            Literal::Percent(p) => format!("{}", *p as i64),
            Literal::Pass => "none".to_string(),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use yuho_core::parse;

    #[test]
    fn test_alloy_struct() {
        let source = "struct Person { string name, int age, }";
        let program = parse(source).unwrap();
        let output = to_alloy(&program);
        assert!(output.contains("sig Person"));
        assert!(output.contains("name: String"));
    }

    #[test]
    fn test_alloy_enum() {
        let source = "enum Color { Red, Green, Blue, }";
        let program = parse(source).unwrap();
        let output = to_alloy(&program);
        assert!(output.contains("abstract sig Color"));
        assert!(output.contains("one sig Red extends Color"));
    }

    #[test]
    fn test_alloy_match() {
        let source = r#"
            match guilty {
                case true := "liable"
                case _ := "not liable"
            }
        "#;
        let program = parse(source).unwrap();
        let output = to_alloy(&program);
        assert!(output.contains("pred"));
    }
}
