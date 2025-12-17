//! Singapore Law Gazette Format Transpiler
//!
//! Generates output in the official Singapore Law Gazette format
//! with proper section numbering, subsections, and legal formatting.

use yuho_core::ast::*;

pub fn to_gazette(program: &Program) -> String {
    let mut output = String::new();
    let mut generator = GazetteGenerator::new();

    // Add header
    output.push_str("SINGAPORE STATUTE\n");
    output.push_str("═══════════════════════════════════════════\n\n");

    for item in &program.items {
        output.push_str(&generator.transpile_item(item));
        output.push('\n');
    }

    output
}

struct GazetteGenerator {
    section_counter: usize,
    subsection_counter: usize,
}

impl GazetteGenerator {
    fn new() -> Self {
        Self {
            section_counter: 0,
            subsection_counter: 0,
        }
    }

    fn next_section(&mut self) -> usize {
        self.section_counter += 1;
        self.subsection_counter = 0;
        self.section_counter
    }

    fn next_subsection(&mut self) -> usize {
        self.subsection_counter += 1;
        self.subsection_counter
    }

    fn letter_for_index(index: usize) -> String {
        if index == 0 {
            return "a".to_string();
        }
        let mut result = String::new();
        let mut n = index;
        while n > 0 {
            result.push((b'a' + ((n - 1) % 26) as u8) as char);
            n = (n - 1) / 26;
        }
        result.chars().rev().collect()
    }

    fn transpile_item(&mut self, item: &Item) -> String {
        match item {
            Item::Struct(s) => self.transpile_struct(s),
            Item::Enum(e) => self.transpile_enum(e),
            Item::Function(f) => self.transpile_function(f),
            Item::Scope(s) => {
                let mut output = String::new();
                for inner in &s.items {
                    output.push_str(&self.transpile_item(inner));
                    output.push('\n');
                }
                output
            },
            Item::Declaration(_) => String::new(),
            Item::TypeAlias(alias) => self.transpile_type_alias(alias),
            Item::LegalTest(_) => String::new(),
            Item::ConflictCheck(_) => String::new(),
            Item::Principle(_) => {
                // Principles are not transpiled to gazette
                String::new()
            },
            Item::Proviso(_) => {
                // Proviso clauses are treated as compile-time directives
                String::new()
            },
        }
    }

    fn transpile_struct(&mut self, s: &StructDefinition) -> String {
        let section_num = self.next_section();
        let mut output = String::new();

        output.push_str(&format!("{}. {}\n\n", section_num, s.name.to_uppercase()));

        // Introduction
        output.push_str(&format!(
            "({}) In this Act, \"{}\", in relation to ",
            self.next_subsection(),
            s.name
        ));

        // Inheritance clause if present
        if let Some(parent) = &s.extends_from {
            output.push_str(&format!("extending {}, ", parent));
        }

        output.push_str("means a matter that satisfies the following conditions:\n\n");

        // List fields as lettered subsections
        for (idx, field) in s.fields.iter().enumerate() {
            let letter = Self::letter_for_index(idx);
            output.push_str(&format!(
                "    ({}) {};\n",
                letter,
                self.transpile_field(field)
            ));
        }

        output.push('\n');
        output
    }

    fn transpile_field(&self, field: &Field) -> String {
        let type_str = self.type_to_gazette(&field.ty);
        let mut output = format!("the {} must be of type {}", field.name, type_str);

        if !field.constraints.is_empty() {
            output.push_str(", and must satisfy");
            for (idx, constraint) in field.constraints.iter().enumerate() {
                if idx > 0 {
                    output.push_str(" and");
                }
                output.push_str(&format!(" {}", self.constraint_to_gazette(constraint)));
            }
        }

        output
    }

    fn transpile_enum(&mut self, e: &EnumDefinition) -> String {
        let section_num = self.next_section();
        let mut output = String::new();

        output.push_str(&format!(
            "{}. {} — INTERPRETATION\n\n",
            section_num,
            e.name.to_uppercase()
        ));

        output.push_str(&format!(
            "({}) For the purposes of this Act, \"{}\" includes —\n\n",
            self.next_subsection(),
            e.name
        ));

        for (idx, variant) in e.variants.iter().enumerate() {
            let letter = Self::letter_for_index(idx);
            output.push_str(&format!("    ({}) {};\n", letter, variant));
        }

        if e.mutually_exclusive {
            output.push_str(&format!(
                "\n({}) The categories in subsection ({}) are mutually exclusive.\n",
                self.next_subsection(),
                self.subsection_counter - 1
            ));
        }

        output.push('\n');
        output
    }

    fn transpile_function(&mut self, f: &FunctionDefinition) -> String {
        let section_num = self.next_section();
        let mut output = String::new();

        output.push_str(&format!(
            "{}. {} — PROCEDURE\n\n",
            section_num,
            f.name.to_uppercase()
        ));

        output.push_str(&format!(
            "({}) Where a matter concerning {} arises —\n\n",
            self.next_subsection(),
            f.name
        ));

        // Parameters as requirements
        for (idx, param) in f.params.iter().enumerate() {
            let letter = Self::letter_for_index(idx);
            let type_str = self.type_to_gazette(&param.ty);
            output.push_str(&format!(
                "    ({}) the {} shall be of type {};\n",
                letter, param.name, type_str
            ));
        }

        // Return type
        output.push_str(&format!(
            "\n({}) The result shall be of type {}.\n",
            self.next_subsection(),
            self.type_to_gazette(&f.return_type)
        ));

        // Requires clause for burden of proof
        if let Some(requires) = &f.requires_clause {
            output.push_str(&format!(
                "\n({}) Provided that {}.\n",
                self.next_subsection(),
                requires
            ));
        }

        output.push('\n');
        output
    }

    fn transpile_type_alias(&mut self, alias: &TypeAliasDefinition) -> String {
        let section_num = self.next_section();
        format!(
            "{}. DEFINITION OF {}\n\n({}) In this Act, \"{}\" means {}.\n\n",
            section_num,
            alias.name.to_uppercase(),
            self.next_subsection(),
            alias.name,
            self.type_to_gazette(&alias.target)
        )
    }

    fn type_to_gazette(&self, ty: &Type) -> String {
        match ty {
            Type::Int | Type::Float => "a numerical value".to_string(),
            Type::Bool => "a boolean value".to_string(),
            Type::String => "a textual description".to_string(),
            Type::Money => "a monetary sum".to_string(),
            Type::Date => "a calendar date".to_string(),
            Type::Duration => "a period of time".to_string(),
            Type::Percent => "a percentage".to_string(),
            Type::Named(name) => format!("a {}", name),
            Type::BoundedInt { min, max } => {
                format!("an integer between {} and {} (inclusive)", min, max)
            },
            Type::NonEmpty(_) => "a non-empty collection".to_string(),
            Type::ValidDate { after, before } => {
                let mut desc = "a date".to_string();
                if let Some(after_date) = after {
                    desc.push_str(&format!(" after {}", after_date));
                }
                if let Some(before_date) = before {
                    desc.push_str(&format!(" before {}", before_date));
                }
                desc
            },
            Type::Positive(_) => "a positive value".to_string(),
            Type::Citation {
                section,
                subsection,
                act,
            } => {
                if subsection.is_empty() {
                    format!("section {} of the {}", section, act)
                } else {
                    format!("section {}({}) of the {}", section, subsection, act)
                }
            },
            Type::TemporalValue {
                inner,
                valid_from,
                valid_until,
            } => {
                let mut desc = format!("a {} valid", self.type_to_gazette(inner));
                if let Some(from) = valid_from {
                    desc.push_str(&format!(" from {}", from));
                }
                if let Some(until) = valid_until {
                    desc.push_str(&format!(" until {}", until));
                }
                desc
            },
            Type::Union(t1, t2) => {
                format!(
                    "either {} or {}",
                    self.type_to_gazette(t1),
                    self.type_to_gazette(t2)
                )
            },
            _ => "a value".to_string(),
        }
    }

    fn constraint_to_gazette(&self, constraint: &Constraint) -> String {
        match constraint {
            Constraint::GreaterThan(expr) => {
                format!("be greater than {}", self.expr_to_gazette(expr))
            },
            Constraint::LessThan(expr) => format!("be less than {}", self.expr_to_gazette(expr)),
            Constraint::GreaterThanOrEqual(expr) => {
                format!("be at least {}", self.expr_to_gazette(expr))
            },
            Constraint::LessThanOrEqual(expr) => {
                format!("be at most {}", self.expr_to_gazette(expr))
            },
            Constraint::Equal(expr) => format!("be equal to {}", self.expr_to_gazette(expr)),
            Constraint::NotEqual(expr) => format!("not be equal to {}", self.expr_to_gazette(expr)),
            Constraint::Before(date) => format!("be before {}", self.expr_to_gazette(date)),
            Constraint::After(date) => format!("be after {}", self.expr_to_gazette(date)),
            Constraint::Between { start, end } => {
                format!(
                    "be between {} and {}",
                    self.expr_to_gazette(start),
                    self.expr_to_gazette(end)
                )
            },
            Constraint::InRange { min, max } => {
                format!(
                    "be between {} and {} (inclusive)",
                    self.expr_to_gazette(min),
                    self.expr_to_gazette(max)
                )
            },
            Constraint::And(c1, c2) => {
                format!(
                    "{} and {}",
                    self.constraint_to_gazette(c1),
                    self.constraint_to_gazette(c2)
                )
            },
            Constraint::Or(c1, c2) => {
                format!(
                    "either {} or {}",
                    self.constraint_to_gazette(c1),
                    self.constraint_to_gazette(c2)
                )
            },
            _ => "satisfy additional conditions".to_string(),
        }
    }

    fn expr_to_gazette(&self, expr: &Expr) -> String {
        match expr {
            Expr::Literal(lit) => format!("{:?}", lit),
            Expr::Identifier(id) => id.clone(),
            Expr::FieldAccess(obj, field) => {
                format!("the {} of {}", field, self.expr_to_gazette(obj))
            },
            Expr::Binary(left, op, right) => {
                format!(
                    "{} {:?} {}",
                    self.expr_to_gazette(left),
                    op,
                    self.expr_to_gazette(right)
                )
            },
            _ => "a value".to_string(),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_letter_generation() {
        assert_eq!(GazetteGenerator::letter_for_index(0), "a");
        assert_eq!(GazetteGenerator::letter_for_index(1), "b");
        assert_eq!(GazetteGenerator::letter_for_index(25), "z");
    }

    #[test]
    fn test_section_numbering() {
        let mut gen = GazetteGenerator::new();
        let s1 = gen.next_section();
        let s2 = gen.next_section();
        let sub1 = gen.next_subsection();
        let sub2 = gen.next_subsection();
        assert_eq!(s1, 1);
        assert_eq!(s2, 2);
        assert_eq!(sub1, 1);
        assert_eq!(sub2, 2);
    }
}
