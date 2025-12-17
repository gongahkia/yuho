# yuho-core

Core compiler components for the Yuho legal DSL.

## Components

### Lexer (`lexer.rs`)
Tokenizes Yuho source code into a stream of tokens.

```rust
use yuho_core::lex;

let tokens = lex("string name := \"Alice\"");
```

### Parser (`parser.rs`)
Parses token streams into an Abstract Syntax Tree (AST).

```rust
use yuho_core::parse;

let program = parse(source)?;
```

### AST (`ast.rs`)
Defines the Abstract Syntax Tree structure for Yuho programs.

Key types:
- `Program` - Complete Yuho program with imports and items
- `Item` - Top-level declarations (Struct, Enum, Scope, Function)
- `Type` - Type system (primitives, custom types, dependent types)
- `Expression` - Runtime values and operations

### Module Resolver (`resolver.rs`)
Resolves import statements across multiple Yuho files.

```rust
use yuho_core::resolver::ModuleResolver;

let mut resolver = ModuleResolver::new("./src");
let resolved = resolver.resolve("main.yh")?;
```

Features:
- **File Resolution** - Searches for imported modules in current directory
- **Circular Import Detection** - Prevents infinite import cycles
- **Symbol Verification** - Validates imported symbols exist
- **Symbol Table Merging** - Combines types from all imported modules

## Import Syntax

```yuho
referencing Person, Address from person

struct Employee {
    Person person,
    string job_title,
}
```

The resolver:
1. Finds `person.yh` in the same directory
2. Verifies `Person` and `Address` exist in that module
3. Makes those types available in the current file
4. Checks for circular dependencies (e.g., person → employee → person)

## Error Handling

All parser and resolver errors use `ParseError` and `ResolveError` with detailed messages:

```rust
pub enum ResolveError {
    ModuleNotFound { module: String, searched_paths: Vec<PathBuf> },
    CircularImport { cycle: Vec<PathBuf> },
    MissingSymbol { symbol: String, module: String, available: Vec<String> },
    // ...
}
```
