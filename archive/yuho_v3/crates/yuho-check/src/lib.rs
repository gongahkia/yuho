use chrono::NaiveDate;
use std::collections::HashMap;
use thiserror::Error;
use yuho_core::ast::*;
use yuho_core::resolver::ResolvedProgram;

pub mod citation_validator;
pub mod conflict_detection;
pub mod control_flow;
pub mod hierarchy_checker;
pub mod interpretation_rules;
pub mod temporal_checker;

const DOCS_BASE: &str = "https://github.com/gongahkia/yuho-2/wiki";

#[derive(Error, Debug, Clone)]
pub enum CheckError {
    #[error("\n╭─ Type Mismatch\n│\n│  Expected: {expected}\n│  Got:      {got}\n│\n├─ How to fix:\n│  • Ensure the expression evaluates to {expected}\n│  • Check if type conversion is needed\n│  • Verify function return types match\n│\n├─ Examples:\n│  ✓ Correct:   int age := 25\n│  ✗ Incorrect: int age := \"25\"  // string, not int\n│\n╰─ Documentation: {}/Type-System", DOCS_BASE)]
    TypeMismatch { expected: String, got: String },

    #[error("\n╭─ Undefined Symbol: '{0}'\n│\n├─ How to fix:\n│  • Make sure '{0}' is defined before use\n│  • Check for typos in the identifier name\n│  • Verify '{0}' is in the current scope\n│  • If imported, check the import statement\n│\n├─ Did you mean?\n│  • Check for similar names in scope\n│  • Ensure proper capitalization\n│\n╰─ Documentation: {}/Variables-and-Scoping", DOCS_BASE)]
    Undefined(String),

    #[error("\n╭─ Duplicate Definition: '{0}'\n│\n├─ How to fix:\n│  • '{0}' is already defined in this scope\n│  • Choose a unique name (e.g., '{0}_updated', '{0}_v2')\n│  • Remove one of the duplicate definitions\n│  • Use different scopes if both definitions are needed\n│\n╰─ Documentation: {}/Variables-and-Scoping", DOCS_BASE)]
    Duplicate(String),

    #[error("\n╭─ Invalid Field\n│\n│  Struct: {struct_name}\n│  Field:  {field}\n│\n├─ How to fix:\n│  • Check the struct definition for valid field names\n│  • Field names are case-sensitive\n│  • Remove '{field}' or add it to the struct definition\n│\n├─ Example:\n│  struct Person {{\n│    string name,\n│    int age,\n│  }}\n│  // Only 'name' and 'age' are valid fields\n│\n╰─ Documentation: {}/Structs", DOCS_BASE)]
    InvalidField { struct_name: String, field: String },

    #[error("\n╭─ Missing Required Field\n│\n│  Struct: {struct_name}\n│  Missing: {field}\n│\n├─ How to fix:\n│  • Add '{field}' to the struct initialization\n│  • All struct fields must be provided\n│\n├─ Example:\n│  Person p := Person {{\n│    name := \"Alice\",\n│    age := 30,  // Don't forget this field!\n│  }}\n│\n╰─ Documentation: {}/Structs", DOCS_BASE)]
    MissingField { struct_name: String, field: String },

    #[error("\n╭─ Non-Exhaustive Match\n│\n├─ How to fix:\n│  • Add a wildcard case to handle all possibilities\n│  • Match expressions must cover all possible values\n│\n├─ Example:\n│  match status {{\n│    case \"active\" := process()\n│    case \"inactive\" := skip()\n│    case _ := handleUnknown()  // Wildcard catches everything else\n│  }}\n│\n╰─ Documentation: {}/Pattern-Matching", DOCS_BASE)]
    NonExhaustiveMatch,

    #[error("\n╭─ Unreachable Case After Wildcard\n│\n├─ How to fix:\n│  • Remove cases after the wildcard '_' pattern\n│  • Move the wildcard case to the end\n│  • The wildcard matches everything, making later cases unreachable\n│\n├─ Example:\n│  ✓ Correct:\n│    case \"active\" := process()\n│    case _ := handleOther()  // Wildcard at end\n│\n│  ✗ Incorrect:\n│    case _ := handleOther()  // Wildcard first\n│    case \"active\" := process()  // Unreachable!\n│\n╰─ Documentation: {}/Pattern-Matching", DOCS_BASE)]
    UnreachableCase,

    #[error("\n╭─ Invalid BoundedInt Range\n│\n│  Min: {min}\n│  Max: {max}\n│\n├─ Problem:\n│  • Minimum value must be less than maximum value\n│  • Got min >= max, which is invalid\n│\n├─ How to fix:\n│  • Use BoundedInt<{min}, {max}> if you meant min={min}, max={max}\n│  • Swap the values: BoundedInt<{max}, {min}>\n│\n├─ Examples:\n│  ✓ Correct:   BoundedInt<0, 100>    // Age 0-100\n│  ✓ Correct:   BoundedInt<-273, 100> // Celsius temp\n│  ✗ Incorrect: BoundedInt<100, 0>    // Max < Min!\n│\n╰─ Documentation: {}/Dependent-Types", DOCS_BASE)]
    InvalidBoundedIntRange { min: i64, max: i64 },

    #[error("\n╭─ Invalid Constraint\n│\n│  {0}\n│\n├─ How to fix:\n│  • Review the constraint syntax\n│  • Ensure comparison operators are valid (>, <, >=, <=, ==, !=)\n│  • Check that constraint expressions are well-formed\n│\n├─ Example:\n│  BoundedInt<18, 65> age where age >= 21  // Valid constraint\n│\n╰─ Documentation: {}/Dependent-Types#Constraints", DOCS_BASE)]
    InvalidConstraint(String),

    #[error("\n╭─ Constraint Violation\n│\n│  {0}\n│\n├─ How to fix:\n│  • Ensure values satisfy the type constraints\n│  • Check that literal values are within allowed ranges\n│  • Verify dependent type requirements are met\n│\n├─ Examples:\n│  BoundedInt<0, 100> age := 150  // ✗ Violates max constraint\n│  BoundedInt<0, 100> age := 50   // ✓ Within bounds\n│  Positive<int> count := -5      // ✗ Violates positive constraint\n│  Positive<int> count := 5       // ✓ Positive value\n│\n╰─ Documentation: {}/Dependent-Types#Constraints", DOCS_BASE)]
    ConstraintViolation(String),

    #[error("\n╭─ Generic Type Arity Mismatch\n│\n│  Type: {name}\n│  Expected: {expected} type parameters\n│  Got:      {got} type parameters\n│\n├─ How to fix:\n│  • Provide exactly {expected} type arguments\n│  • Check the struct/function definition\n│\n├─ Examples:\n│  ✓ Correct:   Container<int>     // 1 type parameter\n│  ✓ Correct:   Pair<int, string>  // 2 type parameters\n│  ✗ Incorrect: Container<int, string>  // Too many!\n│\n╰─ Documentation: {}/Generic-Types", DOCS_BASE)]
    GenericArityMismatch {
        name: String,
        expected: usize,
        got: usize,
    },

    #[error("\n╭─ Unbound Type Variable: '{0}'\n│\n├─ How to fix:\n│  • Type variable '{0}' is not in scope\n│  • Add '{0}' to function/struct type parameters\n│  • Check for typos in the type variable name\n│\n├─ Example:\n│  func map<T, U>(Array<T> items) -> Array<U>  // T, U are bound\n│\n╰─ Documentation: {}/Generic-Types", DOCS_BASE)]
    UnboundTypeVariable(String),
}

pub type CheckResult<T> = Result<T, CheckError>;

#[derive(Debug, Clone)]
pub struct StructInfo {
    pub fields: Vec<(String, Type, Vec<Constraint>)>, // (name, type, constraints)
    pub type_params: Vec<String>,                     // Generic type parameters
}

#[derive(Debug, Clone)]
pub struct EnumInfo {
    pub variants: Vec<String>,
}

#[derive(Debug, Clone)]
pub struct LegalTestInfo {
    pub requirements: Vec<(String, Type)>, // (name, type)
}

#[derive(Debug, Default)]
pub struct SymbolTable {
    scopes: Vec<HashMap<String, Type>>,
    structs: HashMap<String, StructInfo>,
    enums: HashMap<String, EnumInfo>,
    functions: HashMap<String, (Vec<Type>, Type)>, // (param_types, return_type)
    type_params: Vec<Vec<String>>,                 // Stack of type parameter scopes
    type_aliases: HashMap<String, Type>,           // Type alias definitions
    legal_tests: HashMap<String, LegalTestInfo>,   // Legal test definitions
}

impl SymbolTable {
    pub fn new() -> Self {
        Self {
            scopes: vec![HashMap::new()],
            structs: HashMap::new(),
            enums: HashMap::new(),
            functions: HashMap::new(),
            type_params: vec![],
            type_aliases: HashMap::new(),
            legal_tests: HashMap::new(),
        }
    }

    pub fn push_scope(&mut self) {
        self.scopes.push(HashMap::new());
    }

    pub fn pop_scope(&mut self) {
        self.scopes.pop();
    }

    pub fn push_type_params(&mut self, params: Vec<String>) {
        self.type_params.push(params);
    }

    pub fn pop_type_params(&mut self) {
        self.type_params.pop();
    }

    pub fn is_type_param_in_scope(&self, name: &str) -> bool {
        for params in self.type_params.iter().rev() {
            if params.contains(&name.to_string()) {
                return true;
            }
        }
        false
    }

    pub fn define(&mut self, name: String, ty: Type) -> CheckResult<()> {
        let scope = self
            .scopes
            .last_mut()
            .expect("Scope stack should never be empty - push_scope() must be called first");
        if scope.contains_key(&name) {
            return Err(CheckError::Duplicate(name));
        }
        scope.insert(name, ty);
        Ok(())
    }

    pub fn lookup(&self, name: &str) -> Option<&Type> {
        for scope in self.scopes.iter().rev() {
            if let Some(ty) = scope.get(name) {
                return Some(ty);
            }
        }
        None
    }

    pub fn define_struct(
        &mut self,
        name: String,
        fields: Vec<(String, Type, Vec<Constraint>)>,
        type_params: Vec<String>,
    ) -> CheckResult<()> {
        if self.structs.contains_key(&name) {
            return Err(CheckError::Duplicate(name));
        }
        self.structs.insert(
            name,
            StructInfo {
                fields,
                type_params,
            },
        );
        Ok(())
    }

    pub fn get_struct(&self, name: &str) -> Option<&StructInfo> {
        self.structs.get(name)
    }

    pub fn define_enum(&mut self, name: String, variants: Vec<String>) -> CheckResult<()> {
        if self.enums.contains_key(&name) {
            return Err(CheckError::Duplicate(name));
        }
        self.enums.insert(name, EnumInfo { variants });
        Ok(())
    }

    pub fn get_enum(&self, name: &str) -> Option<&EnumInfo> {
        self.enums.get(name)
    }

    pub fn define_function(
        &mut self,
        name: String,
        param_types: Vec<Type>,
        return_type: Type,
    ) -> CheckResult<()> {
        if self.functions.contains_key(&name) {
            return Err(CheckError::Duplicate(name));
        }
        self.functions.insert(name, (param_types, return_type));
        Ok(())
    }

    pub fn define_type_alias(&mut self, name: String, target: Type) -> CheckResult<()> {
        if self.type_aliases.contains_key(&name) {
            return Err(CheckError::Duplicate(name));
        }
        self.type_aliases.insert(name, target);
        Ok(())
    }

    pub fn resolve_type_alias(&self, name: &str) -> Option<&Type> {
        self.type_aliases.get(name)
    }

    pub fn define_legal_test(
        &mut self,
        name: String,
        requirements: Vec<(String, Type)>,
    ) -> CheckResult<()> {
        if self.legal_tests.contains_key(&name) {
            return Err(CheckError::Duplicate(name));
        }
        self.legal_tests
            .insert(name, LegalTestInfo { requirements });
        Ok(())
    }

    pub fn get_legal_test(&self, name: &str) -> Option<&LegalTestInfo> {
        self.legal_tests.get(name)
    }
}

pub struct Checker {
    symbols: SymbolTable,
    errors: Vec<CheckError>,
    control_flow: control_flow::ControlFlowAnalyzer,
    quantifier_vars: Vec<HashMap<String, Type>>, // Stack of quantifier variable scopes
}

impl Checker {
    pub fn new() -> Self {
        Self {
            symbols: SymbolTable::new(),
            errors: Vec::new(),
            control_flow: control_flow::ControlFlowAnalyzer::new(),
            quantifier_vars: Vec::new(),
        }
    }

    fn push_quantifier_scope(&mut self) {
        self.quantifier_vars.push(HashMap::new());
    }

    fn pop_quantifier_scope(&mut self) {
        self.quantifier_vars.pop();
    }

    fn define_quantifier_var(&mut self, name: String, ty: Type) {
        if let Some(scope) = self.quantifier_vars.last_mut() {
            scope.insert(name, ty);
        }
    }

    fn lookup_quantifier_var(&self, name: &str) -> Option<&Type> {
        for scope in self.quantifier_vars.iter().rev() {
            if let Some(ty) = scope.get(name) {
                return Some(ty);
            }
        }
        None
    }

    pub fn check_program(&mut self, program: &Program) -> Vec<CheckError> {
        // First pass: collect all type definitions
        for item in &program.items {
            self.collect_definitions(item);
        }

        // Second pass: check all items
        for item in &program.items {
            self.check_item(item);
        }

        std::mem::take(&mut self.errors)
    }

    /// Checks a program with all imports resolved
    /// This merges symbol tables from imported modules before checking
    pub fn check_with_imports(&mut self, resolved: &ResolvedProgram) -> Vec<CheckError> {
        // First, collect definitions from all imported modules
        for imported_program in resolved.imported_programs.values() {
            for item in &imported_program.items {
                self.collect_definitions(item);
            }
        }

        // Then collect definitions from the main program
        for item in &resolved.main_program.items {
            self.collect_definitions(item);
        }

        // Check all imported modules
        for imported_program in resolved.imported_programs.values() {
            for item in &imported_program.items {
                self.check_item(item);
            }
        }

        // Finally, check the main program
        for item in &resolved.main_program.items {
            self.check_item(item);
        }

        std::mem::take(&mut self.errors)
    }

    fn collect_definitions(&mut self, item: &Item) {
        match item {
            Item::Struct(s) => {
                let fields: Vec<_> = s
                    .fields
                    .iter()
                    .map(|f| (f.name.clone(), f.ty.clone(), f.constraints.clone()))
                    .collect();
                if let Err(e) =
                    self.symbols
                        .define_struct(s.name.clone(), fields, s.type_params.clone())
                {
                    self.errors.push(e);
                }
                // Note: Generic type parameters validated during instantiation
            },
            Item::Enum(e) => {
                if let Err(err) = self.symbols.define_enum(e.name.clone(), e.variants.clone()) {
                    self.errors.push(err);
                }
            },
            Item::Function(f) => {
                let param_types: Vec<_> = f.params.iter().map(|p| p.ty.clone()).collect();
                if let Err(e) =
                    self.symbols
                        .define_function(f.name.clone(), param_types, f.return_type.clone())
                {
                    self.errors.push(e);
                }
                // Note: Generic type parameters validated during type checking
            },
            Item::Scope(s) => {
                for inner in &s.items {
                    self.collect_definitions(inner);
                }
            },
            Item::LegalTest(lt) => {
                let requirements: Vec<_> = lt
                    .requirements
                    .iter()
                    .map(|r| (r.name.clone(), r.ty.clone()))
                    .collect();
                if let Err(e) = self
                    .symbols
                    .define_legal_test(lt.name.clone(), requirements)
                {
                    self.errors.push(e);
                }
            },
            Item::Declaration(_) => {},
            Item::TypeAlias(alias) => {
                // Register type alias
                if let Err(e) = self
                    .symbols
                    .define_type_alias(alias.name.clone(), alias.target.clone())
                {
                    self.errors.push(e);
                }
            },
            Item::ConflictCheck(_) => {
                // Conflict checks don't define any symbols
                // They are processed during multi-file analysis
            },
            Item::Principle(_) => {
                // Principles don't define symbols in the type environment
                // They are verified separately via Z3
            },
            Item::Proviso(_) => {
                // Provisos don't define symbols
            },
        }
    }

    fn check_item(&mut self, item: &Item) {
        match item {
            Item::Struct(s) => {
                // Check extends clause if present
                if let Some(parent) = &s.extends_from {
                    // Verify parent struct exists
                    if !self.symbols.structs.contains_key(parent) {
                        self.errors.push(CheckError::Undefined(format!(
                            "Parent struct '{}' not found",
                            parent
                        )));
                    }
                    // TODO: Inherit fields and constraints from parent
                }

                // Push type parameters into scope
                self.symbols.push_type_params(s.type_params.clone());

                // Check field types are valid
                for field in &s.fields {
                    self.check_type(&field.ty);
                    // Validate constraints are well-formed
                    for constraint in &field.constraints {
                        self.validate_constraint(constraint, &field.ty);
                    }
                }

                // Pop type parameters
                self.symbols.pop_type_params();
            },
            Item::Enum(_) => {
                // Enums are already validated during collection
            },
            Item::Declaration(d) => {
                self.check_declaration(d);
            },
            Item::Scope(s) => {
                self.symbols.push_scope();
                for inner in &s.items {
                    self.check_item(inner);
                }
                self.symbols.pop_scope();
            },
            Item::Function(f) => {
                self.check_function(f);
            },
            Item::LegalTest(lt) => {
                // Check that all requirement types are valid
                for req in &lt.requirements {
                    self.check_type(&req.ty);
                    // Verify requirement types are boolean (legal tests are conjunctive boolean checks)
                    if !matches!(req.ty, Type::Bool) {
                        self.errors.push(CheckError::TypeMismatch {
                            expected: "bool".to_string(),
                            got: format!("{:?}", req.ty),
                        });
                    }
                }
            },
            Item::TypeAlias(alias) => {
                // Type aliases are just definitions, no further checking needed
                // Push type parameters for the alias
                self.symbols.push_type_params(alias.type_params.clone());
                self.check_type(&alias.target);
                self.symbols.pop_type_params();
            },
            Item::ConflictCheck(_) => {
                // Conflict checks are handled separately by the multi-file analyzer
                // This is a placeholder for now - actual conflict detection happens
                // when multiple files are loaded and analyzed together
            },
            Item::Principle(p) => {
                // Type check the principle body expression
                self.check_expr(&p.body);
                // Full verification happens via Z3 in the verify command
            },
            Item::Proviso(pr) => {
                // Type check the proviso condition
                self.check_expr(&pr.condition);
                // Check exception statements
                for stmt in &pr.exception {
                    self.check_statement(stmt);
                }
            },
        }
    }

    fn check_declaration(&mut self, decl: &Declaration) {
        // Check type annotation is valid
        self.check_type(&decl.ty);

        // Check expression type
        self.check_expr(&decl.value);

        // Register the variable
        if let Err(e) = self.symbols.define(decl.name.clone(), decl.ty.clone()) {
            self.errors.push(e);
        }
    }

    fn check_function(&mut self, func: &FunctionDefinition) {
        self.symbols.push_scope();

        // Push type parameters into scope
        self.symbols.push_type_params(func.type_params.clone());

        // Register parameters
        for param in &func.params {
            if let Err(e) = self.symbols.define(param.name.clone(), param.ty.clone()) {
                self.errors.push(e);
            }
        }

        // Check body statements
        for stmt in &func.body {
            self.check_statement(stmt);
        }

        // Pop type parameters
        self.symbols.pop_type_params();
        self.symbols.pop_scope();
    }

    fn check_statement(&mut self, stmt: &Statement) {
        match stmt {
            Statement::Declaration(d) => self.check_declaration(d),
            Statement::Assignment(a) => {
                if self.symbols.lookup(&a.target).is_none() {
                    self.errors.push(CheckError::Undefined(a.target.clone()));
                }
                self.check_expr(&a.value);
            },
            Statement::Return(expr) => {
                self.check_expr(expr);
            },
            Statement::Match(m) => {
                self.check_match(m);
            },
            Statement::Pass => {},
        }
    }

    fn check_expr(&mut self, expr: &Expr) {
        match expr {
            Expr::Literal(_) => {},
            Expr::Identifier(name) => {
                if self.symbols.lookup(name).is_none() && self.symbols.get_enum(name).is_none() {
                    self.errors.push(CheckError::Undefined(name.clone()));
                }
            },
            Expr::Binary(left, _, right) => {
                self.check_expr(left);
                self.check_expr(right);
            },
            Expr::Unary(_, inner) => {
                self.check_expr(inner);
            },
            Expr::Call(name, args) => {
                if self.symbols.functions.get(name).is_none() {
                    self.errors.push(CheckError::Undefined(name.clone()));
                }
                for arg in args {
                    self.check_expr(arg);
                }
            },
            Expr::FieldAccess(obj, field) => {
                self.check_expr(obj);
                // Validate field exists on struct type
                if let Some(obj_type) = self.infer_expr_type(obj) {
                    if let Some(struct_name) = self.get_struct_name(&obj_type) {
                        if let Some(struct_info) = self.symbols.get_struct(&struct_name) {
                            let field_exists = struct_info
                                .fields
                                .iter()
                                .any(|(name, _, _)| name == field);
                            if !field_exists {
                                self.errors.push(CheckError::InvalidField {
                                    struct_name: struct_name.clone(),
                                    field: field.clone(),
                                });
                            }
                        }
                    }
                }
            },
            Expr::StructInit(init) => {
                self.check_struct_init(init);
            },
            Expr::Match(m) => {
                self.check_match(m);
            },
            Expr::Forall { var, ty, body } => {
                // Check quantified type is valid
                self.check_type(ty);
                // Push variable into scope
                self.symbols.push_scope();
                if let Err(e) = self.symbols.define(var.clone(), ty.clone()) {
                    self.errors.push(e);
                }
                // Check body expression
                self.check_expr(body);
                self.symbols.pop_scope();
            },
            Expr::Exists { var, ty, body } => {
                // Check quantified type is valid
                self.check_type(ty);
                // Push variable into scope
                self.symbols.push_scope();
                if let Err(e) = self.symbols.define(var.clone(), ty.clone()) {
                    self.errors.push(e);
                }
                // Check body expression
                self.check_expr(body);
                self.symbols.pop_scope();
            },
        }
    }

    fn check_struct_init(&mut self, init: &StructInit) {
        if !init.name.is_empty() {
            if let Some(struct_info) = self.symbols.get_struct(&init.name).cloned() {
                let defined_fields: std::collections::HashSet<_> = struct_info
                    .fields
                    .iter()
                    .map(|(n, _, _)| n.as_str())
                    .collect();

                let provided_fields: std::collections::HashSet<_> =
                    init.fields.iter().map(|(n, _)| n.as_str()).collect();

                // Check each provided field is valid and satisfies constraints
                for (field_name, value) in &init.fields {
                    if !defined_fields.contains(field_name.as_str()) {
                        self.errors.push(CheckError::InvalidField {
                            struct_name: init.name.clone(),
                            field: field_name.clone(),
                        });
                    }
                    self.check_expr(value);

                    // Check constraints for this field
                    if let Some((_, field_type, constraints)) = struct_info
                        .fields
                        .iter()
                        .find(|(name, _, _)| name == field_name)
                    {
                        self.check_constraints_satisfied(constraints, value, field_type);
                    }
                }

                // Check for missing required fields
                for (field_name, _field_type, _constraints) in &struct_info.fields {
                    if !provided_fields.contains(field_name.as_str()) {
                        self.errors.push(CheckError::MissingField {
                            struct_name: init.name.clone(),
                            field: field_name.clone(),
                        });
                    }
                }
            } else {
                self.errors.push(CheckError::Undefined(init.name.clone()));
            }
        } else {
            // Anonymous struct init
            for (_, value) in &init.fields {
                self.check_expr(value);
            }
        }
    }

    fn check_match(&mut self, m: &MatchExpr) {
        self.check_expr(&m.scrutinee);

        let mut has_wildcard = false;
        let mut after_wildcard = false;

        for case in &m.cases {
            if after_wildcard {
                self.errors.push(CheckError::UnreachableCase);
            }

            // Check pattern validity
            match &case.pattern {
                Pattern::Wildcard => {
                    has_wildcard = true;
                    after_wildcard = true;
                },
                Pattern::Satisfies(test_name) => {
                    // Verify legal test exists
                    if self.symbols.get_legal_test(test_name).is_none() {
                        self.errors.push(CheckError::Undefined(test_name.clone()));
                    }
                },
                _ => {},
            }

            self.check_expr(&case.consequence);
        }

        if !has_wildcard {
            self.errors.push(CheckError::NonExhaustiveMatch);
        }
    }

    /// Verify that a struct initialization satisfies a legal test's requirements
    /// This is used when matching against Pattern::Satisfies
    fn verify_satisfies_legal_test(&mut self, _struct_name: &str, _test_name: &str) -> bool {
        // This would check if the struct has all required fields with appropriate values
        // For now, we just return true - full implementation would verify:
        // 1. Struct has all required boolean fields from the legal test
        // 2. All fields evaluate to true (conjunctive requirement)
        // TODO: Implement full verification logic
        true
    }

    fn check_type(&mut self, ty: &Type) {
        match ty {
            Type::Named(name) => {
                // Check if it's a type alias first
                if self.symbols.resolve_type_alias(name).is_some() {
                    // Type alias found, it's valid
                    return;
                }
                // Otherwise check if it's a struct or enum
                if self.symbols.get_struct(name).is_none() && self.symbols.get_enum(name).is_none()
                {
                    self.errors.push(CheckError::Undefined(name.clone()));
                }
            },
            // Phase 1: Validate dependent types
            Type::BoundedInt { min, max } => {
                if min >= max {
                    self.errors.push(CheckError::InvalidBoundedIntRange {
                        min: *min,
                        max: *max,
                    });
                }
            },
            Type::NonEmpty(inner) => {
                self.check_type(inner);
            },
            Type::Positive(inner) => {
                self.check_type(inner);
                // Verify inner type is numeric
                match **inner {
                    Type::Int
                    | Type::Float
                    | Type::Money
                    | Type::MoneyWithCurrency(_)
                    | Type::Percent => {},
                    _ => {
                        self.errors.push(CheckError::InvalidConstraint(
                            "Positive<T> requires numeric type".to_string(),
                        ));
                    },
                }
            },
            Type::ValidDate { after, before } => {
                // Validate date format and ordering
                let after_date = if let Some(a) = after {
                    match Self::parse_date(a) {
                        Ok(date) => Some(date),
                        Err(e) => {
                            self.errors.push(CheckError::InvalidConstraint(format!(
                                "Invalid 'after' date '{}': {}",
                                a, e
                            )));
                            None
                        },
                    }
                } else {
                    None
                };

                let before_date = if let Some(b) = before {
                    match Self::parse_date(b) {
                        Ok(date) => Some(date),
                        Err(e) => {
                            self.errors.push(CheckError::InvalidConstraint(format!(
                                "Invalid 'before' date '{}': {}",
                                b, e
                            )));
                            None
                        },
                    }
                } else {
                    None
                };

                // Check ordering: after must be before before
                if let (Some(after), Some(before)) = (after_date, before_date) {
                    if after >= before {
                        self.errors.push(CheckError::InvalidConstraint(
                            format!("ValidDate constraint error: 'after' date ({}) must be before 'before' date ({})",
                                after.format("%d-%m-%Y"), before.format("%d-%m-%Y"))
                        ));
                    }
                }
            },
            Type::Citation {
                section,
                subsection,
                act,
            } => {
                // Validate citation format
                if section.is_empty() {
                    self.errors.push(CheckError::InvalidConstraint(
                        "Citation section cannot be empty".to_string(),
                    ));
                }
                if subsection.is_empty() {
                    self.errors.push(CheckError::InvalidConstraint(
                        "Citation subsection cannot be empty".to_string(),
                    ));
                }
                if act.is_empty() {
                    self.errors.push(CheckError::InvalidConstraint(
                        "Citation act cannot be empty".to_string(),
                    ));
                }
            },
            Type::TemporalValue {
                inner,
                valid_from,
                valid_until,
            } => {
                // Check inner type
                self.check_type(inner);

                // Validate temporal window
                let from_date = if let Some(from) = valid_from {
                    match Self::parse_date(from) {
                        Ok(date) => Some(date),
                        Err(e) => {
                            self.errors.push(CheckError::InvalidConstraint(format!(
                                "Invalid 'valid_from' date '{}': {}",
                                from, e
                            )));
                            None
                        },
                    }
                } else {
                    None
                };

                let until_date = if let Some(until) = valid_until {
                    match Self::parse_date(until) {
                        Ok(date) => Some(date),
                        Err(e) => {
                            self.errors.push(CheckError::InvalidConstraint(format!(
                                "Invalid 'valid_until' date '{}': {}",
                                until, e
                            )));
                            None
                        },
                    }
                } else {
                    None
                };

                // Check ordering: valid_from must be before valid_until
                if let (Some(from), Some(until)) = (from_date, until_date) {
                    if from >= until {
                        self.errors.push(CheckError::InvalidConstraint(
                            format!("TemporalValue error: 'valid_from' date ({}) must be before 'valid_until' date ({})",
                                from.format("%d-%m-%Y"), until.format("%d-%m-%Y"))
                        ));
                    }
                }
            },
            Type::Array(inner) => {
                self.check_type(inner);
            },
            Type::Union(left, right) => {
                self.check_type(left);
                self.check_type(right);
            },
            Type::MoneyWithCurrency(_currency) => {
                // Could validate currency code against ISO 4217
                // For now, accept any currency code
            },
            // Phase 2: Validate generic types
            Type::Generic { name, args } => {
                // Validate that the base type exists
                let type_exists = self.symbols.get_struct(name).is_some()
                    || self.symbols.get_enum(name).is_some();

                if !type_exists {
                    self.errors.push(CheckError::Undefined(name.clone()));
                    return;
                }

                // Validate parameter count matches definition (structs only support generics for now)
                if let Some(struct_def) = self.symbols.get_struct(name) {
                    let expected_params = struct_def.type_params.len();

                    if args.len() != expected_params {
                        self.errors.push(CheckError::GenericArityMismatch {
                            name: name.clone(),
                            expected: expected_params,
                            got: args.len(),
                        });
                    }
                } else {
                    // Enum used with generic syntax - not supported yet
                    self.errors.push(CheckError::InvalidConstraint(format!(
                        "Enum '{}' does not support generic type parameters",
                        name
                    )));
                }

                // Recursively check each type argument
                for arg in args {
                    self.check_type(arg);
                }
            },
            Type::TypeVariable(name) => {
                // Type variables must be in scope (declared in function/struct type parameters)
                if !self.symbols.is_type_param_in_scope(name) {
                    self.errors
                        .push(CheckError::UnboundTypeVariable(name.clone()));
                }

                // Basic validation: ensure it looks like a type variable (uppercase)
                if !name.chars().next().map_or(false, |c| c.is_uppercase()) {
                    self.errors.push(CheckError::InvalidConstraint(format!(
                        "Type variable '{}' should start with uppercase letter",
                        name
                    )));
                }
            },
            // Basic types don't need validation
            Type::Int
            | Type::Float
            | Type::Bool
            | Type::String
            | Type::Money
            | Type::Date
            | Type::Duration
            | Type::Percent
            | Type::Pass => {},
        }
    }

    /// Parse a date string in multiple formats (DD-MM-YYYY, YYYY-MM-DD, MM/DD/YYYY)
    fn parse_date(date_str: &str) -> Result<NaiveDate, String> {
        // Try DD-MM-YYYY format first (Yuho standard)
        if let Ok(date) = NaiveDate::parse_from_str(date_str, "%d-%m-%Y") {
            return Ok(date);
        }

        // Try YYYY-MM-DD format (ISO 8601)
        if let Ok(date) = NaiveDate::parse_from_str(date_str, "%Y-%m-%d") {
            return Ok(date);
        }

        // Try MM/DD/YYYY format (US)
        if let Ok(date) = NaiveDate::parse_from_str(date_str, "%m/%d/%Y") {
            return Ok(date);
        }

        Err(format!(
            "Invalid date format. Expected DD-MM-YYYY, YYYY-MM-DD, or MM/DD/YYYY"
        ))
    }

    /// Validate that a constraint is well-formed for the given type
    fn validate_constraint(&mut self, constraint: &Constraint, ty: &Type) {
        match constraint {
            Constraint::GreaterThan(expr)
            | Constraint::LessThan(expr)
            | Constraint::GreaterThanOrEqual(expr)
            | Constraint::LessThanOrEqual(expr)
            | Constraint::Equal(expr)
            | Constraint::NotEqual(expr) => {
                // Check that comparison makes sense for the type
                self.check_expr(expr);
                match ty {
                    Type::Int
                    | Type::Float
                    | Type::Money
                    | Type::Date
                    | Type::Duration
                    | Type::Percent
                    | Type::MoneyWithCurrency(_)
                    | Type::BoundedInt { .. }
                    | Type::Positive(_) => {
                        // Valid for numeric and comparable types
                    },
                    _ => {
                        self.errors.push(CheckError::InvalidConstraint(format!(
                            "Comparison constraint not supported for type {:?}",
                            ty
                        )));
                    },
                }
            },
            Constraint::InRange { min, max } => {
                self.check_expr(min);
                self.check_expr(max);
                match ty {
                    Type::Int
                    | Type::Float
                    | Type::Money
                    | Type::Percent
                    | Type::MoneyWithCurrency(_)
                    | Type::BoundedInt { .. } => {
                        // Valid for numeric types
                    },
                    _ => {
                        self.errors.push(CheckError::InvalidConstraint(format!(
                            "Range constraint not supported for type {:?}",
                            ty
                        )));
                    },
                }
            },
            Constraint::And(left, right) | Constraint::Or(left, right) => {
                self.validate_constraint(left, ty);
                self.validate_constraint(right, ty);
            },
            Constraint::Not(inner) => {
                self.validate_constraint(inner, ty);
            },
            Constraint::Before(expr) | Constraint::After(expr) => {
                self.check_expr(expr);
                match ty {
                    Type::Date | Type::ValidDate { .. } | Type::TemporalValue { .. } => {
                        // Valid for date types
                    },
                    _ => {
                        self.errors.push(CheckError::InvalidConstraint(format!(
                            "Temporal constraint (Before/After) requires date type, got {:?}",
                            ty
                        )));
                    },
                }
            },
            Constraint::Between { start, end } => {
                self.check_expr(start);
                self.check_expr(end);
                match ty {
                    Type::Date | Type::ValidDate { .. } | Type::TemporalValue { .. } => {
                        // Valid for date types
                    },
                    _ => {
                        self.errors.push(CheckError::InvalidConstraint(format!(
                            "Temporal constraint (Between) requires date type, got {:?}",
                            ty
                        )));
                    },
                }
            },
            Constraint::Custom(_) => {
                // Custom constraints are validated at runtime
            },
        }
    }

    /// Check that constraints are satisfied by a value
    fn check_constraints_satisfied(&mut self, constraints: &[Constraint], value: &Expr, ty: &Type) {
        // Try to evaluate the expression as a constant
        if let Some(const_val) = self.try_eval_const(value) {
            for constraint in constraints {
                if !self.eval_constraint(constraint, &const_val, ty) {
                    self.errors.push(CheckError::ConstraintViolation(format!(
                        "Value {:?} violates constraint {:?}",
                        const_val, constraint
                    )));
                }
            }
        }
        // For non-constant values, we can't check at compile time
        // Runtime checks would be needed
    }

    /// Try to evaluate an expression as a compile-time constant
    fn try_eval_const(&self, expr: &Expr) -> Option<Literal> {
        match expr {
            Expr::Literal(lit) => Some(lit.clone()),
            Expr::Unary(UnaryOp::Neg, inner) => {
                let val = self.try_eval_const(inner)?;
                match val {
                    Literal::Int(i) => Some(Literal::Int(-i)),
                    Literal::Float(f) => Some(Literal::Float(-f)),
                    Literal::Money(m) => Some(Literal::Money(-m)),
                    Literal::Percent(p) => Some(Literal::Percent(-p)),
                    _ => None,
                }
            },
            Expr::Binary(left, op, right) => {
                let left_val = self.try_eval_const(left)?;
                let right_val = self.try_eval_const(right)?;
                self.eval_binary_const(&left_val, op, &right_val)
            },
            _ => None, // Can't evaluate non-literals at compile time
        }
    }

    /// Evaluate a binary operation on constants
    fn eval_binary_const(&self, left: &Literal, op: &BinaryOp, right: &Literal) -> Option<Literal> {
        match (left, right) {
            (Literal::Int(l), Literal::Int(r)) => match op {
                BinaryOp::Add => Some(Literal::Int(l + r)),
                BinaryOp::Sub => Some(Literal::Int(l - r)),
                BinaryOp::Mul => Some(Literal::Int(l * r)),
                BinaryOp::Div if *r != 0 => Some(Literal::Int(l / r)),
                BinaryOp::Mod if *r != 0 => Some(Literal::Int(l % r)),
                _ => None,
            },
            (Literal::Float(l), Literal::Float(r)) => match op {
                BinaryOp::Add => Some(Literal::Float(l + r)),
                BinaryOp::Sub => Some(Literal::Float(l - r)),
                BinaryOp::Mul => Some(Literal::Float(l * r)),
                BinaryOp::Div if *r != 0.0 => Some(Literal::Float(l / r)),
                _ => None,
            },
            _ => None,
        }
    }

    /// Evaluate a constraint against a constant value
    fn eval_constraint(&self, constraint: &Constraint, value: &Literal, ty: &Type) -> bool {
        match constraint {
            Constraint::GreaterThan(expr) => {
                if let Some(bound) = self.try_eval_const(expr) {
                    self.compare_literals(value, &bound, ty) == Some(std::cmp::Ordering::Greater)
                } else {
                    true // Can't evaluate, assume satisfied
                }
            },
            Constraint::LessThan(expr) => {
                if let Some(bound) = self.try_eval_const(expr) {
                    self.compare_literals(value, &bound, ty) == Some(std::cmp::Ordering::Less)
                } else {
                    true
                }
            },
            Constraint::GreaterThanOrEqual(expr) => {
                if let Some(bound) = self.try_eval_const(expr) {
                    matches!(
                        self.compare_literals(value, &bound, ty),
                        Some(std::cmp::Ordering::Greater | std::cmp::Ordering::Equal)
                    )
                } else {
                    true
                }
            },
            Constraint::LessThanOrEqual(expr) => {
                if let Some(bound) = self.try_eval_const(expr) {
                    matches!(
                        self.compare_literals(value, &bound, ty),
                        Some(std::cmp::Ordering::Less | std::cmp::Ordering::Equal)
                    )
                } else {
                    true
                }
            },
            Constraint::Equal(expr) => {
                if let Some(bound) = self.try_eval_const(expr) {
                    self.compare_literals(value, &bound, ty) == Some(std::cmp::Ordering::Equal)
                } else {
                    true
                }
            },
            Constraint::NotEqual(expr) => {
                if let Some(bound) = self.try_eval_const(expr) {
                    self.compare_literals(value, &bound, ty) != Some(std::cmp::Ordering::Equal)
                } else {
                    true
                }
            },
            Constraint::InRange { min, max } => {
                let min_lit = self.try_eval_const(min);
                let max_lit = self.try_eval_const(max);
                if let (Some(min_val), Some(max_val)) = (min_lit, max_lit) {
                    matches!(
                        self.compare_literals(value, &min_val, ty),
                        Some(std::cmp::Ordering::Greater | std::cmp::Ordering::Equal)
                    ) && matches!(
                        self.compare_literals(value, &max_val, ty),
                        Some(std::cmp::Ordering::Less | std::cmp::Ordering::Equal)
                    )
                } else {
                    true
                }
            },
            Constraint::And(left, right) => {
                self.eval_constraint(left, value, ty) && self.eval_constraint(right, value, ty)
            },
            Constraint::Or(left, right) => {
                self.eval_constraint(left, value, ty) || self.eval_constraint(right, value, ty)
            },
            Constraint::Not(inner) => !self.eval_constraint(inner, value, ty),
            Constraint::Before(expr) => {
                if let Some(bound) = self.try_eval_const(expr) {
                    self.compare_literals(value, &bound, ty) == Some(std::cmp::Ordering::Less)
                } else {
                    true
                }
            },
            Constraint::After(expr) => {
                if let Some(bound) = self.try_eval_const(expr) {
                    self.compare_literals(value, &bound, ty) == Some(std::cmp::Ordering::Greater)
                } else {
                    true
                }
            },
            Constraint::Between { start, end } => {
                let start_lit = self.try_eval_const(start);
                let end_lit = self.try_eval_const(end);
                if let (Some(start_val), Some(end_val)) = (start_lit, end_lit) {
                    matches!(
                        self.compare_literals(value, &start_val, ty),
                        Some(std::cmp::Ordering::Greater | std::cmp::Ordering::Equal)
                    ) && matches!(
                        self.compare_literals(value, &end_val, ty),
                        Some(std::cmp::Ordering::Less | std::cmp::Ordering::Equal)
                    )
                } else {
                    true
                }
            },
            Constraint::Custom(_) => true, // Can't evaluate custom constraints at compile time
        }
    }

    /// Compare two literals, returning an ordering if they're comparable
    fn compare_literals(
        &self,
        left: &Literal,
        right: &Literal,
        _ty: &Type,
    ) -> Option<std::cmp::Ordering> {
        match (left, right) {
            (Literal::Int(l), Literal::Int(r)) => Some(l.cmp(r)),
            (Literal::Float(l), Literal::Float(r)) => l.partial_cmp(r),
            (Literal::Money(l), Literal::Money(r)) => l.partial_cmp(r),
            (Literal::Percent(l), Literal::Percent(r)) => l.partial_cmp(r),
            (Literal::Bool(l), Literal::Bool(r)) => Some(l.cmp(r)),
            (Literal::String(l), Literal::String(r)) => Some(l.cmp(r)),
            (Literal::Date(l), Literal::Date(r)) => {
                // Parse and compare dates
                if let (Ok(d1), Ok(d2)) = (Self::parse_date(l), Self::parse_date(r)) {
                    Some(d1.cmp(&d2))
                } else {
                    None
                }
            },
            _ => None, // Types don't match or aren't comparable
        }
    }

    /// Try to infer the type of an expression (basic implementation)
    fn infer_expr_type(&self, expr: &Expr) -> Option<Type> {
        match expr {
            Expr::Identifier(name) => self.symbols.lookup(name).cloned(),
            Expr::FieldAccess(obj, field) => {
                // Recursively infer object type and lookup field
                let obj_type = self.infer_expr_type(obj)?;
                let struct_name = self.get_struct_name(&obj_type)?;
                let struct_info = self.symbols.get_struct(&struct_name)?;
                struct_info
                    .fields
                    .iter()
                    .find(|(name, _, _)| name == field)
                    .map(|(_, ty, _)| ty.clone())
            },
            Expr::StructInit(init) if !init.name.is_empty() => {
                Some(Type::Named(init.name.clone()))
            },
            _ => None, // For other expressions, we'd need full type inference
        }
    }

    /// Extract struct name from a type (handles Named and Generic types)
    fn get_struct_name(&self, ty: &Type) -> Option<String> {
        match ty {
            Type::Named(name) => Some(name.clone()),
            Type::Generic { name, .. } => Some(name.clone()),
            _ => None,
        }
    }
}

impl Default for Checker {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use yuho_core::parse;

    #[test]
    fn test_undefined_variable() {
        let source = "int x := y";
        let program = parse(source).unwrap();
        let mut checker = Checker::new();
        let errors = checker.check_program(&program);
        assert!(errors.iter().any(|e| matches!(e, CheckError::Undefined(_))));
    }

    #[test]
    fn test_duplicate_definition() {
        let source = "int x := 1 int x := 2";
        let program = parse(source).unwrap();
        let mut checker = Checker::new();
        let errors = checker.check_program(&program);
        assert!(errors.iter().any(|e| matches!(e, CheckError::Duplicate(_))));
    }

    #[test]
    fn test_valid_program() {
        let source = r#"
            struct Person { string name, int age, }
            Person p := { name := "John", age := 30, }
        "#;
        let program = parse(source).unwrap();
        let mut checker = Checker::new();
        let errors = checker.check_program(&program);
        // Should only have non-exhaustive match warning if any match exists
        assert!(
            errors.is_empty()
                || errors
                    .iter()
                    .all(|e| !matches!(e, CheckError::Undefined(_)))
        );
    }

    #[test]
    fn test_invalid_field() {
        let source = r#"
            struct Person { string name, }
            Person p := Person { invalid := "test", }
        "#;
        let program = parse(source).unwrap();
        let mut checker = Checker::new();
        let errors = checker.check_program(&program);
        assert!(errors
            .iter()
            .any(|e| matches!(e, CheckError::InvalidField { .. })));
    }

    #[test]
    fn test_non_exhaustive_match() {
        let source = r#"
            match x { case 1 := "one" }
        "#;
        let program = parse(source).unwrap();
        let mut checker = Checker::new();
        let errors = checker.check_program(&program);
        assert!(errors
            .iter()
            .any(|e| matches!(e, CheckError::NonExhaustiveMatch)));
    }

    // Phase 1 tests for dependent type validation
    #[test]
    fn test_valid_bounded_int() {
        let source = "BoundedInt<0, 100> age := 25";
        let program = parse(source).unwrap();
        let mut checker = Checker::new();
        let errors = checker.check_program(&program);
        // Should not have any BoundedInt range errors
        assert!(!errors
            .iter()
            .any(|e| matches!(e, CheckError::InvalidBoundedIntRange { .. })));
    }

    #[test]
    fn test_invalid_bounded_int_range() {
        let source = "struct Test { BoundedInt<100, 0> invalid, }";
        let program = parse(source).unwrap();
        let mut checker = Checker::new();
        let errors = checker.check_program(&program);
        assert!(errors
            .iter()
            .any(|e| matches!(e, CheckError::InvalidBoundedIntRange { .. })));
    }

    #[test]
    fn test_positive_numeric_type() {
        let source = "Positive<int> count := 5";
        let program = parse(source).unwrap();
        let mut checker = Checker::new();
        let errors = checker.check_program(&program);
        // Should not have constraint errors for numeric types
        assert!(!errors
            .iter()
            .any(|e| matches!(e, CheckError::InvalidConstraint(_))));
    }

    #[test]
    fn test_positive_invalid_type() {
        let source = "struct Test { Positive<string> invalid, }";
        let program = parse(source).unwrap();
        let mut checker = Checker::new();
        let errors = checker.check_program(&program);
        assert!(errors
            .iter()
            .any(|e| matches!(e, CheckError::InvalidConstraint(_))));
    }

    #[test]
    fn test_nested_dependent_types() {
        let source = "NonEmpty<Array<Positive<int>>> matrix := 1";
        let program = parse(source).unwrap();
        let mut checker = Checker::new();
        let errors = checker.check_program(&program);
        // Nested types should be validated recursively
        assert!(!errors
            .iter()
            .any(|e| matches!(e, CheckError::InvalidConstraint(_))));
    }

    // Date validation tests
    #[test]
    fn test_valid_date_no_constraints() {
        let source = "ValidDate event := 15-06-2024";
        let program = parse(source).unwrap();
        let mut checker = Checker::new();
        let errors = checker.check_program(&program);
        assert!(errors.is_empty());
    }

    // Note: ValidDate with after/before parameters tested in integration tests
    // Parser currently requires specific syntax for date parameters

    // Struct field validation tests
    #[test]
    fn test_struct_all_fields_provided() {
        let source = r#"
            struct Person {
                string name,
                int age,
            }
            scope test {
                Person p := Person {
                    name := "Alice",
                    age := 30,
                }
            }
        "#;
        let program = parse(source).unwrap();
        let mut checker = Checker::new();
        let errors = checker.check_program(&program);
        // No missing field errors
        assert!(!errors
            .iter()
            .any(|e| matches!(e, CheckError::MissingField { .. })));
    }

    #[test]
    fn test_struct_missing_field() {
        let source = r#"
            struct Person {
                string name,
                int age,
                string email,
            }
            scope test {
                Person p := Person {
                    name := "Bob",
                }
            }
        "#;
        let program = parse(source).unwrap();
        let mut checker = Checker::new();
        let errors = checker.check_program(&program);
        // Should have 2 missing field errors (age, email)
        let missing_errors: Vec<_> = errors
            .iter()
            .filter(|e| matches!(e, CheckError::MissingField { .. }))
            .collect();
        assert_eq!(missing_errors.len(), 2);
    }

    #[test]
    fn test_struct_invalid_field() {
        let source = r#"
            struct Person {
                string name,
                int age,
            }
            scope test {
                Person p := Person {
                    name := "Charlie",
                    age := 25,
                    invalid_field := "test",
                }
            }
        "#;
        let program = parse(source).unwrap();
        let mut checker = Checker::new();
        let errors = checker.check_program(&program);
        // Should have invalid field error
        assert!(errors
            .iter()
            .any(|e| matches!(e, CheckError::InvalidField { .. })));
    }

    #[test]
    fn test_struct_multiple_missing_fields_reported() {
        let source = r#"
            struct Contract {
                string title,
                string party_a,
                string party_b,
                money<SGD> value,
                date signed_date,
            }
            scope test {
                Contract c := Contract {
                    title := "Test",
                }
            }
        "#;
        let program = parse(source).unwrap();
        let mut checker = Checker::new();
        let errors = checker.check_program(&program);
        // Should report ALL missing fields (4 in total)
        let missing_errors: Vec<_> = errors
            .iter()
            .filter(|e| matches!(e, CheckError::MissingField { .. }))
            .collect();
        assert_eq!(missing_errors.len(), 4);
    }

    #[test]
    fn test_check_with_imports() {
        use std::fs;
        use tempfile::TempDir;
        use yuho_core::resolver::ModuleResolver;

        let temp_dir = TempDir::new().unwrap();
        let temp_path = temp_dir.path();

        // Create a module with Person struct
        let person_file = temp_path.join("person.yh");
        fs::write(
            &person_file,
            r#"
struct Person {
    string name,
    int age,
}
"#,
        )
        .unwrap();

        // Create main file that imports and uses Person
        let main_file = temp_path.join("main.yh");
        fs::write(
            &main_file,
            r#"
referencing Person from person

struct Employee {
    Person person,
    string job_title,
}

scope test {
    Employee e := Employee {
        person := Person {
            name := "Alice",
            age := 30,
        },
        job_title := "Engineer",
    }
}
"#,
        )
        .unwrap();

        // Resolve imports
        let mut resolver = ModuleResolver::new(temp_path);
        let resolved = resolver.resolve(&main_file).unwrap();

        // Check with imports
        let mut checker = Checker::new();
        let errors = checker.check_with_imports(&resolved);

        // Should have no errors
        assert_eq!(errors.len(), 0, "Expected no errors, got: {:?}", errors);
    }

    #[test]
    fn test_check_with_imports_missing_field() {
        use std::fs;
        use tempfile::TempDir;
        use yuho_core::resolver::ModuleResolver;

        let temp_dir = TempDir::new().unwrap();
        let temp_path = temp_dir.path();

        // Create a module with Person struct
        let person_file = temp_path.join("person.yh");
        fs::write(
            &person_file,
            r#"
struct Person {
    string name,
    int age,
}
"#,
        )
        .unwrap();

        // Create main file that imports Person but doesn't provide all fields
        let main_file = temp_path.join("main.yh");
        fs::write(
            &main_file,
            r#"
referencing Person from person

scope test {
    Person p := Person {
        name := "Bob",
    }
}
"#,
        )
        .unwrap();

        // Resolve imports
        let mut resolver = ModuleResolver::new(temp_path);
        let resolved = resolver.resolve(&main_file).unwrap();

        // Check with imports
        let mut checker = Checker::new();
        let errors = checker.check_with_imports(&resolved);

        // Should have missing field error for 'age'
        assert!(errors
            .iter()
            .any(|e| matches!(e, CheckError::MissingField { field, .. } if field == "age")));
    }
}
