use yuho_core::ast::*;

/// Generate TypeScript type definitions from Yuho program
pub fn to_typescript(program: &Program) -> String {
    let mut gen = TypeScriptGenerator::new();
    gen.generate(program)
}

struct TypeScriptGenerator {
    output: String,
    indent: usize,
}

impl TypeScriptGenerator {
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
        self.line("// TypeScript type definitions generated from Yuho");
        self.line("// Auto-generated - do not edit manually");
        self.blank();

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
            Item::TypeAlias(alias) => self.emit_type_alias(alias),
            Item::LegalTest(test) => self.emit_legal_test(test),
            Item::ConflictCheck(_) => {
                // Conflict checks are compile-time directives, not runtime code
                self.line("// Conflict check performed at compile time");
            },
            Item::Principle(_) => {},
            Item::Proviso(_) => {
                // Proviso clauses are treated as compile-time directives
            },
            Item::Proviso(_) => {
                // For now, principles are not transpiled to this target
                // Full Z3 verification support coming in future commits
                self.line("// Principle verification performed at compile time");
            },
        }
    }

    fn emit_struct(&mut self, s: &StructDefinition) {
        // Generate type parameter list for generic structs
        let type_params = if !s.type_params.is_empty() {
            format!("<{}>", s.type_params.join(", "))
        } else {
            String::new()
        };

        self.line(&format!("export interface {}{} {{", s.name, type_params));
        self.indent += 1;

        for field in &s.fields {
            let ts_type = self.type_to_ts(&field.ty);
            self.line(&format!("{}: {};", field.name, ts_type));
        }

        self.indent -= 1;
        self.line("}");
        self.blank();
    }

    fn emit_enum(&mut self, e: &EnumDefinition) {
        // Emit as union type
        let variants: Vec<String> = e.variants.iter().map(|v| format!("\"{}\"", v)).collect();

        self.line(&format!(
            "export type {} = {};",
            e.name,
            variants.join(" | ")
        ));
        self.blank();

        // Also emit as const enum for runtime use
        self.line(&format!("export const {}Values = {{", e.name));
        self.indent += 1;
        for variant in &e.variants {
            self.line(&format!("{}: \"{}\",", variant, variant));
        }
        self.indent -= 1;
        self.line("} as const;");
        self.blank();

        // Add mutually exclusive comment
        if e.mutually_exclusive {
            self.line(&format!(
                "// MUTUALLY EXCLUSIVE: {} variants must not overlap in return paths",
                e.name
            ));
            self.line("// Static analysis enforces this at compile time");
            self.blank();
        }
    }

    fn emit_type_alias(&mut self, alias: &TypeAliasDefinition) {
        // Generate type parameter list for generic type aliases
        let type_params = if !alias.type_params.is_empty() {
            format!("<{}>", alias.type_params.join(", "))
        } else {
            String::new()
        };

        let target = self.type_to_ts(&alias.target);
        self.line(&format!(
            "export type {}{} = {};",
            alias.name, type_params, target
        ));
        self.blank();
    }

    fn emit_legal_test(&mut self, test: &LegalTestDefinition) {
        // Generate TypeScript interface for the legal test
        self.line(&format!("export interface {}Test {{", test.name));
        self.indent += 1;

        for req in &test.requirements {
            let ts_type = self.type_to_ts(&req.ty);
            self.line(&format!("{}: {};", req.name, ts_type));
        }

        self.indent -= 1;
        self.line("}");
        self.blank();

        // Generate validation function that checks all requirements
        self.line(&format!(
            "export function satisfies{}Test(values: {}Test): boolean {{",
            test.name, test.name
        ));
        self.indent += 1;

        if test.requirements.is_empty() {
            self.line("return true;");
        } else {
            let conditions: Vec<String> = test
                .requirements
                .iter()
                .map(|req| format!("values.{}", req.name))
                .collect();
            self.line(&format!("return {};", conditions.join(" && ")));
        }

        self.indent -= 1;
        self.line("}");
        self.blank();
    }

    fn emit_scope(&mut self, s: &ScopeDefinition) {
        self.line(&format!("export namespace {} {{", s.name));
        self.indent += 1;

        for item in &s.items {
            self.emit_item(item);
        }

        self.indent -= 1;
        self.line("}");
        self.blank();
    }

    fn emit_function(&mut self, f: &FunctionDefinition) {
        // Generate type parameter list for generic functions
        let type_params = if !f.type_params.is_empty() {
            format!("<{}>", f.type_params.join(", "))
        } else {
            String::new()
        };

        let params: Vec<String> = f
            .params
            .iter()
            .map(|p| format!("{}: {}", p.name, self.type_to_ts(&p.ty)))
            .collect();
        let return_type = self.type_to_ts(&f.return_type);

        self.line(&format!(
            "export function {}{}({}): {} {{",
            f.name,
            type_params,
            params.join(", "),
            return_type
        ));
        self.indent += 1;
        self.line("// Implementation placeholder");
        self.line(&format!("throw new Error('Not implemented: {}');", f.name));
        self.indent -= 1;
        self.line("}");
        self.blank();
    }

    fn emit_declaration(&mut self, d: &Declaration) {
        let ts_type = self.type_to_ts(&d.ty);

        if let Expr::Match(m) = &d.value {
            self.emit_match_function(d, m);
        } else {
            let value = self.expr_to_ts(&d.value);
            self.line(&format!(
                "export const {}: {} = {};",
                d.name, ts_type, value
            ));
            self.blank();
        }
    }

    fn emit_match_function(&mut self, d: &Declaration, m: &MatchExpr) {
        let scrutinee_type = "unknown"; // Would need type inference
        let result_type = self.type_to_ts(&d.ty);

        self.line(&format!(
            "export function {}(value: {}): {} {{",
            d.name, scrutinee_type, result_type
        ));
        self.indent += 1;

        for (i, case) in m.cases.iter().enumerate() {
            let mut condition = match &case.pattern {
                Pattern::Literal(lit) => format!("value === {}", self.literal_to_ts(lit)),
                Pattern::Identifier(_id) => {
                    // Bind pattern variable
                    format!("true") // Pattern variable always matches
                },
                Pattern::Wildcard => "true".to_string(),
                Pattern::Satisfies(test_name) => {
                    format!("satisfies{}Test(value)", test_name)
                },
            };

            // Add guard condition if present
            if let Some(guard) = &case.guard {
                let guard_expr = self.expr_to_ts(guard);
                if matches!(case.pattern, Pattern::Identifier(_)) {
                    // For identifier patterns, the guard is the only condition
                    condition = guard_expr;
                } else if !matches!(case.pattern, Pattern::Wildcard) {
                    // For other patterns, combine with guard
                    condition = format!("({}) && ({})", condition, guard_expr);
                }
            }

            let consequence = self.expr_to_ts(&case.consequence);

            if i == 0 {
                self.line(&format!("if ({}) {{", condition));
            } else if matches!(case.pattern, Pattern::Wildcard) && case.guard.is_none() {
                self.line("} else {");
            } else {
                self.line(&format!("}} else if ({}) {{", condition));
            }
            self.indent += 1;
            self.line(&format!("return {};", consequence));
            self.indent -= 1;
        }
        self.line("}");

        self.indent -= 1;
        self.line("}");
        self.blank();
    }

    fn type_to_ts(&self, ty: &Type) -> String {
        match ty {
            Type::Int => "number".to_string(),
            Type::Float => "number".to_string(),
            Type::Bool => "boolean".to_string(),
            Type::String => "string".to_string(),
            Type::Money => "number".to_string(),
            Type::Date => "Date".to_string(),
            Type::Duration => "number".to_string(),
            Type::Percent => "number".to_string(),
            Type::Pass => "void".to_string(),
            Type::Named(name) => name.clone(),
            Type::Union(a, b) => format!("{} | {}", self.type_to_ts(a), self.type_to_ts(b)),

            // Dependent types (Phase 1)
            Type::BoundedInt { .. } => "number".to_string(),
            Type::NonEmpty(inner) => format!("NonEmptyArray<{}>", self.type_to_ts(inner)),
            Type::ValidDate { .. } => "Date".to_string(),
            Type::Positive(_) => "number".to_string(),
            Type::Array(inner) => format!("Array<{}>", self.type_to_ts(inner)),
            Type::MoneyWithCurrency(currency) => format!("Money<'{}'>", currency),
            Type::Citation {
                section,
                subsection,
                act,
            } => {
                format!("Citation<'{}', '{}', '{}'>", section, subsection, act)
            },
            Type::TemporalValue {
                inner,
                valid_from,
                valid_until,
            } => {
                let mut parts = vec![self.type_to_ts(inner)];
                if let Some(from) = valid_from {
                    parts.push(format!("ValidFrom<'{}'>", from));
                }
                if let Some(until) = valid_until {
                    parts.push(format!("ValidUntil<'{}'>", until));
                }
                format!("Temporal<{}>", parts.join(", "))
            },
            Type::TypeVariable(name) => name.clone(),
            Type::Generic { name, args } => {
                let args_str = args
                    .iter()
                    .map(|arg| self.type_to_ts(arg))
                    .collect::<Vec<_>>()
                    .join(", ");
                format!("{}<{}>", name, args_str)
            },
        }
    }

    fn expr_to_ts(&self, expr: &Expr) -> String {
        match expr {
            Expr::Literal(lit) => self.literal_to_ts(lit),
            Expr::Identifier(name) => name.clone(),
            Expr::Binary(l, op, r) => {
                let op_str = match op {
                    BinaryOp::Add => "+",
                    BinaryOp::Sub => "-",
                    BinaryOp::Mul => "*",
                    BinaryOp::Div => "/",
                    BinaryOp::Mod => "%",
                    BinaryOp::Eq => "===",
                    BinaryOp::Neq => "!==",
                    BinaryOp::Lt => "<",
                    BinaryOp::Gt => ">",
                    BinaryOp::Lte => "<=",
                    BinaryOp::Gte => ">=",
                    BinaryOp::And => "&&",
                    BinaryOp::Or => "||",
                };
                format!("({} {} {})", self.expr_to_ts(l), op_str, self.expr_to_ts(r))
            },
            Expr::Unary(op, e) => {
                let op_str = match op {
                    UnaryOp::Not => "!",
                    UnaryOp::Neg => "-",
                };
                format!("{}{}", op_str, self.expr_to_ts(e))
            },
            Expr::Call(name, args) => {
                let arg_strs: Vec<_> = args.iter().map(|a| self.expr_to_ts(a)).collect();
                format!("{}({})", name, arg_strs.join(", "))
            },
            Expr::FieldAccess(obj, field) => {
                format!("{}.{}", self.expr_to_ts(obj), field)
            },
            Expr::StructInit(init) => {
                let fields: Vec<String> = init
                    .fields
                    .iter()
                    .map(|(k, v)| format!("{}: {}", k, self.expr_to_ts(v)))
                    .collect();
                format!("{{ {} }}", fields.join(", "))
            },
            Expr::Match(_) => "/* match expr */".to_string(),
            Expr::Forall { var, ty, body } => {
                format!("/* ∀{}: {:?}, {} */", var, ty, self.expr_to_ts(body))
            },
            Expr::Exists { var, ty, body } => {
                format!("/* ∃{}: {:?}, {} */", var, ty, self.expr_to_ts(body))
            },
        }
    }

    fn literal_to_ts(&self, lit: &Literal) -> String {
        match lit {
            Literal::Int(n) => n.to_string(),
            Literal::Float(n) => n.to_string(),
            Literal::Bool(b) => b.to_string(),
            Literal::String(s) => format!("\"{}\"", s.replace('\"', "\\\"")),
            Literal::Money(n) => n.to_string(),
            Literal::Date(d) => format!("new Date(\"{}\")", d),
            Literal::Duration(d) => format!("/* {} */ 0", d),
            Literal::Percent(p) => format!("{}", (*p as f64) / 100.0),
            Literal::Pass => "undefined".to_string(),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use yuho_core::parse;

    #[test]
    fn test_ts_struct() {
        let source = "struct Person { string name, int age, }";
        let program = parse(source).unwrap();
        let output = to_typescript(&program);
        assert!(output.contains("export interface Person"));
        assert!(output.contains("name: string"));
        assert!(output.contains("age: number"));
    }

    #[test]
    fn test_ts_enum() {
        let source = "enum Color { Red, Green, Blue, }";
        let program = parse(source).unwrap();
        let output = to_typescript(&program);
        assert!(output.contains("export type Color"));
        assert!(output.contains("\"Red\""));
    }

    #[test]
    fn test_ts_function() {
        let source = "int func add(int a, int b) { pass }";
        let program = parse(source).unwrap();
        let output = to_typescript(&program);
        assert!(output.contains("export function add"));
        assert!(output.contains("a: number"));
    }
}
