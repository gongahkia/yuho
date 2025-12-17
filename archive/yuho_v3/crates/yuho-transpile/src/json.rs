use serde_json::{json, Value};
use yuho_core::ast::*;

/// Generate JSON representation of Yuho program
pub fn to_json(program: &Program) -> String {
    serde_json::to_string_pretty(program).unwrap_or_else(|_| "{}".to_string())
}

/// Generate simplified JSON suitable for data interchange
pub fn to_interchange_json(program: &Program) -> String {
    let mut gen = JsonGenerator::new();
    let value = gen.generate(program);
    serde_json::to_string_pretty(&value).unwrap_or_else(|_| "{}".to_string())
}

struct JsonGenerator {
    // State if needed
}

impl JsonGenerator {
    fn new() -> Self {
        Self {}
    }

    fn generate(&mut self, program: &Program) -> Value {
        let items: Vec<Value> = program
            .items
            .iter()
            .map(|item| self.emit_item(item))
            .collect();

        json!({
            "version": "yuho-2",
            "items": items
        })
    }

    fn emit_item(&mut self, item: &Item) -> Value {
        match item {
            Item::Struct(s) => self.emit_struct(s),
            Item::Enum(e) => self.emit_enum(e),
            Item::Scope(s) => self.emit_scope(s),
            Item::Function(f) => self.emit_function(f),
            Item::Declaration(d) => self.emit_declaration(d),
            Item::TypeAlias(alias) => self.emit_type_alias(alias),
            Item::LegalTest(test) => self.emit_legal_test(test),
            Item::ConflictCheck(check) => json!({
                "type": "conflict_check",
                "file1": check.file1,
                "file2": check.file2
            }),
            Item::Principle(p) => json!({
                "kind": "principle",
                "name": p.name,
                "body": format!("{:?}", p.body)
            }),
            Item::Proviso(pr) => json!({
                "kind": "proviso",
                "condition": format!("{:?}", pr.condition),
                "exception": format!("{:?}", pr.exception),
                "applies_to": pr.applies_to
            }),
        }
    }

    fn emit_struct(&mut self, s: &StructDefinition) -> Value {
        let fields: Vec<Value> = s
            .fields
            .iter()
            .map(|f| {
                json!({
                    "name": f.name,
                    "type": self.type_to_json(&f.ty)
                })
            })
            .collect();

        json!({
            "kind": "struct",
            "name": s.name,
            "type_params": s.type_params,
            "fields": fields
        })
    }

    fn emit_enum(&mut self, e: &EnumDefinition) -> Value {
        json!({
            "kind": "enum",
            "name": e.name,
            "variants": e.variants,
            "mutually_exclusive": e.mutually_exclusive
        })
    }

    fn emit_scope(&mut self, s: &ScopeDefinition) -> Value {
        let items: Vec<Value> = s.items.iter().map(|item| self.emit_item(item)).collect();

        json!({
            "kind": "scope",
            "name": s.name,
            "items": items
        })
    }

    fn emit_function(&mut self, f: &FunctionDefinition) -> Value {
        let params: Vec<Value> = f
            .params
            .iter()
            .map(|p| {
                json!({
                    "name": p.name,
                    "type": self.type_to_json(&p.ty)
                })
            })
            .collect();

        json!({
            "kind": "function",
            "name": f.name,
            "type_params": f.type_params,
            "params": params,
            "returnType": self.type_to_json(&f.return_type)
        })
    }

    fn emit_declaration(&mut self, d: &Declaration) -> Value {
        json!({
            "kind": "declaration",
            "name": d.name,
            "type": self.type_to_json(&d.ty),
            "value": self.expr_to_json(&d.value)
        })
    }

    fn emit_type_alias(&mut self, alias: &TypeAliasDefinition) -> Value {
        json!({
            "kind": "type_alias",
            "name": alias.name,
            "type_params": alias.type_params,
            "target": self.type_to_json(&alias.target)
        })
    }

    fn emit_legal_test(&mut self, test: &LegalTestDefinition) -> Value {
        let requirements: Vec<Value> = test
            .requirements
            .iter()
            .map(|req| {
                json!({
                    "name": req.name,
                    "type": self.type_to_json(&req.ty)
                })
            })
            .collect();

        json!({
            "kind": "legal_test",
            "name": test.name,
            "requirements": requirements,
            "semantics": "conjunctive"
        })
    }

    fn type_to_json(&self, ty: &Type) -> Value {
        match ty {
            Type::Int => json!("int"),
            Type::Float => json!("float"),
            Type::Bool => json!("bool"),
            Type::String => json!("string"),
            Type::Money => json!("money"),
            Type::Date => json!("date"),
            Type::Duration => json!("duration"),
            Type::Percent => json!("percent"),
            Type::Pass => json!("pass"),
            Type::Named(name) => json!({"named": name}),
            Type::Union(a, b) => json!({
                "union": [self.type_to_json(a), self.type_to_json(b)]
            }),

            // Dependent types (Phase 1)
            Type::BoundedInt { min, max } => json!({
                "bounded_int": {"min": min, "max": max}
            }),
            Type::NonEmpty(inner) => json!({
                "non_empty": self.type_to_json(inner)
            }),
            Type::ValidDate { after, before } => json!({
                "valid_date": {"after": after, "before": before}
            }),
            Type::Positive(inner) => json!({
                "positive": self.type_to_json(inner)
            }),
            Type::Array(inner) => json!({
                "array": self.type_to_json(inner)
            }),
            Type::MoneyWithCurrency(currency) => json!({
                "money": {"currency": currency}
            }),
            Type::Citation {
                section,
                subsection,
                act,
            } => json!({
                "citation": {
                    "section": section,
                    "subsection": subsection,
                    "act": act
                }
            }),
            Type::TemporalValue {
                inner,
                valid_from,
                valid_until,
            } => json!({
                "temporal": {
                    "inner": self.type_to_json(inner),
                    "valid_from": valid_from,
                    "valid_until": valid_until
                }
            }),
            Type::TypeVariable(name) => json!({
                "type": "type_variable",
                "name": name
            }),
            Type::Generic { name, args } => json!({
                "type": "generic",
                "name": name,
                "args": args.iter().map(|a| self.type_to_json(a)).collect::<Vec<_>>()
            }),
        }
    }

    fn expr_to_json(&self, expr: &Expr) -> Value {
        match expr {
            Expr::Literal(lit) => self.literal_to_json(lit),
            Expr::Identifier(name) => json!({"identifier": name}),
            Expr::Binary(l, op, r) => json!({
                "binary": {
                    "op": format!("{:?}", op),
                    "left": self.expr_to_json(l),
                    "right": self.expr_to_json(r)
                }
            }),
            Expr::Unary(op, e) => json!({
                "unary": {
                    "op": format!("{:?}", op),
                    "operand": self.expr_to_json(e)
                }
            }),
            Expr::Call(name, args) => {
                let arg_values: Vec<Value> = args.iter().map(|a| self.expr_to_json(a)).collect();
                json!({
                    "call": {
                        "function": name,
                        "arguments": arg_values
                    }
                })
            },
            Expr::FieldAccess(obj, field) => json!({
                "fieldAccess": {
                    "object": self.expr_to_json(obj),
                    "field": field
                }
            }),
            Expr::StructInit(init) => {
                let fields: Vec<Value> = init
                    .fields
                    .iter()
                    .map(|(k, v)| {
                        json!({
                            "name": k,
                            "value": self.expr_to_json(v)
                        })
                    })
                    .collect();
                json!({
                    "structInit": {
                        "name": init.name,
                        "fields": fields
                    }
                })
            },
            Expr::Match(m) => {
                let cases: Vec<Value> = m
                    .cases
                    .iter()
                    .map(|c| {
                        let mut case_obj = json!({
                            "pattern": self.pattern_to_json(&c.pattern),
                            "consequence": self.expr_to_json(&c.consequence)
                        });

                        if let Some(guard) = &c.guard {
                            case_obj
                                .as_object_mut()
                                .unwrap()
                                .insert("guard".to_string(), self.expr_to_json(guard));
                        }

                        case_obj
                    })
                    .collect();
                json!({
                    "match": {
                        "scrutinee": self.expr_to_json(&m.scrutinee),
                        "cases": cases
                    }
                })
            },
            Expr::Forall { var, ty, body } => json!({
                "forall": {
                    "variable": var,
                    "type": self.type_to_json(ty),
                    "body": self.expr_to_json(body)
                }
            }),
            Expr::Exists { var, ty, body } => json!({
                "exists": {
                    "variable": var,
                    "type": self.type_to_json(ty),
                    "body": self.expr_to_json(body)
                }
            }),
        }
    }

    fn literal_to_json(&self, lit: &Literal) -> Value {
        match lit {
            Literal::Int(n) => json!({"int": n}),
            Literal::Float(n) => json!({"float": n}),
            Literal::Bool(b) => json!({"bool": b}),
            Literal::String(s) => json!({"string": s}),
            Literal::Money(n) => json!({"money": n}),
            Literal::Date(d) => json!({"date": d}),
            Literal::Duration(d) => json!({"duration": d}),
            Literal::Percent(p) => json!({"percent": p}),
            Literal::Pass => json!({"pass": null}),
        }
    }

    fn pattern_to_json(&self, pattern: &Pattern) -> Value {
        match pattern {
            Pattern::Literal(lit) => self.literal_to_json(lit),
            Pattern::Identifier(name) => json!({"identifier": name}),
            Pattern::Wildcard => json!({"wildcard": true}),
            Pattern::Satisfies(test_name) => json!({"satisfies": test_name}),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use yuho_core::parse;

    #[test]
    fn test_json_struct() {
        let source = "struct Person { string name, int age, }";
        let program = parse(source).unwrap();
        let output = to_interchange_json(&program);
        assert!(output.contains("\"kind\": \"struct\""));
        assert!(output.contains("\"name\": \"Person\""));
    }

    #[test]
    fn test_json_enum() {
        let source = "enum Color { Red, Green, Blue, }";
        let program = parse(source).unwrap();
        let output = to_interchange_json(&program);
        assert!(output.contains("\"kind\": \"enum\""));
        assert!(output.contains("\"Red\""));
    }

    #[test]
    fn test_json_declaration() {
        let source = "int x := 42";
        let program = parse(source).unwrap();
        let output = to_interchange_json(&program);
        assert!(output.contains("\"kind\": \"declaration\""));
        assert!(output.contains("\"int\": 42"));
    }
}
