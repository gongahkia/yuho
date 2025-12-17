use crate::ast::{ImportStatement, Program};
use crate::parser::parse;
use std::collections::{HashMap, HashSet};
use std::fs;
use std::path::{Path, PathBuf};
use thiserror::Error;

#[derive(Error, Debug, Clone)]
pub enum ResolveError {
    #[error("Failed to read file '{path}': {reason}")]
    FileReadError { path: String, reason: String },

    #[error("Failed to parse file '{path}': {reason}")]
    ParseError { path: String, reason: String },

    #[error("Circular import detected: {cycle}")]
    CircularImport { cycle: String },

    #[error("Module '{module}' not found (searched: {searched_paths})")]
    ModuleNotFound {
        module: String,
        searched_paths: String,
    },

    #[error("Symbol '{symbol}' not found in module '{module}'")]
    SymbolNotFound { symbol: String, module: String },
}

pub type ResolveResult<T> = Result<T, ResolveError>;

/// Resolves imports and merges symbol tables across multiple files
#[derive(Debug)]
pub struct ModuleResolver {
    /// Root directory for module resolution
    root_dir: PathBuf,
    /// Cache of parsed modules: path -> Program
    module_cache: HashMap<PathBuf, Program>,
    /// Tracks which modules are currently being resolved (for cycle detection)
    resolution_stack: Vec<PathBuf>,
    /// Search paths for modules (relative to root)
    search_paths: Vec<PathBuf>,
}

impl ModuleResolver {
    /// Creates a new resolver with the given root directory
    pub fn new<P: AsRef<Path>>(root_dir: P) -> Self {
        let root = root_dir.as_ref().to_path_buf();
        Self {
            search_paths: vec![root.clone(), root.join("lib"), root.join("stdlib")],
            root_dir: root,
            module_cache: HashMap::new(),
            resolution_stack: Vec::new(),
        }
    }

    /// Adds a search path for module resolution
    pub fn add_search_path<P: AsRef<Path>>(&mut self, path: P) {
        self.search_paths.push(self.root_dir.join(path));
    }

    /// Resolves all imports in a program and returns the merged program
    pub fn resolve(&mut self, main_file: &Path) -> ResolveResult<ResolvedProgram> {
        let main_path = self.root_dir.join(main_file);

        // Add main file to resolution stack
        self.resolution_stack.push(main_path.clone());
        let program = self.resolve_file(&main_path)?;

        // Extract all imported symbols
        let mut resolved = ResolvedProgram {
            main_program: program.clone(),
            imported_programs: HashMap::new(),
            symbol_map: HashMap::new(),
        };

        self.resolve_imports_recursive(&program, &mut resolved)?;

        // Clear resolution stack when done
        self.resolution_stack.clear();

        Ok(resolved)
    }

    /// Recursively resolves imports
    fn resolve_imports_recursive(
        &mut self,
        program: &Program,
        resolved: &mut ResolvedProgram,
    ) -> ResolveResult<()> {
        for import in &program.imports {
            let module_path = self.find_module(&import.from)?;

            // Check for circular imports
            if self.resolution_stack.contains(&module_path) {
                return Err(ResolveError::CircularImport {
                    cycle: self.format_cycle(&module_path),
                });
            }

            // Load and cache module if not already loaded
            if !self.module_cache.contains_key(&module_path) {
                self.resolution_stack.push(module_path.clone());
                let imported_program = self.resolve_file(&module_path)?;
                self.module_cache
                    .insert(module_path.clone(), imported_program.clone());
                self.resolution_stack.pop();

                // Recursively resolve imports in the imported module
                self.resolve_imports_recursive(&imported_program, resolved)?;
            }

            let imported_program = self.module_cache.get(&module_path).unwrap();

            // Verify imported symbols exist
            self.verify_symbols(import, imported_program)?;

            // Map imported symbols
            for symbol_name in &import.names {
                resolved
                    .symbol_map
                    .insert(symbol_name.clone(), module_path.clone());
            }

            resolved
                .imported_programs
                .insert(module_path.clone(), imported_program.clone());
        }

        Ok(())
    }

    /// Finds a module file by name
    fn find_module(&self, module_name: &str) -> ResolveResult<PathBuf> {
        let module_file = format!("{}.yh", module_name);
        let mut searched = Vec::new();

        for search_path in &self.search_paths {
            let candidate = search_path.join(&module_file);
            searched.push(candidate.display().to_string());

            if candidate.exists() {
                return Ok(candidate);
            }

            // Also try with subdirectories (e.g., "common/person" -> "common/person.yh")
            let subdir_candidate = self.root_dir.join(module_name).with_extension("yh");
            if subdir_candidate.exists() {
                return Ok(subdir_candidate);
            }
        }

        Err(ResolveError::ModuleNotFound {
            module: module_name.to_string(),
            searched_paths: searched.join(", "),
        })
    }

    /// Resolves a single file
    fn resolve_file(&self, path: &Path) -> ResolveResult<Program> {
        let source = fs::read_to_string(path).map_err(|e| ResolveError::FileReadError {
            path: path.display().to_string(),
            reason: e.to_string(),
        })?;

        parse(&source).map_err(|e| ResolveError::ParseError {
            path: path.display().to_string(),
            reason: e.to_string(),
        })
    }

    /// Verifies that all imported symbols exist in the module
    fn verify_symbols(&self, import: &ImportStatement, program: &Program) -> ResolveResult<()> {
        let available_symbols: HashSet<String> = program
            .items
            .iter()
            .filter_map(|item| match item {
                crate::ast::Item::Struct(s) => Some(s.name.clone()),
                crate::ast::Item::Enum(e) => Some(e.name.clone()),
                crate::ast::Item::Function(f) => Some(f.name.clone()),
                crate::ast::Item::Scope(s) => Some(s.name.clone()),
                _ => None,
            })
            .collect();

        for symbol in &import.names {
            if !available_symbols.contains(symbol) {
                return Err(ResolveError::SymbolNotFound {
                    symbol: symbol.clone(),
                    module: import.from.clone(),
                });
            }
        }

        Ok(())
    }

    /// Formats the circular import cycle for error message
    fn format_cycle(&self, new_path: &Path) -> String {
        let mut cycle = self
            .resolution_stack
            .iter()
            .map(|p| p.display().to_string())
            .collect::<Vec<_>>();
        cycle.push(new_path.display().to_string());
        cycle.join(" -> ")
    }
}

/// A program with all imports resolved
#[derive(Debug, Clone)]
pub struct ResolvedProgram {
    /// The main program being compiled
    pub main_program: Program,
    /// All imported programs: path -> Program
    pub imported_programs: HashMap<PathBuf, Program>,
    /// Symbol to module mapping: symbol_name -> module_path
    pub symbol_map: HashMap<String, PathBuf>,
}

impl ResolvedProgram {
    /// Gets a symbol's definition from the appropriate module
    pub fn get_symbol_program(&self, symbol: &str) -> Option<&Program> {
        self.symbol_map
            .get(symbol)
            .and_then(|path| self.imported_programs.get(path))
    }

    /// Returns all programs (main + imported) in dependency order
    pub fn all_programs(&self) -> Vec<&Program> {
        let mut programs = vec![&self.main_program];
        programs.extend(self.imported_programs.values());
        programs
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;
    use tempfile::TempDir;

    fn create_test_file(dir: &Path, name: &str, content: &str) -> PathBuf {
        let path = dir.join(format!("{}.yh", name));
        fs::write(&path, content).unwrap();
        path
    }

    #[test]
    fn test_basic_module_resolution() {
        let temp_dir = TempDir::new().unwrap();
        let temp_path = temp_dir.path();

        // Create a simple module
        create_test_file(
            temp_path,
            "person",
            r#"
struct Person {
    string name,
    int age,
}
"#,
        );

        // Create main file that imports it
        create_test_file(
            temp_path,
            "main",
            r#"
referencing Person from person

struct Employee {
    Person person,
    string job_title,
}
"#,
        );

        let mut resolver = ModuleResolver::new(temp_path);
        let result = resolver.resolve(&temp_path.join("main.yh"));

        assert!(result.is_ok());
        let resolved = result.unwrap();
        assert_eq!(resolved.imported_programs.len(), 1);
        assert!(resolved.symbol_map.contains_key("Person"));
    }

    #[test]
    fn test_circular_import_detection() {
        let temp_dir = TempDir::new().unwrap();
        let temp_path = temp_dir.path();

        create_test_file(
            temp_path,
            "a",
            r#"
referencing B from b

struct A {
    string name,
}
"#,
        );

        create_test_file(
            temp_path,
            "b",
            r#"
referencing A from a

struct B {
    string name,
}
"#,
        );

        let mut resolver = ModuleResolver::new(temp_path);
        let result = resolver.resolve(&temp_path.join("a.yh"));

        assert!(result.is_err());
        match result.unwrap_err() {
            ResolveError::CircularImport { .. } => {},
            e => panic!("Expected CircularImport error, got: {:?}", e),
        }
    }

    #[test]
    fn test_missing_symbol_error() {
        let temp_dir = TempDir::new().unwrap();
        let temp_path = temp_dir.path();

        create_test_file(
            temp_path,
            "person",
            r#"
struct Person {
    string name,
}
"#,
        );

        create_test_file(
            temp_path,
            "main",
            r#"
referencing Person, Company from person

struct Employee {
    Person person,
}
"#,
        );

        let mut resolver = ModuleResolver::new(temp_path);
        let result = resolver.resolve(&temp_path.join("main.yh"));

        assert!(result.is_err());
        match result.unwrap_err() {
            ResolveError::SymbolNotFound { symbol, .. } => {
                assert_eq!(symbol, "Company");
            },
            e => panic!("Expected SymbolNotFound error, got: {:?}", e),
        }
    }

    #[test]
    fn test_module_not_found() {
        let temp_dir = TempDir::new().unwrap();
        let temp_path = temp_dir.path();

        create_test_file(
            temp_path,
            "main",
            r#"
referencing Person from nonexistent

struct Employee {
    string name,
}
"#,
        );

        let mut resolver = ModuleResolver::new(temp_path);
        let result = resolver.resolve(&temp_path.join("main.yh"));

        assert!(result.is_err());
        match result.unwrap_err() {
            ResolveError::ModuleNotFound { module, .. } => {
                assert_eq!(module, "nonexistent");
            },
            e => panic!("Expected ModuleNotFound error, got: {:?}", e),
        }
    }
}
