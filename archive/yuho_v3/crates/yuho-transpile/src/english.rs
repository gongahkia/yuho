use yuho_core::ast::*;

/// Generate plain English explanation of Yuho program
pub fn to_english(program: &Program) -> String {
    let mut gen = EnglishGenerator::new();
    gen.generate(program)
}

struct EnglishGenerator {
    output: String,
}

impl EnglishGenerator {
    fn new() -> Self {
        Self {
            output: String::new(),
        }
    }

    fn generate(&mut self, program: &Program) -> String {
        self.output.push_str("LEGAL SPECIFICATION\n");
        self.output.push_str("===================\n\n");

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
                // Type aliases are compile-time only
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
        self.output.push_str(&format!(
            "A \"{}\" consists of the following components:\n",
            s.name
        ));

        for field in &s.fields {
            let annotation_note = self.extract_annotation_note(&field.annotations);
            self.output.push_str(&format!(
                "  - {} ({}){}\n",
                field.name,
                self.type_description(&field.ty),
                annotation_note
            ));
        }
        self.output.push('\n');
    }

    fn extract_annotation_note(&self, annotations: &[Annotation]) -> String {
        let mut notes = Vec::new();
        for ann in annotations {
            match ann {
                Annotation::Precedent { citation } => {
                    notes.push(format!(" [Legal precedent: {}]", citation));
                },
                Annotation::Presumed(value) => {
                    notes.push(format!(" [Presumed: {}]", value));
                },
                Annotation::Hierarchy {
                    level,
                    subordinate_to,
                } => {
                    if let Some(parent) = subordinate_to {
                        notes.push(format!(" [Hierarchy: {}, under {}]", level, parent));
                    } else {
                        notes.push(format!(" [Hierarchy: {}]", level));
                    }
                },
                Annotation::Amended { date, act } => {
                    notes.push(format!(" [Amended: {} by {}]", date, act));
                },
            }
        }
        notes.join("")
    }

    fn emit_enum(&mut self, e: &EnumDefinition) {
        self.output
            .push_str(&format!("\"{}\" may be one of the following:\n", e.name));

        for (i, variant) in e.variants.iter().enumerate() {
            if i == e.variants.len() - 1 && e.variants.len() > 1 {
                self.output.push_str(&format!("  - or {}\n", variant));
            } else {
                self.output.push_str(&format!("  - {}\n", variant));
            }
        }

        if e.mutually_exclusive {
            self.output
                .push_str("\nIMPORTANT: These options are MUTUALLY EXCLUSIVE.\n");
            self.output
                .push_str("Only ONE of these values may be returned from any function.\n");
            self.output.push_str(
                "The compiler verifies that no code path can return multiple variants.\n",
            );
        }

        self.output.push('\n');
    }

    fn emit_legal_test(&mut self, test: &LegalTestDefinition) {
        self.output.push_str(&format!(
            "LEGAL TEST \"{}\": ALL of the following conditions must be satisfied:\n",
            test.name
        ));

        for (i, req) in test.requirements.iter().enumerate() {
            self.output.push_str(&format!(
                "  {}. {} must be {}\n",
                i + 1,
                req.name,
                self.type_description(&req.ty)
            ));
        }
        self.output.push('\n');
    }

    fn emit_scope(&mut self, s: &ScopeDefinition) {
        self.output.push_str(&format!(
            "SECTION: {}\n{}\n\n",
            s.name,
            "-".repeat(s.name.len() + 9)
        ));

        for item in &s.items {
            self.emit_item(item);
        }
    }

    fn emit_function(&mut self, f: &FunctionDefinition) {
        let params: Vec<String> = f
            .params
            .iter()
            .map(|p| format!("{} ({})", p.name, self.type_description(&p.ty)))
            .collect();

        self.output.push_str(&format!(
            "RULE \"{}\": Given {}, determine {}.\n\n",
            f.name,
            if params.is_empty() {
                "no inputs".to_string()
            } else {
                params.join(" and ")
            },
            self.type_description(&f.return_type)
        ));
    }

    fn emit_declaration(&mut self, d: &Declaration) {
        if let Expr::Match(m) = &d.value {
            self.emit_match_decision(m);
        } else {
            let expr = self.expr_to_english(&d.value);
            self.output
                .push_str(&format!("Let \"{}\" be defined as {}.\n\n", d.name, expr));
        }
    }

    fn emit_match_decision(&mut self, m: &MatchExpr) {
        let scrutinee = self.expr_to_english(&m.scrutinee);

        self.output
            .push_str(&format!("DECISION based on {}:\n", scrutinee));

        for (i, case) in m.cases.iter().enumerate() {
            let condition = match &case.pattern {
                Pattern::Literal(lit) => self.literal_to_english(lit),
                Pattern::Identifier(id) => format!("\"{}\"", id),
                Pattern::Wildcard => "all other cases".to_string(),
                Pattern::Satisfies(test_name) => {
                    format!("all {} requirements are satisfied", test_name)
                },
            };
            let consequence = self.expr_to_english(&case.consequence);

            if i == 0 {
                self.output
                    .push_str(&format!("  IF {} THEN {}\n", condition, consequence));
            } else if matches!(case.pattern, Pattern::Wildcard) {
                self.output
                    .push_str(&format!("  OTHERWISE {}\n", consequence));
            } else {
                self.output
                    .push_str(&format!("  ELSE IF {} THEN {}\n", condition, consequence));
            }
        }
        self.output.push('\n');
    }

    fn type_description(&self, ty: &Type) -> String {
        match ty {
            Type::Int => "a whole number".to_string(),
            Type::Float => "a decimal number".to_string(),
            Type::Bool => "true or false".to_string(),
            Type::String => "text".to_string(),
            Type::Money => "a monetary amount".to_string(),
            Type::Date => "a date".to_string(),
            Type::Duration => "a time period".to_string(),
            Type::Percent => "a percentage".to_string(),
            Type::Pass => "nothing".to_string(),
            Type::Named(name) => format!("a {}", name),
            Type::Union(a, b) => format!(
                "either {} or {}",
                self.type_description(a),
                self.type_description(b)
            ),

            // Dependent types (Phase 1)
            Type::BoundedInt { min, max } => format!("a whole number between {} and {}", min, max),
            Type::NonEmpty(inner) => format!("at least one {}", self.type_description(inner)),
            Type::ValidDate { after, before } => match (after, before) {
                (Some(a), Some(b)) => format!("a date between {} and {}", a, b),
                (Some(a), None) => format!("a date after {}", a),
                (None, Some(b)) => format!("a date before {}", b),
                (None, None) => "a valid date".to_string(),
            },
            Type::Positive(inner) => format!("a positive {}", self.type_description(inner)),
            Type::Array(inner) => format!("a collection of {}", self.type_description(inner)),
            Type::MoneyWithCurrency(currency) => format!("a monetary amount in {}", currency),
            Type::Citation {
                section,
                subsection,
                act,
            } => {
                format!(
                    "a legal citation to section {}, subsection {} of the {}",
                    section, subsection, act
                )
            },
            Type::TemporalValue {
                inner,
                valid_from,
                valid_until,
            } => {
                let mut desc = format!("a time-bound {}", self.type_description(inner));
                match (valid_from, valid_until) {
                    (Some(from), Some(until)) => {
                        desc.push_str(&format!(" (valid from {} to {})", from, until));
                    },
                    (Some(from), None) => {
                        desc.push_str(&format!(" (effective from {})", from));
                    },
                    (None, Some(until)) => {
                        desc.push_str(&format!(" (valid until {})", until));
                    },
                    (None, None) => {},
                }
                desc
            },
            Type::TypeVariable(name) => format!("type {}", name),
            Type::Generic { name, args } => {
                let args_str = args
                    .iter()
                    .map(|arg| self.type_description(arg))
                    .collect::<Vec<_>>()
                    .join(" and ");
                format!("{} containing {}", name, args_str)
            },
        }
    }

    fn expr_to_english(&self, expr: &Expr) -> String {
        match expr {
            Expr::Literal(lit) => self.literal_to_english(lit),
            Expr::Identifier(name) => format!("\"{}\"", name),
            Expr::Binary(l, op, r) => {
                let op_str = match op {
                    BinaryOp::Add => "plus",
                    BinaryOp::Sub => "minus",
                    BinaryOp::Mul => "multiplied by",
                    BinaryOp::Div => "divided by",
                    BinaryOp::Mod => "modulo",
                    BinaryOp::Eq => "equals",
                    BinaryOp::Neq => "does not equal",
                    BinaryOp::Lt => "is less than",
                    BinaryOp::Gt => "is greater than",
                    BinaryOp::Lte => "is at most",
                    BinaryOp::Gte => "is at least",
                    BinaryOp::And => "and",
                    BinaryOp::Or => "or",
                };
                format!(
                    "{} {} {}",
                    self.expr_to_english(l),
                    op_str,
                    self.expr_to_english(r)
                )
            },
            Expr::Unary(op, e) => {
                let op_str = match op {
                    UnaryOp::Not => "not",
                    UnaryOp::Neg => "negative",
                };
                format!("{} {}", op_str, self.expr_to_english(e))
            },
            Expr::Call(name, args) => {
                let arg_strs: Vec<_> = args.iter().map(|a| self.expr_to_english(a)).collect();
                if args.is_empty() {
                    format!("apply rule \"{}\"", name)
                } else {
                    format!("apply rule \"{}\" to {}", name, arg_strs.join(" and "))
                }
            },
            Expr::FieldAccess(obj, field) => {
                format!("the {} of {}", field, self.expr_to_english(obj))
            },
            Expr::StructInit(init) => {
                format!("a new {}", init.name)
            },
            Expr::Match(_) => "(see decision below)".to_string(),
            Expr::Forall { var, ty, body } => {
                format!("for all {}: {:?}, {}", var, ty, self.expr_to_english(body))
            },
            Expr::Exists { var, ty, body } => {
                format!(
                    "there exists {}: {:?} such that {}",
                    var,
                    ty,
                    self.expr_to_english(body)
                )
            },
        }
    }

    fn literal_to_english(&self, lit: &Literal) -> String {
        match lit {
            Literal::Int(n) => n.to_string(),
            Literal::Float(n) => n.to_string(),
            Literal::Bool(b) => if *b { "true" } else { "false" }.to_string(),
            Literal::String(s) => format!("\"{}\"", s),
            Literal::Money(n) => format!("${:.2}", n),
            Literal::Date(d) => d.clone(),
            Literal::Duration(d) => d.clone(),
            Literal::Percent(p) => format!("{}%", p),
            Literal::Pass => "nothing".to_string(),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use yuho_core::parse;

    #[test]
    fn test_english_struct() {
        let source = "struct Person { string name, int age, }";
        let program = parse(source).unwrap();
        let output = to_english(&program);
        assert!(output.contains("consists of the following"));
        assert!(output.contains("name"));
    }

    #[test]
    fn test_english_enum() {
        let source = "enum Verdict { Guilty, NotGuilty, }";
        let program = parse(source).unwrap();
        let output = to_english(&program);
        assert!(output.contains("may be one of"));
    }

    #[test]
    fn test_english_match() {
        let source = r#"
            match guilty {
                case true := "liable"
                case _ := "not liable"
            }
        "#;
        let program = parse(source).unwrap();
        let output = to_english(&program);
        assert!(output.contains("DECISION"));
        assert!(output.contains("IF"));
        assert!(output.contains("OTHERWISE"));
    }
}
