use yuho_core::ast::*;

pub fn to_mermaid(program: &Program) -> String {
    let mut gen = MermaidGenerator::new();
    gen.generate(program)
}

struct MermaidGenerator {
    output: String,
    node_id: usize,
}

impl MermaidGenerator {
    fn new() -> Self {
        Self {
            output: String::new(),
            node_id: 0,
        }
    }

    fn next_id(&mut self) -> usize {
        let id = self.node_id;
        self.node_id += 1;
        id
    }

    fn generate(&mut self, program: &Program) -> String {
        self.output.push_str("graph TD\n");

        for item in &program.items {
            self.emit_item(item, None);
        }

        std::mem::take(&mut self.output)
    }

    fn emit_item(&mut self, item: &Item, parent: Option<usize>) -> usize {
        match item {
            Item::Scope(s) => self.emit_scope(s, parent),
            Item::Struct(s) => self.emit_struct(s, parent),
            Item::Enum(e) => self.emit_enum(e, parent),
            Item::Function(f) => self.emit_function(f, parent),
            Item::Declaration(d) => self.emit_declaration(d, parent),
            Item::TypeAlias(_) => {
                // Type aliases are compile-time only, don't emit in Mermaid
                parent.unwrap_or(0)
            },
            Item::LegalTest(test) => self.emit_legal_test(test, parent),
            Item::ConflictCheck(_) => {
                // Conflict checks are compile-time directives
                parent.unwrap_or(0)
            },
            Item::Principle(_) => {
                // For now, principles are not transpiled to this target
                // Full Z3 verification support coming in future commits
                parent.unwrap_or(0)
            },
            Item::Proviso(_) => {
                // Proviso clauses are compile-time directives
                parent.unwrap_or(0)
            },
        }
    }

    fn emit_scope(&mut self, scope: &ScopeDefinition, parent: Option<usize>) -> usize {
        let id = self.next_id();
        self.output
            .push_str(&format!("    N{}[\"scope {}\"]\n", id, scope.name));

        if let Some(p) = parent {
            self.output.push_str(&format!("    N{} --> N{}\n", p, id));
        }

        for inner in &scope.items {
            self.emit_item(inner, Some(id));
        }

        id
    }

    fn emit_struct(&mut self, s: &StructDefinition, parent: Option<usize>) -> usize {
        let id = self.next_id();
        let fields: Vec<_> = s
            .fields
            .iter()
            .map(|f| format!("{}: {}", f.name, self.type_to_string(&f.ty)))
            .collect();

        self.output.push_str(&format!(
            "    N{}[\"struct {}<br/>{}\"]\n",
            id,
            s.name,
            fields.join("<br/>")
        ));

        if let Some(p) = parent {
            self.output.push_str(&format!("    N{} --> N{}\n", p, id));
        }

        id
    }

    fn emit_enum(&mut self, e: &EnumDefinition, parent: Option<usize>) -> usize {
        let id = self.next_id();

        let exclusive_marker = if e.mutually_exclusive {
            "<br/>[MUTUALLY EXCLUSIVE]"
        } else {
            ""
        };

        self.output.push_str(&format!(
            "    N{}[\"enum {}<br/>{}{}\"]\n",
            id,
            e.name,
            e.variants.join(" | "),
            exclusive_marker
        ));

        if let Some(p) = parent {
            self.output.push_str(&format!("    N{} --> N{}\n", p, id));
        }

        id
    }

    fn emit_legal_test(&mut self, test: &LegalTestDefinition, parent: Option<usize>) -> usize {
        let id = self.next_id();
        let requirements: Vec<_> = test
            .requirements
            .iter()
            .map(|req| format!("{}: {}", req.name, self.type_to_string(&req.ty)))
            .collect();

        self.output.push_str(&format!(
            "    N{}{{\"legal_test {}<br/>ALL: {}\"

}}\n",
            id,
            test.name,
            requirements.join("<br/>AND: ")
        ));

        if let Some(p) = parent {
            self.output.push_str(&format!("    N{} --> N{}\n", p, id));
        }

        id
    }

    fn emit_function(&mut self, f: &FunctionDefinition, parent: Option<usize>) -> usize {
        let id = self.next_id();
        let params: Vec<_> = f
            .params
            .iter()
            .map(|p| format!("{}: {}", p.name, self.type_to_string(&p.ty)))
            .collect();

        self.output.push_str(&format!(
            "    N{}[\"func {}({}): {}\"]\n",
            id,
            f.name,
            params.join(", "),
            self.type_to_string(&f.return_type)
        ));

        if let Some(p) = parent {
            self.output.push_str(&format!("    N{} --> N{}\n", p, id));
        }

        id
    }

    fn emit_declaration(&mut self, d: &Declaration, parent: Option<usize>) -> usize {
        let id = self.next_id();

        // Check if it's a match expression
        if let Expr::Match(m) = &d.value {
            return self.emit_match(m, parent);
        }

        let expr_str = self.expr_to_string(&d.value);
        self.output.push_str(&format!(
            "    N{}[\"{} {} := {}\"]\n",
            id,
            self.type_to_string(&d.ty),
            d.name,
            expr_str
        ));

        if let Some(p) = parent {
            self.output.push_str(&format!("    N{} --> N{}\n", p, id));
        }

        id
    }

    fn emit_match(&mut self, m: &MatchExpr, parent: Option<usize>) -> usize {
        let id = self.next_id();
        let scrutinee = self.expr_to_string(&m.scrutinee);

        self.output
            .push_str(&format!("    N{}{{\"`match {}`\"}}\n", id, scrutinee));

        if let Some(p) = parent {
            self.output.push_str(&format!("    N{} --> N{}\n", p, id));
        }

        for case in &m.cases {
            let case_id = self.next_id();
            let pattern = self.pattern_to_string(&case.pattern);
            let consequence = self.expr_to_string(&case.consequence);

            self.output.push_str(&format!(
                "    N{}[\"{} → {}\"]\n",
                case_id, pattern, consequence
            ));
            self.output
                .push_str(&format!("    N{} --> N{}\n", id, case_id));
        }

        id
    }

    fn expr_to_string(&self, expr: &Expr) -> String {
        match expr {
            Expr::Literal(lit) => self.literal_to_string(lit),
            Expr::Identifier(name) => name.clone(),
            Expr::Binary(l, op, r) => {
                let op_str = match op {
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
                    BinaryOp::And => "&&",
                    BinaryOp::Or => "||",
                };
                format!(
                    "{} {} {}",
                    self.expr_to_string(l),
                    op_str,
                    self.expr_to_string(r)
                )
            },
            Expr::Unary(op, e) => {
                let op_str = match op {
                    UnaryOp::Not => "!",
                    UnaryOp::Neg => "-",
                };
                format!("{}{}", op_str, self.expr_to_string(e))
            },
            Expr::Call(name, args) => {
                let arg_strs: Vec<_> = args.iter().map(|a| self.expr_to_string(a)).collect();
                format!("{}({})", name, arg_strs.join(", "))
            },
            Expr::FieldAccess(obj, field) => {
                format!("{}.{}", self.expr_to_string(obj), field)
            },
            Expr::StructInit(init) => {
                let fields: Vec<_> = init
                    .fields
                    .iter()
                    .map(|(k, v)| format!("{}: {}", k, self.expr_to_string(v)))
                    .collect();
                if init.name.is_empty() {
                    format!("{{ {} }}", fields.join(", "))
                } else {
                    format!("{} {{ {} }}", init.name, fields.join(", "))
                }
            },
            Expr::Match(_) => "match {...}".to_string(),
            Expr::Forall { var, ty, body } => {
                format!("∀{}: {:?}, {}", var, ty, self.expr_to_string(body))
            },
            Expr::Exists { var, ty, body } => {
                format!("∃{}: {:?}, {}", var, ty, self.expr_to_string(body))
            },
        }
    }

    fn literal_to_string(&self, lit: &Literal) -> String {
        match lit {
            Literal::Int(n) => n.to_string(),
            Literal::Float(n) => n.to_string(),
            Literal::Bool(b) => b.to_string(),
            Literal::String(s) => s.clone(), // Remove quotes for Mermaid compatibility
            Literal::Money(n) => format!("${:.2}", n),
            Literal::Date(d) => d.clone(),
            Literal::Duration(d) => d.clone(),
            Literal::Percent(p) => format!("{}%", p),
            Literal::Pass => "pass".to_string(),
        }
    }

    fn pattern_to_string(&self, pattern: &Pattern) -> String {
        match pattern {
            Pattern::Literal(lit) => self.literal_to_string(lit),
            Pattern::Identifier(name) => name.clone(),
            Pattern::Wildcard => "_".to_string(),
            Pattern::Satisfies(test_name) => format!("satisfies {}", test_name),
        }
    }

    fn type_to_string(&self, ty: &Type) -> String {
        match ty {
            Type::Int => "Int".to_string(),
            Type::Float => "Float".to_string(),
            Type::Bool => "Bool".to_string(),
            Type::String => "String".to_string(),
            Type::Money => "Money".to_string(),
            Type::Date => "Date".to_string(),
            Type::Duration => "Duration".to_string(),
            Type::Percent => "Percent".to_string(),
            Type::Pass => "Pass".to_string(),
            Type::Named(name) => name.clone(),
            Type::Union(left, right) => {
                format!(
                    "{} | {}",
                    self.type_to_string(left),
                    self.type_to_string(right)
                )
            },
            Type::BoundedInt { min, max } => format!("BoundedInt‹{}, {}›", min, max),
            Type::NonEmpty(inner) => format!("NonEmpty‹{}›", self.type_to_string(inner)),
            Type::Positive(inner) => format!("Positive‹{}›", self.type_to_string(inner)),
            Type::ValidDate { .. } => "ValidDate".to_string(),
            Type::Array(inner) => format!("Array‹{}›", self.type_to_string(inner)),
            Type::MoneyWithCurrency(currency) => format!("Money‹{}›", currency),
            Type::Citation {
                section,
                subsection,
                act,
            } => {
                format!("Citation‹§{}.{} {}›", section, subsection, act)
            },
            Type::TemporalValue {
                inner,
                valid_from,
                valid_until,
            } => {
                let mut result = format!("Temporal‹{}", self.type_to_string(inner));
                if let Some(from) = valid_from {
                    result.push_str(&format!(" from:{}", from));
                }
                if let Some(until) = valid_until {
                    result.push_str(&format!(" until:{}", until));
                }
                result.push('›');
                result
            },
            Type::TypeVariable(name) => name.clone(),
            Type::Generic { name, args } => {
                let args_str = args
                    .iter()
                    .map(|arg| self.type_to_string(arg))
                    .collect::<Vec<_>>()
                    .join(", ");
                format!("{}‹{}›", name, args_str)
            },
        }
    }
}

/// Generate a flowchart specifically for legal reasoning
pub fn to_legal_flowchart(program: &Program) -> String {
    let mut output = String::from("flowchart TD\n");
    output.push_str("    subgraph legend[Legend]\n");
    output.push_str("        L1[Struct] --> L2{Decision}\n");
    output.push_str("        L2 --> L3[Outcome]\n");
    output.push_str("    end\n\n");

    let mut gen = LegalFlowchartGenerator::new();
    output.push_str(&gen.generate(program));

    output
}

struct LegalFlowchartGenerator {
    node_id: usize,
}

impl LegalFlowchartGenerator {
    fn new() -> Self {
        Self { node_id: 0 }
    }

    fn next_id(&mut self) -> String {
        let id = format!("N{}", self.node_id);
        self.node_id += 1;
        id
    }

    fn generate(&mut self, program: &Program) -> String {
        let mut output = String::new();

        for item in &program.items {
            output.push_str(&self.emit_item(item));
        }

        output
    }

    fn emit_item(&mut self, item: &Item) -> String {
        match item {
            Item::Scope(s) => {
                let mut out = format!("    subgraph {}[\"{}\"]\n", self.next_id(), s.name);
                for inner in &s.items {
                    out.push_str(&self.emit_item(inner));
                }
                out.push_str("    end\n");
                out
            },
            Item::Declaration(d) => {
                if let Expr::Match(m) = &d.value {
                    self.emit_match_flowchart(m)
                } else {
                    String::new()
                }
            },
            _ => String::new(),
        }
    }

    fn emit_match_flowchart(&mut self, m: &MatchExpr) -> String {
        let mut out = String::new();
        let decision_id = self.next_id();

        // Use MermaidGenerator to convert expression to string
        let gen = MermaidGenerator::new();
        let scrutinee = gen.expr_to_string(&m.scrutinee);

        out.push_str(&format!("        {}{{\"{}\"}}\n", decision_id, scrutinee));

        for case in &m.cases {
            let outcome_id = self.next_id();
            let pattern = match &case.pattern {
                Pattern::Literal(lit) => gen.literal_to_string(lit),
                Pattern::Identifier(name) => name.clone(),
                Pattern::Wildcard => "otherwise".to_string(),
                Pattern::Satisfies(test_name) => format!("satisfies {}", test_name),
            };
            let consequence = gen.expr_to_string(&case.consequence);

            out.push_str(&format!("        {}[\"{}\"]\n", outcome_id, consequence));
            out.push_str(&format!(
                "        {} -->|{}| {}\n",
                decision_id, pattern, outcome_id
            ));
        }

        out
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use yuho_core::parse;

    #[test]
    fn test_mermaid_struct() {
        let source = "struct Person { string name, int age, }";
        let program = parse(source).unwrap();
        let output = to_mermaid(&program);
        assert!(output.contains("struct Person"));
    }

    #[test]
    fn test_mermaid_scope() {
        let source = "scope test { int x := 1 }";
        let program = parse(source).unwrap();
        let output = to_mermaid(&program);
        assert!(output.contains("scope test"));
    }

    #[test]
    fn test_legal_flowchart() {
        let source = r#"
            scope s415 {
                match guilty {
                    case true := "liable"
                    case _ := "not liable"
                }
            }
        "#;
        let program = parse(source).unwrap();
        let output = to_legal_flowchart(&program);
        assert!(output.contains("flowchart TD"));
    }
}
