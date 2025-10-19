# AST API

The Yuho Abstract Syntax Tree (AST) represents the parsed structure of Yuho code.

## Overview

The AST provides:

- **Program Structure** - Complete program representation
- **Type Safety** - Strongly typed nodes
- **Traversal** - Easy navigation of code structure
- **Transformation** - Code modification and generation

## AST Node Types

### Base Node

```python
@dataclass
class ASTNode:
    """Base class for all AST nodes"""
    pass
```

### Program Structure

```python
@dataclass
class Program(ASTNode):
    """Root AST node representing a complete Yuho program"""
    statements: List[ASTNode]

@dataclass
class ImportStatement(ASTNode):
    """Import statement: referencing StructName from module_name"""
    struct_name: str
    module_name: str
```

### Type Definitions

```python
@dataclass
class TypeNode(ASTNode):
    """Type annotation node"""
    type_name: Union[YuhoType, str]

@dataclass
class QualifiedIdentifier(ASTNode):
    """Qualified identifier like module.StructName"""
    parts: List[str]
    
    def __str__(self):
        return ".".join(self.parts)
```

### Expressions

```python
@dataclass
class Expression(ASTNode):
    """Base class for all expressions"""
    pass

@dataclass
class Literal(Expression):
    """Literal value expression"""
    value: Any
    literal_type: YuhoType

@dataclass
class Identifier(Expression):
    """Variable or function identifier"""
    name: str

@dataclass
class BinaryOperation(Expression):
    """Binary operation expression"""
    left: Expression
    operator: Operator
    right: Expression

@dataclass
class UnaryOperation(Expression):
    """Unary operation expression"""
    operator: str
    operand: Expression
```

### Statements

```python
@dataclass
class Statement(ASTNode):
    """Base class for all statements"""
    pass

@dataclass
class Declaration(Statement):
    """Variable declaration"""
    type_node: TypeNode
    name: str
    value: Optional[Expression] = None

@dataclass
class Assignment(Statement):
    """Variable assignment"""
    name: str
    value: Expression

@dataclass
class PassStatement(Statement):
    """Pass statement (no-op)"""
    pass
```

### Structures

```python
@dataclass
class StructMember(ASTNode):
    """Member of a struct definition"""
    type_node: TypeNode
    name: str

@dataclass
class StructDefinition(Statement):
    """Struct definition"""
    name: str
    members: List[StructMember]

@dataclass
class StructInstantiation(Expression):
    """Struct instantiation with field assignments"""
    struct_type: QualifiedIdentifier
    name: str
    fields: List['FieldAssignment']

@dataclass
class FieldAssignment(ASTNode):
    """Field assignment in struct instantiation"""
    field_name: str
    value: Expression
```

### Control Structures

```python
@dataclass
class CaseClause(ASTNode):
    """Case clause in match statement"""
    condition: Optional[Expression]  # None for wildcard (_)
    consequence: Expression

@dataclass
class MatchCase(Statement):
    """Match-case control structure"""
    expression: Optional[Expression]  # None for bare match {}
    cases: List[CaseClause]
```

### Functions

```python
@dataclass
class Parameter(ASTNode):
    """Function parameter"""
    type_node: TypeNode
    name: str

@dataclass
class FunctionDefinition(Statement):
    """Function definition"""
    name: str
    parameters: List[Parameter]
    return_type: TypeNode
    body: List[Statement]

@dataclass
class FunctionCall(Expression):
    """Function call expression"""
    name: str
    arguments: List[Expression]
```

## Type System

### Yuho Types

```python
class YuhoType(Enum):
    INT = "int"
    FLOAT = "float"
    PERCENT = "percent"
    MONEY = "money"
    DATE = "date"
    DURATION = "duration"
    BOOL = "bool"
    STRING = "string"
    CUSTOM = "custom"
```

### Operators

```python
class Operator(Enum):
    PLUS = "+"
    MINUS = "-"
    MULT = "*"
    DIV = "/"
    EQUAL = "=="
    NOTEQUAL = "!="
    GT = ">"
    LT = "<"
    AND = "&&"
    OR = "||"
```

## AST Construction

### Basic Construction

```python
from yuho_v3.ast_nodes import *

# Create a simple struct
struct_def = StructDefinition(
    name="Person",
    members=[
        StructMember(
            type_node=TypeNode(type_name=YuhoType.STRING),
            name="name"
        ),
        StructMember(
            type_node=TypeNode(type_name=YuhoType.INT),
            name="age"
        )
    ]
)

# Create a program
program = Program(statements=[struct_def])
```

### Complex Construction

```python
# Create a match-case statement
match_case = MatchCase(
    expression=None,
    cases=[
        CaseClause(
            condition=BinaryOperation(
                left=Identifier(name="deception"),
                operator=Operator.AND,
                right=Identifier(name="dishonest")
            ),
            consequence=Literal(
                value="guilty",
                literal_type=YuhoType.STRING
            )
        ),
        CaseClause(
            condition=None,  # Default case
            consequence=Literal(
                value="not guilty",
                literal_type=YuhoType.STRING
            )
        )
    ]
)

# Add to program
program.statements.append(match_case)
```

## AST Traversal

### Visitor Pattern

```python
class ASTVisitor:
    """Base visitor for AST traversal"""
    
    def visit(self, node: ASTNode):
        """Visit a node"""
        method_name = f"visit_{type(node).__name__}"
        method = getattr(self, method_name, self.generic_visit)
        return method(node)
    
    def generic_visit(self, node: ASTNode):
        """Generic visit method"""
        for field in node.__dataclass_fields__:
            value = getattr(node, field)
            if isinstance(value, ASTNode):
                self.visit(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, ASTNode):
                        self.visit(item)
```

### Custom Visitors

```python
class PrintVisitor(ASTVisitor):
    """Visitor that prints AST structure"""
    
    def visit_Program(self, node: Program):
        print("Program:")
        for stmt in node.statements:
            self.visit(stmt)
    
    def visit_StructDefinition(self, node: StructDefinition):
        print(f"  Struct: {node.name}")
        for member in node.members:
            print(f"    {member.name}: {member.type_node.type_name}")
    
    def visit_MatchCase(self, node: MatchCase):
        print("  Match:")
        for case in node.cases:
            if case.condition:
                print(f"    Case: {case.condition}")
            else:
                print("    Default case")
            print(f"    Consequence: {case.consequence}")
```

### Transformation Visitors

```python
class TransformVisitor(ASTVisitor):
    """Visitor that transforms AST"""
    
    def visit_StructDefinition(self, node: StructDefinition):
        """Transform struct definition"""
        # Add validation to struct
        validation = self._create_validation(node)
        return [node, validation]
    
    def _create_validation(self, struct: StructDefinition):
        """Create validation for struct"""
        # Implementation
        pass
```

## AST Analysis

### Type Analysis

```python
class TypeAnalyzer(ASTVisitor):
    """Analyze types in AST"""
    
    def __init__(self):
        self.symbol_table = {}
    
    def visit_Declaration(self, node: Declaration):
        """Analyze variable declaration"""
        self.symbol_table[node.name] = node.type_node.type_name
    
    def visit_Identifier(self, node: Identifier):
        """Analyze identifier usage"""
        if node.name in self.symbol_table:
            return self.symbol_table[node.name]
        else:
            raise SemanticError(f"Undefined variable: {node.name}")
```

### Semantic Analysis

```python
class SemanticAnalyzer(ASTVisitor):
    """Perform semantic analysis"""
    
    def __init__(self):
        self.errors = []
    
    def visit_MatchCase(self, node: MatchCase):
        """Analyze match-case completeness"""
        has_default = any(case.condition is None for case in node.cases)
        if not has_default:
            self.errors.append("Match-case must have default case")
    
    def visit_StructDefinition(self, node: StructDefinition):
        """Analyze struct definition"""
        if not node.members:
            self.errors.append("Struct must have at least one member")
```

## AST Generation

### From Parser

```python
from yuho_v3.parser import YuhoParser

# Parse source code
parser = YuhoParser()
ast = parser.parse("""
struct Person {
    string name,
    int age
}

match {
    case age >= 18 := consequence "adult";
    case _ := consequence "minor";
}
""")

# Access AST nodes
print(f"Program has {len(ast.statements)} statements")
for stmt in ast.statements:
    print(f"  {type(stmt).__name__}")
```

### Manual Construction

```python
# Create AST manually
program = Program(statements=[
    StructDefinition(
        name="Person",
        members=[
            StructMember(
                type_node=TypeNode(type_name=YuhoType.STRING),
                name="name"
            ),
            StructMember(
                type_node=TypeNode(type_name=YuhoType.INT),
                name="age"
            )
        ]
    ),
    MatchCase(
        expression=None,
        cases=[
            CaseClause(
                condition=BinaryOperation(
                    left=Identifier(name="age"),
                    operator=Operator.GT,
                    right=Literal(value=18, literal_type=YuhoType.INT)
                ),
                consequence=Literal(value="adult", literal_type=YuhoType.STRING)
            ),
            CaseClause(
                condition=None,
                consequence=Literal(value="minor", literal_type=YuhoType.STRING)
            )
        ]
    )
])
```

## AST Serialization

### JSON Serialization

```python
import json
from dataclasses import asdict

def ast_to_json(ast: Program) -> str:
    """Convert AST to JSON"""
    return json.dumps(asdict(ast), indent=2)

def json_to_ast(json_str: str) -> Program:
    """Convert JSON to AST"""
    data = json.loads(json_str)
    return Program(**data)
```

### Pickle Serialization

```python
import pickle

def save_ast(ast: Program, filename: str):
    """Save AST to file"""
    with open(filename, 'wb') as f:
        pickle.dump(ast, f)

def load_ast(filename: str) -> Program:
    """Load AST from file"""
    with open(filename, 'rb') as f:
        return pickle.load(f)
```

## AST Validation

### Structure Validation

```python
class ASTValidator:
    """Validate AST structure"""
    
    def validate(self, ast: Program) -> List[str]:
        """Validate AST and return errors"""
        errors = []
        
        for stmt in ast.statements:
            if isinstance(stmt, StructDefinition):
                errors.extend(self._validate_struct(stmt))
            elif isinstance(stmt, MatchCase):
                errors.extend(self._validate_match_case(stmt))
        
        return errors
    
    def _validate_struct(self, struct: StructDefinition) -> List[str]:
        """Validate struct definition"""
        errors = []
        
        if not struct.name:
            errors.append("Struct must have a name")
        
        if not struct.members:
            errors.append("Struct must have at least one member")
        
        return errors
    
    def _validate_match_case(self, match: MatchCase) -> List[str]:
        """Validate match-case statement"""
        errors = []
        
        if not match.cases:
            errors.append("Match-case must have at least one case")
        
        has_default = any(case.condition is None for case in match.cases)
        if not has_default:
            errors.append("Match-case must have default case")
        
        return errors
```

## AST Transformation

### Code Generation

```python
class CodeGenerator(ASTVisitor):
    """Generate code from AST"""
    
    def visit_Program(self, node: Program) -> str:
        """Generate program code"""
        lines = []
        for stmt in node.statements:
            lines.append(self.visit(stmt))
        return "\n".join(lines)
    
    def visit_StructDefinition(self, node: StructDefinition) -> str:
        """Generate struct code"""
        lines = [f"struct {node.name} {{"]
        for member in node.members:
            lines.append(f"    {member.type_node.type_name} {member.name},")
        lines.append("}")
        return "\n".join(lines)
    
    def visit_MatchCase(self, node: MatchCase) -> str:
        """Generate match-case code"""
        lines = ["match {"]
        for case in node.cases:
            if case.condition:
                lines.append(f"    case {case.condition} := consequence {case.consequence};")
            else:
                lines.append(f"    case _ := consequence {case.consequence};")
        lines.append("}")
        return "\n".join(lines)
```

### Optimization

```python
class ASTOptimizer(ASTVisitor):
    """Optimize AST"""
    
    def visit_BinaryOperation(self, node: BinaryOperation) -> Expression:
        """Optimize binary operations"""
        if isinstance(node.left, Literal) and isinstance(node.right, Literal):
            # Constant folding
            return self._fold_constants(node)
        return node
    
    def _fold_constants(self, node: BinaryOperation) -> Literal:
        """Fold constant expressions"""
        # Implementation
        pass
```

## Testing

### Unit Tests

```python
def test_ast_construction():
    """Test AST construction"""
    struct = StructDefinition(
        name="Person",
        members=[
            StructMember(
                type_node=TypeNode(type_name=YuhoType.STRING),
                name="name"
            )
        ]
    )
    
    assert struct.name == "Person"
    assert len(struct.members) == 1
    assert struct.members[0].name == "name"
```

### Integration Tests

```python
def test_ast_parsing():
    """Test AST parsing"""
    parser = YuhoParser()
    ast = parser.parse("struct Person { string name }")
    
    assert isinstance(ast, Program)
    assert len(ast.statements) == 1
    assert isinstance(ast.statements[0], StructDefinition)
```

### Performance Tests

```python
def test_ast_performance():
    """Test AST performance"""
    parser = YuhoParser()
    code = "struct Person { string name, int age }" * 100
    
    start_time = time.time()
    ast = parser.parse(code)
    end_time = time.time()
    
    assert (end_time - start_time) < 1.0
```

## Best Practices

### AST Design

- Use dataclasses for all nodes
- Include type hints for all fields
- Use enums for constants
- Keep nodes immutable

### Traversal

- Use visitor pattern for traversal
- Separate concerns in different visitors
- Handle errors gracefully
- Optimize for performance

### Validation

- Validate AST structure
- Check semantic correctness
- Ensure completeness
- Handle edge cases

## Troubleshooting

### Common Issues

#### Issue 1: Circular References

```python
# Problem: Circular references in AST
struct_a = StructDefinition(name="A", members=[])
struct_b = StructDefinition(name="B", members=[])
struct_a.members.append(StructMember(type_node=TypeNode(type_name="B"), name="b"))
struct_b.members.append(StructMember(type_node=TypeNode(type_name="A"), name="a"))
```

**Solution**: Use weak references or separate type system:

```python
# Use string references instead of direct references
struct_a.members.append(StructMember(type_node=TypeNode(type_name="B"), name="b"))
```

#### Issue 2: Memory Usage

```python
# Problem: High memory usage with large ASTs
ast = parser.parse(large_source)
# Memory usage too high
```

**Solution**: Use streaming or lazy evaluation:

```python
class LazyAST:
    """Lazy AST evaluation"""
    
    def __init__(self, source: str):
        self.source = source
        self._ast = None
    
    @property
    def ast(self):
        if self._ast is None:
            self._ast = parser.parse(self.source)
        return self._ast
```

#### Issue 3: Type Safety

```python
# Problem: Type errors in AST
node = StructDefinition(name="Person", members="invalid")
# TypeError: members must be List[StructMember]
```

**Solution**: Use type hints and validation:

```python
@dataclass
class StructDefinition(Statement):
    name: str
    members: List[StructMember]  # Type hint
    
    def __post_init__(self):
        if not isinstance(self.members, list):
            raise TypeError("members must be a list")
```

## Next Steps

- [Lexer API](lexer.md) - Tokenization
- [Parser API](parser.md) - Parsing tokens into AST
- [Semantic API](semantic.md) - Semantic analysis
- [Transpilers API](transpilers.md) - Code generation
