# Transpilers API

The Yuho transpilers convert AST into various target formats for visualization and verification.

## Overview

The transpilers provide:

- **Mermaid Generation** - Create visual diagrams
- **Alloy Generation** - Generate formal specifications
- **Code Generation** - Convert to target formats
- **Format Validation** - Ensure output correctness

## Base Transpiler

### Abstract Base Class

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from ..ast_nodes import *

class BaseTranspiler(ABC):
    """Base class for all transpilers"""
    
    def __init__(self):
        self.output = []
        self.node_counter = 0
    
    @abstractmethod
    def transpile(self, program: Program) -> str:
        """Transpile program to target format"""
        pass
    
    def _process_statement(self, stmt: Statement):
        """Process individual statement"""
        if isinstance(stmt, StructDefinition):
            self._process_struct_definition(stmt)
        elif isinstance(stmt, MatchCase):
            self._process_match_case(stmt)
        elif isinstance(stmt, Declaration):
            self._process_declaration(stmt)
    
    @abstractmethod
    def _process_struct_definition(self, struct: StructDefinition):
        """Process struct definition"""
        pass
    
    @abstractmethod
    def _process_match_case(self, match: MatchCase):
        """Process match-case statement"""
        pass
    
    def _process_declaration(self, decl: Declaration):
        """Process variable declaration"""
        pass
```

## Mermaid Transpiler

### Flowchart Generation

```python
class MermaidTranspiler(BaseTranspiler):
    """Transpiles Yuho AST to Mermaid diagram syntax"""
    
    def transpile_to_flowchart(self, program: Program) -> str:
        """Generate Mermaid flowchart from Yuho program"""
        self.output = ["flowchart TD"]
        self.node_counter = 0
        
        for stmt in program.statements:
            self._process_statement_flowchart(stmt)
        
        return "\n".join(self.output)
    
    def _process_statement_flowchart(self, stmt: Statement):
        """Process statement for flowchart generation"""
        if isinstance(stmt, StructDefinition):
            self._add_struct_flowchart(stmt)
        elif isinstance(stmt, MatchCase):
            self._add_match_case_flowchart(stmt)
        elif isinstance(stmt, Declaration):
            self._add_declaration_flowchart(stmt)
    
    def _add_struct_flowchart(self, struct: StructDefinition):
        """Add struct definition to flowchart"""
        struct_id = f"S{self.node_counter}"
        self.node_counter += 1
        
        # Main struct node
        self.output.append(f"    {struct_id}[{struct.name}]")
        
        # Add member nodes
        for member in struct.members:
            member_id = f"M{self.node_counter}"
            self.node_counter += 1
            
            self.output.append(f"    {member_id}[{member.name}: {self.get_type_from_node(member.type_node)}]")
            self.output.append(f"    {struct_id} --> {member_id}")
    
    def _add_match_case_flowchart(self, match: MatchCase):
        """Add match-case to flowchart"""
        match_id = f"MC{self.node_counter}"
        self.node_counter += 1
        
        # Decision diamond
        condition_text = "Decision"
        if match.expression:
            condition_text = f"Match Expression"
        
        self.output.append(f"    {match_id}{{{condition_text}}}")
        
        # Add case branches
        for i, case in enumerate(match.cases):
            case_id = f"C{self.node_counter}"
            self.node_counter += 1
            
            if case.condition:
                case_text = f"Case {i + 1}"
            else:
                case_text = "Default"
            
            self.output.append(f"    {case_id}[{case_text}]")
            self.output.append(f"    {match_id} --> {case_id}")
            
            # Add consequence
            if not isinstance(case.consequence, PassStatement):
                cons_id = f"CO{self.node_counter}"
                self.node_counter += 1
                self.output.append(f"    {cons_id}[Consequence]")
                self.output.append(f"    {case_id} --> {cons_id}")
```

### Mindmap Generation

```python
def transpile_to_mindmap(self, program: Program) -> str:
    """Generate Mermaid mindmap from Yuho program"""
    self.output = ["mindmap"]
    self.node_counter = 0
    
    # Find main structs and their relationships
    structs = [stmt for stmt in program.statements if isinstance(stmt, StructDefinition)]
    match_cases = [stmt for stmt in program.statements if isinstance(stmt, MatchCase)]
    
    if structs:
        main_struct = structs[0]  # Use first struct as root
        self.output.append(f"  root((({main_struct.name})))")
        
        # Add struct members as branches
        for member in main_struct.members:
            self.output.append(f"    {member.name}")
            self.output.append(f"      {self.get_type_from_node(member.type_node)}")
    
    # Add match cases as decision branches
    for match_case in match_cases:
        self.output.append(f"    Decisions")
        for i, case in enumerate(match_case.cases):
            if case.condition:
                self.output.append(f"      Case{i + 1}")
            else:
                self.output.append(f"      Default")
    
    return "\n".join(self.output)
```

## Alloy Transpiler

### Specification Generation

```python
class AlloyTranspiler(BaseTranspiler):
    """Transpiles Yuho AST to Alloy specification language"""
    
    def __init__(self):
        self.signatures = []
        self.facts = []
        self.predicates = []
        self.functions = []
    
    def transpile(self, program: Program) -> str:
        """Generate Alloy specification from Yuho program"""
        self.signatures = []
        self.facts = []
        self.predicates = []
        self.functions = []
        
        # Process all statements
        for stmt in program.statements:
            self._process_statement(stmt)
        
        # Generate final Alloy code
        return self._generate_alloy_code()
    
    def _process_struct_definition(self, struct: StructDefinition):
        """Convert struct definition to Alloy signature"""
        sig_lines = [f"sig {struct.name} {{"]
        
        # Add fields
        for member in struct.members:
            alloy_type = self._get_alloy_type(member.type_node)
            sig_lines.append(f"  {member.name}: {alloy_type},")
        
        # Remove last comma and close signature
        if sig_lines[-1].endswith(','):
            sig_lines[-1] = sig_lines[-1][:-1]
        
        sig_lines.append("}")
        
        self.signatures.append("\n".join(sig_lines))
    
    def _process_match_case(self, match: MatchCase):
        """Convert match-case to Alloy predicates"""
        pred_name = f"MatchCase{len(self.predicates)}"
        pred_lines = [f"pred {pred_name}[x: univ] {{"]
        
        if match.expression:
            # Add condition for the expression being matched
            pred_lines.append("  // Match expression conditions")
        
        # Process each case
        for i, case in enumerate(match.cases):
            if case.condition is None:
                # Default case
                pred_lines.append("  // Default case")
                pred_lines.append("  else {")
            else:
                # Specific case condition
                condition_alloy = self._expression_to_alloy(case.condition)
                if i == 0:
                    pred_lines.append(f"  {condition_alloy} => {{")
                else:
                    pred_lines.append(f"  else {condition_alloy} => {{")
            
            # Add consequence
            if not isinstance(case.consequence, PassStatement):
                consequence_alloy = self._expression_to_alloy(case.consequence)
                pred_lines.append(f"    {consequence_alloy}")
            
            pred_lines.append("  }")
        
        pred_lines.append("}")
        self.predicates.append("\n".join(pred_lines))
```

### Type Mapping

```python
def _get_alloy_type(self, type_node: TypeNode) -> str:
    """Convert Yuho type to Alloy type"""
    if isinstance(type_node.type_name, YuhoType):
        mapping = {
            YuhoType.INT: "Int",
            YuhoType.FLOAT: "Int",  # Alloy doesn't have floats
            YuhoType.BOOL: "Bool",
            YuhoType.STRING: "String",
            YuhoType.PERCENT: "Int",
            YuhoType.MONEY: "Int",
            YuhoType.DATE: "String",
            YuhoType.DURATION: "String"
        }
        return mapping.get(type_node.type_name, "univ")
    else:
        # Custom type
        return str(type_node.type_name)

def _expression_to_alloy(self, expr: Expression) -> str:
    """Convert expression to Alloy syntax"""
    if isinstance(expr, Literal):
        return self._literal_to_alloy(expr)
    elif isinstance(expr, Identifier):
        return expr.name
    elif isinstance(expr, BinaryOperation):
        left = self._expression_to_alloy(expr.left)
        right = self._expression_to_alloy(expr.right)
        op = self._operator_to_alloy(expr.operator)
        return f"({left} {op} {right})"
    else:
        return "// Expression translation not implemented"
```

## Custom Transpilers

### Creating Custom Transpiler

```python
class CustomTranspiler(BaseTranspiler):
    """Custom transpiler for specific target"""
    
    def transpile(self, program: Program) -> str:
        """Transpile to custom format"""
        self.output = []
        self.node_counter = 0
        
        # Add header
        self.output.append("// Custom format output")
        self.output.append("")
        
        # Process statements
        for stmt in program.statements:
            self._process_statement(stmt)
        
        return "\n".join(self.output)
    
    def _process_struct_definition(self, struct: StructDefinition):
        """Process struct for custom format"""
        self.output.append(f"struct {struct.name} {{")
        for member in struct.members:
            self.output.append(f"  {member.name}: {member.type_node.type_name}")
        self.output.append("}")
        self.output.append("")
    
    def _process_match_case(self, match: MatchCase):
        """Process match-case for custom format"""
        self.output.append("match {")
        for case in match.cases:
            if case.condition:
                self.output.append(f"  case {case.condition} := consequence {case.consequence};")
            else:
                self.output.append(f"  case _ := consequence {case.consequence};")
        self.output.append("}")
        self.output.append("")
```

### Transpiler Registry

```python
class TranspilerRegistry:
    """Registry for transpilers"""
    
    def __init__(self):
        self.transpilers = {}
    
    def register(self, name: str, transpiler_class: type):
        """Register transpiler"""
        self.transpilers[name] = transpiler_class
    
    def get_transpiler(self, name: str) -> BaseTranspiler:
        """Get transpiler by name"""
        if name not in self.transpilers:
            raise ValueError(f"Unknown transpiler: {name}")
        return self.transpilers[name]()
    
    def list_transpilers(self) -> List[str]:
        """List available transpilers"""
        return list(self.transpilers.keys())

# Register transpilers
registry = TranspilerRegistry()
registry.register("mermaid", MermaidTranspiler)
registry.register("alloy", AlloyTranspiler)
registry.register("custom", CustomTranspiler)
```

## Transpiler Configuration

### Configuration Options

```python
@dataclass
class TranspilerConfig:
    """Configuration for transpilers"""
    output_format: str = "default"
    include_comments: bool = True
    optimize_output: bool = False
    custom_options: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.custom_options is None:
            self.custom_options = {}
```

### Configurable Transpiler

```python
class ConfigurableTranspiler(BaseTranspiler):
    """Transpiler with configuration options"""
    
    def __init__(self, config: TranspilerConfig = None):
        super().__init__()
        self.config = config or TranspilerConfig()
    
    def transpile(self, program: Program) -> str:
        """Transpile with configuration"""
        self.output = []
        self.node_counter = 0
        
        # Add header if comments enabled
        if self.config.include_comments:
            self.output.append("// Generated by Yuho transpiler")
            self.output.append("")
        
        # Process statements
        for stmt in program.statements:
            self._process_statement(stmt)
        
        # Optimize if requested
        if self.config.optimize_output:
            self._optimize_output()
        
        return "\n".join(self.output)
    
    def _optimize_output(self):
        """Optimize output based on configuration"""
        # Remove empty lines
        self.output = [line for line in self.output if line.strip()]
        
        # Remove duplicate lines
        self.output = list(dict.fromkeys(self.output))
```

## Error Handling

### Transpiler Errors

```python
class TranspilerError(Exception):
    """Transpiler error exception"""
    
    def __init__(self, message: str, line: int = 0, column: int = 0):
        self.message = message
        self.line = line
        self.column = column
        super().__init__(f"Transpiler error: {message} at line {line}, column {column}")

class UnsupportedFeatureError(TranspilerError):
    """Error for unsupported features"""
    pass

class OutputFormatError(TranspilerError):
    """Error for output format issues"""
    pass
```

### Error Handling in Transpilers

```python
def safe_transpile(transpiler: BaseTranspiler, program: Program) -> str:
    """Safely transpile program"""
    try:
        return transpiler.transpile(program)
    except TranspilerError as e:
        return f"Transpiler error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"
```

## Testing

### Unit Tests

```python
def test_mermaid_transpiler():
    """Test Mermaid transpiler"""
    transpiler = MermaidTranspiler()
    parser = YuhoParser()
    
    code = """
    struct Person {
        string name,
        int age
    }
    """
    
    ast = parser.parse(code)
    result = transpiler.transpile_to_flowchart(ast)
    
    assert "flowchart TD" in result
    assert "Person" in result
    assert "name: string" in result
    assert "age: int" in result

def test_alloy_transpiler():
    """Test Alloy transpiler"""
    transpiler = AlloyTranspiler()
    parser = YuhoParser()
    
    code = """
    struct Person {
        string name,
        int age
    }
    """
    
    ast = parser.parse(code)
    result = transpiler.transpile(ast)
    
    assert "sig Person" in result
    assert "name: String" in result
    assert "age: Int" in result
    assert "run {} for 5" in result
```

### Integration Tests

```python
def test_transpiler_integration():
    """Test transpiler integration"""
    parser = YuhoParser()
    mermaid_transpiler = MermaidTranspiler()
    alloy_transpiler = AlloyTranspiler()
    
    code = """
    struct Test {
        bool field
    }
    
    match {
        case field := consequence "true";
        case _ := consequence "false";
    }
    """
    
    ast = parser.parse(code)
    
    # Test Mermaid generation
    mermaid_result = mermaid_transpiler.transpile_to_flowchart(ast)
    assert "flowchart TD" in mermaid_result
    
    # Test Alloy generation
    alloy_result = alloy_transpiler.transpile(ast)
    assert "sig Test" in alloy_result
```

## Performance

### Optimization Techniques

```python
class OptimizedTranspiler(BaseTranspiler):
    """Optimized transpiler"""
    
    def __init__(self):
        super().__init__()
        self.cache = {}
    
    def transpile(self, program: Program) -> str:
        """Optimized transpilation with caching"""
        program_hash = hash(str(program))
        if program_hash in self.cache:
            return self.cache[program_hash]
        
        result = self._transpile_internal(program)
        self.cache[program_hash] = result
        return result
    
    def _transpile_internal(self, program: Program) -> str:
        """Internal transpilation logic"""
        # Implementation
        pass
```

### Memory Management

```python
class MemoryEfficientTranspiler(BaseTranspiler):
    """Memory-efficient transpiler"""
    
    def transpile(self, program: Program) -> str:
        """Memory-efficient transpilation"""
        # Use generators for large outputs
        # Stream output instead of storing all
        # Clear intermediate data
        pass
```

## Best Practices

### Transpiler Design

- Use abstract base classes
- Implement consistent interfaces
- Handle errors gracefully
- Optimize for performance

### Output Quality

- Generate clean, readable output
- Include appropriate comments
- Follow target format conventions
- Validate output correctness

### Error Handling

- Provide clear error messages
- Handle edge cases
- Validate input AST
- Report unsupported features

## Troubleshooting

### Common Issues

#### Issue 1: Output Format Errors

```python
# Problem: Invalid output format
transpiler = MermaidTranspiler()
result = transpiler.transpile_to_flowchart(ast)
# Invalid Mermaid syntax
```

**Solution**: Validate output format:

```python
def validate_mermaid_output(output: str) -> bool:
    """Validate Mermaid output"""
    required_elements = ["flowchart TD"]
    return all(element in output for element in required_elements)
```

#### Issue 2: Type Mapping Errors

```python
# Problem: Incorrect type mapping
alloy_type = transpiler._get_alloy_type(type_node)
# Expected: "Int", Actual: "unknown"
```

**Solution**: Improve type mapping:

```python
def _get_alloy_type(self, type_node: TypeNode) -> str:
    """Convert Yuho type to Alloy type with better mapping"""
    mapping = {
        YuhoType.INT: "Int",
        YuhoType.FLOAT: "Int",
        YuhoType.BOOL: "Bool",
        YuhoType.STRING: "String",
        # Add more mappings
    }
    return mapping.get(type_node.type_name, "univ")
```

#### Issue 3: Performance Issues

```python
# Problem: Slow transpilation
transpiler = MermaidTranspiler()
result = transpiler.transpile(large_ast)
# Takes too long
```

**Solution**: Use optimized transpiler:

```python
class OptimizedMermaidTranspiler(MermaidTranspiler):
    """Optimized Mermaid transpiler"""
    
    def transpile_to_flowchart(self, program: Program) -> str:
        """Optimized flowchart generation"""
        # Use streaming output
        # Cache intermediate results
        # Skip unnecessary processing
        pass
```

## Next Steps

- [Lexer API](lexer.md) - Tokenization
- [Parser API](parser.md) - Parsing tokens into AST
- [AST API](ast.md) - Abstract Syntax Tree nodes
- [Semantic API](semantic.md) - Semantic analysis
