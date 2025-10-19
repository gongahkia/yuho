# Semantic Analyzer API

The Yuho semantic analyzer validates the meaning and correctness of parsed code.

## Overview

The semantic analyzer provides:

- **Type Checking** - Validate type consistency
- **Variable Analysis** - Check variable declarations and usage
- **Semantic Validation** - Ensure logical correctness
- **Error Reporting** - Provide detailed error messages

## Basic Usage

```python
from yuho_v3.semantic_analyzer import SemanticAnalyzer
from yuho_v3.parser import YuhoParser

# Parse source code
parser = YuhoParser()
ast = parser.parse("""
struct Person {
    string name,
    int age
}

Person person := {
    name := "Alice",
    age := 25
}
""")

# Perform semantic analysis
analyzer = SemanticAnalyzer()
errors = analyzer.analyze(ast)

if errors:
    for error in errors:
        print(f"Error: {error}")
else:
    print("Semantic analysis passed")
```

## Analysis Types

### Type Checking

```python
class TypeChecker:
    """Type checking functionality"""
    
    def __init__(self):
        self.symbol_table = {}
        self.errors = []
    
    def check_types(self, ast: Program) -> List[str]:
        """Check types in AST"""
        self.errors = []
        self.symbol_table = {}
        
        for stmt in ast.statements:
            self._check_statement(stmt)
        
        return self.errors
    
    def _check_statement(self, stmt: Statement):
        """Check individual statement"""
        if isinstance(stmt, Declaration):
            self._check_declaration(stmt)
        elif isinstance(stmt, StructDefinition):
            self._check_struct_definition(stmt)
        elif isinstance(stmt, MatchCase):
            self._check_match_case(stmt)
```

### Variable Analysis

```python
class VariableAnalyzer:
    """Variable analysis functionality"""
    
    def __init__(self):
        self.symbol_table = {}
        self.errors = []
    
    def analyze_variables(self, ast: Program) -> List[str]:
        """Analyze variable usage"""
        self.errors = []
        self.symbol_table = {}
        
        # First pass: collect declarations
        for stmt in ast.statements:
            if isinstance(stmt, Declaration):
                self._add_declaration(stmt)
        
        # Second pass: check usage
        for stmt in ast.statements:
            self._check_statement(stmt)
        
        return self.errors
    
    def _add_declaration(self, decl: Declaration):
        """Add variable declaration to symbol table"""
        self.symbol_table[decl.name] = decl.type_node.type_name
    
    def _check_identifier(self, ident: Identifier):
        """Check identifier usage"""
        if ident.name not in self.symbol_table:
            self.errors.append(f"Undefined variable: {ident.name}")
```

### Semantic Validation

```python
class SemanticValidator:
    """Semantic validation functionality"""
    
    def __init__(self):
        self.errors = []
    
    def validate(self, ast: Program) -> List[str]:
        """Validate semantic correctness"""
        self.errors = []
        
        for stmt in ast.statements:
            if isinstance(stmt, MatchCase):
                self._validate_match_case(stmt)
            elif isinstance(stmt, StructDefinition):
                self._validate_struct_definition(stmt)
        
        return self.errors
    
    def _validate_match_case(self, match: MatchCase):
        """Validate match-case statement"""
        if not match.cases:
            self.errors.append("Match-case must have at least one case")
            return
        
        # Check for default case
        has_default = any(case.condition is None for case in match.cases)
        if not has_default:
            self.errors.append("Match-case must have default case")
        
        # Check case completeness
        self._check_case_completeness(match)
    
    def _check_case_completeness(self, match: MatchCase):
        """Check if all cases are covered"""
        # Implementation for checking completeness
        pass
```

## Error Types

### Type Errors

```python
class TypeError:
    """Type-related error"""
    
    def __init__(self, message: str, line: int = 0, column: int = 0):
        self.message = message
        self.line = line
        self.column = column
    
    def __str__(self):
        return f"Type error: {self.message} at line {self.line}, column {self.column}"

# Common type errors
def check_type_mismatch(left_type: str, right_type: str, line: int, column: int):
    """Check for type mismatch"""
    if left_type != right_type:
        return TypeError(f"Type mismatch: expected {left_type}, got {right_type}", line, column)
    return None
```

### Variable Errors

```python
class VariableError:
    """Variable-related error"""
    
    def __init__(self, message: str, variable: str, line: int = 0, column: int = 0):
        self.message = message
        self.variable = variable
        self.line = line
        self.column = column
    
    def __str__(self):
        return f"Variable error: {self.message} for '{self.variable}' at line {self.line}, column {self.column}"

# Common variable errors
def check_undefined_variable(var_name: str, line: int, column: int):
    """Check for undefined variable"""
    return VariableError(f"Undefined variable: {var_name}", var_name, line, column)

def check_redeclared_variable(var_name: str, line: int, column: int):
    """Check for redeclared variable"""
    return VariableError(f"Variable already declared: {var_name}", var_name, line, column)
```

### Semantic Errors

```python
class SemanticError:
    """Semantic-related error"""
    
    def __init__(self, message: str, line: int = 0, column: int = 0):
        self.message = message
        self.line = line
        self.column = column
    
    def __str__(self):
        return f"Semantic error: {self.message} at line {self.line}, column {self.column}"

# Common semantic errors
def check_incomplete_match_case(line: int, column: int):
    """Check for incomplete match-case"""
    return SemanticError("Match-case must have default case", line, column)

def check_empty_struct(line: int, column: int):
    """Check for empty struct"""
    return SemanticError("Struct must have at least one member", line, column)
```

## Analysis Implementation

### Main Analyzer Class

```python
class SemanticAnalyzer:
    """Main semantic analyzer"""
    
    def __init__(self):
        self.symbol_table = {}
        self.errors = []
        self.warnings = []
    
    def analyze(self, ast: Program) -> List[str]:
        """Perform complete semantic analysis"""
        self.errors = []
        self.warnings = []
        self.symbol_table = {}
        
        # Phase 1: Collect declarations
        self._collect_declarations(ast)
        
        # Phase 2: Type checking
        self._check_types(ast)
        
        # Phase 3: Variable analysis
        self._analyze_variables(ast)
        
        # Phase 4: Semantic validation
        self._validate_semantics(ast)
        
        return self.errors
    
    def _collect_declarations(self, ast: Program):
        """Collect all declarations"""
        for stmt in ast.statements:
            if isinstance(stmt, Declaration):
                self._add_declaration(stmt)
            elif isinstance(stmt, StructDefinition):
                self._add_struct_definition(stmt)
    
    def _check_types(self, ast: Program):
        """Check type consistency"""
        for stmt in ast.statements:
            self._check_statement_types(stmt)
    
    def _analyze_variables(self, ast: Program):
        """Analyze variable usage"""
        for stmt in ast.statements:
            self._check_statement_variables(stmt)
    
    def _validate_semantics(self, ast: Program):
        """Validate semantic correctness"""
        for stmt in ast.statements:
            self._validate_statement(stmt)
```

### Type Checking Implementation

```python
def _check_statement_types(self, stmt: Statement):
    """Check types in statement"""
    if isinstance(stmt, Declaration):
        self._check_declaration_types(stmt)
    elif isinstance(stmt, Assignment):
        self._check_assignment_types(stmt)
    elif isinstance(stmt, MatchCase):
        self._check_match_case_types(stmt)

def _check_declaration_types(self, decl: Declaration):
    """Check declaration types"""
    if decl.value:
        expected_type = decl.type_node.type_name
        actual_type = self._get_expression_type(decl.value)
        
        if expected_type != actual_type:
            self.errors.append(
                f"Type mismatch in declaration '{decl.name}': "
                f"expected {expected_type}, got {actual_type}"
            )

def _get_expression_type(self, expr: Expression) -> str:
    """Get type of expression"""
    if isinstance(expr, Literal):
        return expr.literal_type.value
    elif isinstance(expr, Identifier):
        return self.symbol_table.get(expr.name, "unknown")
    elif isinstance(expr, BinaryOperation):
        return self._get_binary_operation_type(expr)
    else:
        return "unknown"
```

### Variable Analysis Implementation

```python
def _check_statement_variables(self, stmt: Statement):
    """Check variables in statement"""
    if isinstance(stmt, Declaration):
        self._check_declaration_variables(stmt)
    elif isinstance(stmt, Assignment):
        self._check_assignment_variables(stmt)
    elif isinstance(stmt, MatchCase):
        self._check_match_case_variables(stmt)

def _check_declaration_variables(self, decl: Declaration):
    """Check declaration variables"""
    if decl.name in self.symbol_table:
        self.errors.append(f"Variable already declared: {decl.name}")
    else:
        self.symbol_table[decl.name] = decl.type_node.type_name

def _check_assignment_variables(self, assign: Assignment):
    """Check assignment variables"""
    if assign.name not in self.symbol_table:
        self.errors.append(f"Undefined variable: {assign.name}")
    
    # Check if variable is being assigned to itself
    if isinstance(assign.value, Identifier) and assign.value.name == assign.name:
        self.warnings.append(f"Variable assigned to itself: {assign.name}")
```

## Advanced Analysis

### Control Flow Analysis

```python
class ControlFlowAnalyzer:
    """Analyze control flow"""
    
    def __init__(self):
        self.errors = []
    
    def analyze_control_flow(self, ast: Program) -> List[str]:
        """Analyze control flow patterns"""
        self.errors = []
        
        for stmt in ast.statements:
            if isinstance(stmt, MatchCase):
                self._analyze_match_case_flow(stmt)
        
        return self.errors
    
    def _analyze_match_case_flow(self, match: MatchCase):
        """Analyze match-case control flow"""
        # Check for unreachable cases
        self._check_unreachable_cases(match)
        
        # Check for redundant cases
        self._check_redundant_cases(match)
    
    def _check_unreachable_cases(self, match: MatchCase):
        """Check for unreachable cases"""
        # Implementation for checking unreachable cases
        pass
    
    def _check_redundant_cases(self, match: MatchCase):
        """Check for redundant cases"""
        # Implementation for checking redundant cases
        pass
```

### Data Flow Analysis

```python
class DataFlowAnalyzer:
    """Analyze data flow"""
    
    def __init__(self):
        self.errors = []
    
    def analyze_data_flow(self, ast: Program) -> List[str]:
        """Analyze data flow patterns"""
        self.errors = []
        
        # Track variable definitions and uses
        self._track_variable_flow(ast)
        
        return self.errors
    
    def _track_variable_flow(self, ast: Program):
        """Track variable definitions and uses"""
        # Implementation for tracking variable flow
        pass
```

## Error Reporting

### Error Formatting

```python
class ErrorFormatter:
    """Format error messages"""
    
    @staticmethod
    def format_error(error: str, line: int = 0, column: int = 0) -> str:
        """Format error message"""
        if line > 0 and column > 0:
            return f"Error at line {line}, column {column}: {error}"
        else:
            return f"Error: {error}"
    
    @staticmethod
    def format_warning(warning: str, line: int = 0, column: int = 0) -> str:
        """Format warning message"""
        if line > 0 and column > 0:
            return f"Warning at line {line}, column {column}: {warning}"
        else:
            return f"Warning: {warning}"
```

### Error Categories

```python
class ErrorCategory(Enum):
    TYPE_ERROR = "type_error"
    VARIABLE_ERROR = "variable_error"
    SEMANTIC_ERROR = "semantic_error"
    SYNTAX_ERROR = "syntax_error"

class CategorizedError:
    """Error with category"""
    
    def __init__(self, message: str, category: ErrorCategory, line: int = 0, column: int = 0):
        self.message = message
        self.category = category
        self.line = line
        self.column = column
    
    def __str__(self):
        return f"{self.category.value}: {self.message} at line {self.line}, column {self.column}"
```

## Testing

### Unit Tests

```python
def test_type_checking():
    """Test type checking"""
    analyzer = SemanticAnalyzer()
    
    # Test valid code
    parser = YuhoParser()
    ast = parser.parse("int x := 42;")
    errors = analyzer.analyze(ast)
    assert len(errors) == 0
    
    # Test type mismatch
    ast = parser.parse('int x := "hello";')
    errors = analyzer.analyze(ast)
    assert len(errors) > 0
    assert "type mismatch" in errors[0].lower()

def test_variable_analysis():
    """Test variable analysis"""
    analyzer = SemanticAnalyzer()
    
    # Test undefined variable
    parser = YuhoParser()
    ast = parser.parse("x := 42;")
    errors = analyzer.analyze(ast)
    assert len(errors) > 0
    assert "undefined variable" in errors[0].lower()

def test_semantic_validation():
    """Test semantic validation"""
    analyzer = SemanticAnalyzer()
    
    # Test incomplete match-case
    parser = YuhoParser()
    ast = parser.parse("""
    match {
        case condition := consequence "result";
    }
    """)
    errors = analyzer.analyze(ast)
    assert len(errors) > 0
    assert "default case" in errors[0].lower()
```

### Integration Tests

```python
def test_complete_analysis():
    """Test complete semantic analysis"""
    analyzer = SemanticAnalyzer()
    parser = YuhoParser()
    
    code = """
    struct Person {
        string name,
        int age
    }
    
    Person person := {
        name := "Alice",
        age := 25
    }
    
    match {
        case person.age >= 18 := consequence "adult";
        case _ := consequence "minor";
    }
    """
    
    ast = parser.parse(code)
    errors = analyzer.analyze(ast)
    assert len(errors) == 0
```

## Performance Considerations

### Analysis Optimization

```python
class OptimizedAnalyzer:
    """Optimized semantic analyzer"""
    
    def __init__(self):
        self.cache = {}
    
    def analyze(self, ast: Program) -> List[str]:
        """Optimized analysis with caching"""
        ast_hash = hash(str(ast))
        if ast_hash in self.cache:
            return self.cache[ast_hash]
        
        errors = self._analyze_internal(ast)
        self.cache[ast_hash] = errors
        return errors
```

### Memory Management

```python
class MemoryEfficientAnalyzer:
    """Memory-efficient semantic analyzer"""
    
    def __init__(self):
        self.symbol_table = {}
        self.errors = []
    
    def analyze(self, ast: Program) -> List[str]:
        """Memory-efficient analysis"""
        # Clear previous state
        self.symbol_table.clear()
        self.errors.clear()
        
        # Perform analysis
        self._analyze_ast(ast)
        
        # Return copy of errors
        return self.errors.copy()
```

## Best Practices

### Error Handling

```python
def safe_analyze(ast: Program) -> List[str]:
    """Safely analyze AST"""
    try:
        analyzer = SemanticAnalyzer()
        return analyzer.analyze(ast)
    except Exception as e:
        return [f"Analysis error: {str(e)}"]
```

### Performance

```python
def analyze_large_ast(ast: Program) -> List[str]:
    """Analyze large AST efficiently"""
    analyzer = SemanticAnalyzer()
    
    # Use streaming analysis for large ASTs
    if len(ast.statements) > 1000:
        return analyzer.analyze_streaming(ast)
    else:
        return analyzer.analyze(ast)
```

## Troubleshooting

### Common Issues

#### Issue 1: False Positives

```python
# Problem: False positive type errors
analyzer = SemanticAnalyzer()
ast = parser.parse("int x := 42;")
errors = analyzer.analyze(ast)
# Unexpected type error
```

**Solution**: Check type inference logic:

```python
def _get_expression_type(self, expr: Expression) -> str:
    """Get type of expression with better inference"""
    if isinstance(expr, Literal):
        return expr.literal_type.value
    elif isinstance(expr, Identifier):
        return self.symbol_table.get(expr.name, "unknown")
    # Add more type inference logic
```

#### Issue 2: Missing Errors

```python
# Problem: Missing semantic errors
analyzer = SemanticAnalyzer()
ast = parser.parse("match { case condition := consequence result; }")
errors = analyzer.analyze(ast)
# Should have error about missing default case
```

**Solution**: Improve semantic validation:

```python
def _validate_match_case(self, match: MatchCase):
    """Validate match-case with better checking"""
    if not match.cases:
        self.errors.append("Match-case must have at least one case")
        return
    
    has_default = any(case.condition is None for case in match.cases)
    if not has_default:
        self.errors.append("Match-case must have default case")
```

#### Issue 3: Performance Issues

```python
# Problem: Slow analysis
analyzer = SemanticAnalyzer()
ast = parser.parse(large_source)
errors = analyzer.analyze(ast)
# Takes too long
```

**Solution**: Use optimized analysis:

```python
class OptimizedAnalyzer:
    """Optimized analyzer"""
    
    def analyze(self, ast: Program) -> List[str]:
        """Optimized analysis"""
        # Use incremental analysis
        # Cache results
        # Skip redundant checks
        pass
```

## Next Steps

- [Lexer API](lexer.md) - Tokenization
- [Parser API](parser.md) - Parsing tokens into AST
- [AST API](ast.md) - Abstract Syntax Tree nodes
- [Transpilers API](transpilers.md) - Code generation
