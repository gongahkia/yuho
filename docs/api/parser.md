# Parser API Reference

API documentation for Yuho's parser module.

## Overview

The parser module (`yuho_v3/parser.py`) converts Lark parse trees into Yuho's Abstract Syntax Tree (AST). It consists of two main components:

1. **YuhoTransformer**: Transforms Lark parse trees to AST nodes
2. **YuhoParser**: Main parser interface for user code

## Module: `yuho_v3.parser`

```python
from yuho_v3.parser import YuhoParser, YuhoTransformer
```

---

## Class: `YuhoParser`

Main parser class for Yuho language.

### Constructor

```python
YuhoParser()
```

Creates a new parser instance.

**Example**:
```python
parser = YuhoParser()
```

### Methods

#### `parse(text: str) -> Program`

Parse Yuho source code into an AST.

**Parameters**:
- `text` (str): Yuho source code string

**Returns**:
- `Program`: Root AST node representing the complete program

**Raises**:
- `SyntaxError`: If parsing fails due to syntax errors

**Example**:
```python
parser = YuhoParser()
ast = parser.parse('int x := 42;')
print(f"Parsed {len(ast.statements)} statement(s)")
```

**Usage**:
```python
code = """
struct Person {
    string name,
    int age
}
"""
try:
    ast = parser.parse(code)
    print("Parsing successful!")
except SyntaxError as e:
    print(f"Syntax error: {e}")
```

---

#### `parse_file(filepath: str) -> Program`

Parse a Yuho source file.

**Parameters**:
- `filepath` (str): Path to `.yh` file

**Returns**:
- `Program`: Root AST node

**Raises**:
- `SyntaxError`: If parsing fails
- `FileNotFoundError`: If file doesn't exist
- `IOError`: If file can't be read

**Example**:
```python
parser = YuhoParser()
ast = parser.parse_file('example.yh')
print(f"File contains {len(ast.statements)} statements")
```

**Usage**:
```python
try:
    ast = parser.parse_file('/path/to/statute.yh')
    for stmt in ast.statements:
        print(f"Statement type: {type(stmt).__name__}")
except FileNotFoundError:
    print("File not found")
except SyntaxError as e:
    print(f"Parse error: {e}")
```

---

## Class: `YuhoTransformer`

Lark transformer that converts parse trees to Yuho AST nodes.

This is an internal class used by `YuhoParser`. Most users don't need to interact with it directly.

### Transformation Methods

The transformer handles all Yuho language constructs:

#### Statement Transformations

- `program(children)` - Transform program node
- `import_statement(children)` - Transform import statements
- `declaration(children)` - Transform variable declarations
- `assignment(children)` - Transform assignments
- `struct_definition(children)` - Transform struct definitions
- `function_definition(children)` - Transform function definitions
- `match_case(children)` - Transform match-case statements

#### Expression Transformations

- `expression(children)` - Transform expressions
- `logical_expression(children)` - Transform logical operations (&&, ||)
- `relational_expression(children)` - Transform comparisons (>, <, ==)
- `additive_expression(children)` - Transform addition/subtraction
- `multiplicative_expression(children)` - Transform multiplication/division
- `primary_expression(children)` - Transform primary expressions
- `literal(children)` - Transform literal values

---

## Usage Examples

### Basic Parsing

```python
from yuho_v3.parser import YuhoParser

# Create parser
parser = YuhoParser()

# Parse simple code
code = "int x := 42;"
ast = parser.parse(code)

# Access AST
assert len(ast.statements) == 1
decl = ast.statements[0]
assert decl.name == "x"
assert decl.value.value == 42
```

### Parsing Complex Code

```python
from yuho_v3.parser import YuhoParser

code = """
// Define a legal concept
struct Cheating {
    string accused,
    string victim,
    bool deception,
    bool harm
}

// Define logic
match {
    case deception && harm := consequence "guilty";
    case _ := consequence "not guilty";
}
"""

parser = YuhoParser()
ast = parser.parse(code)

# Examine AST structure
for stmt in ast.statements:
    if isinstance(stmt, StructDefinition):
        print(f"Struct: {stmt.name}")
        print(f"  Members: {len(stmt.members)}")
    elif isinstance(stmt, MatchCase):
        print(f"Match-case with {len(stmt.cases)} cases")
```

### Error Handling

```python
from yuho_v3.parser import YuhoParser

parser = YuhoParser()

# Handle syntax errors gracefully
invalid_code = "int x = 42;"  # Wrong: should use :=

try:
    ast = parser.parse(invalid_code)
except SyntaxError as e:
    print(f"Syntax error: {e}")
    # Provide helpful feedback to user
```

### File Parsing with Error Recovery

```python
from yuho_v3.parser import YuhoParser
from pathlib import Path

def parse_yuho_files(directory):
    """Parse all .yh files in a directory"""
    parser = YuhoParser()
    results = {}
    
    for file_path in Path(directory).glob('*.yh'):
        try:
            ast = parser.parse_file(str(file_path))
            results[file_path.name] = {
                'success': True,
                'ast': ast,
                'statements': len(ast.statements)
            }
        except SyntaxError as e:
            results[file_path.name] = {
                'success': False,
                'error': str(e)
            }
    
    return results

# Usage
results = parse_yuho_files('example/cheating/')
for filename, result in results.items():
    if result['success']:
        print(f"✓ {filename}: {result['statements']} statements")
    else:
        print(f"✗ {filename}: {result['error']}")
```

---

## AST Nodes

The parser produces instances of AST node classes defined in `yuho_v3/ast_nodes.py`.

### Common AST Nodes

```python
from yuho_v3.ast_nodes import (
    Program,           # Root node
    Declaration,       # Variable declaration
    StructDefinition,  # Struct definition
    MatchCase,         # Match-case statement
    Literal,          # Literal value
    Identifier,       # Variable reference
    BinaryOperation,  # Binary operation (&&, +, etc.)
)
```

### Inspecting AST

```python
from yuho_v3.parser import YuhoParser
from yuho_v3.ast_nodes import Declaration, Literal

parser = YuhoParser()
ast = parser.parse('int x := 42;')

# Type checking
stmt = ast.statements[0]
assert isinstance(stmt, Declaration)

# Access properties
assert stmt.name == "x"
assert isinstance(stmt.value, Literal)
assert stmt.value.value == 42
assert stmt.value.literal_type == YuhoType.INT
```

---

## Integration with Other Components

### With Semantic Analyzer

```python
from yuho_v3.parser import YuhoParser
from yuho_v3.semantic_analyzer import SemanticAnalyzer

# Parse code
parser = YuhoParser()
ast = parser.parse(code)

# Analyze semantics
analyzer = SemanticAnalyzer()
errors = analyzer.analyze(ast)

if errors:
    print("Semantic errors:")
    for error in errors:
        print(f"  - {error}")
else:
    print("Code is semantically correct!")
```

### With Transpilers

```python
from yuho_v3.parser import YuhoParser
from yuho_v3.transpilers.mermaid_transpiler import MermaidTranspiler

# Parse code
parser = YuhoParser()
ast = parser.parse_file('statute.yh')

# Generate Mermaid diagram
transpiler = MermaidTranspiler()
diagram = transpiler.transpile_to_flowchart(ast)

# Save to file
with open('diagram.mmd', 'w') as f:
    f.write(diagram)
```

---

## Performance Considerations

### Parser Performance

- **Time Complexity**: O(n) where n = source code length
- **Memory**: O(m) where m = AST node count
- **Typical Speed**: ~1000 lines/second on modern hardware

### Optimization Tips

```python
# 1. Reuse parser instance
parser = YuhoParser()  # Create once
for file in files:
    ast = parser.parse_file(file)  # Reuse

# 2. Parse large files in chunks (if streaming supported in future)
# Currently, parse entire file at once

# 3. Cache parsed results
from functools import lru_cache

@lru_cache(maxsize=100)
def parse_cached(filepath):
    parser = YuhoParser()
    return parser.parse_file(filepath)
```

---

## Error Messages

The parser provides detailed error messages:

### Syntax Error Example

```python
parser = YuhoParser()
try:
    parser.parse("int x = 42;")  # Wrong operator
except SyntaxError as e:
    # Error message will indicate:
    # - What was expected
    # - What was found
    # - Line and column number
    print(e)
```

---

## Advanced Usage

### Custom Error Handling

```python
from yuho_v3.parser import YuhoParser
from yuho_v3.exceptions import YuhoSyntaxError, SourceLocation

def parse_with_custom_errors(code, filename=None):
    """Parse with custom error handling"""
    parser = YuhoParser()
    
    try:
        return parser.parse(code)
    except SyntaxError as e:
        # Convert to custom error type
        error = YuhoSyntaxError(
            message=str(e),
            location=SourceLocation(line=1, column=1, filename=filename),
            suggestion="Check your syntax - did you use := for assignment?"
        )
        raise error
```

### Batch Processing

```python
from yuho_v3.parser import YuhoParser
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

def parse_file_safe(filepath):
    """Parse file and return result tuple"""
    parser = YuhoParser()
    try:
        ast = parser.parse_file(filepath)
        return (filepath, ast, None)
    except Exception as e:
        return (filepath, None, e)

def parse_directory_parallel(directory, max_workers=4):
    """Parse all files in directory in parallel"""
    files = list(Path(directory).glob('*.yh'))
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(parse_file_safe, files))
    
    return results
```

---

## See Also

- [AST Nodes Reference](ast.md)
- [Lexer Reference](lexer.md)
- [Semantic Analyzer Reference](semantic.md)
- [Architecture Overview](../development/architecture.md)

---

## Source Code

**Location**: `yuho_v3/parser.py`

**View on GitHub**: [parser.py](https://github.com/gongahkia/yuho/blob/main/yuho_v3/parser.py)

