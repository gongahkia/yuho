# Testing Guide

Comprehensive guide to testing Yuho code and ensuring legal accuracy.

## Overview

Testing in Yuho involves multiple layers:

- **Unit Tests** - Test individual components
- **Integration Tests** - Test complete workflows
- **Legal Tests** - Test legal accuracy
- **Performance Tests** - Test performance characteristics

## Test Structure

### Test Organization

```
yuho_v3/tests/
├── __init__.py
├── conftest.py
├── test_lexer.py
├── test_parser.py
├── test_semantic_analyzer.py
├── test_transpilers.py
├── test_integration.py
└── test_legal.py
```

### Test Categories

- **Parser Tests** - Test syntax parsing
- **Semantic Tests** - Test semantic analysis
- **Transpiler Tests** - Test code generation
- **Integration Tests** - Test complete workflows
- **Legal Tests** - Test legal accuracy

## Running Tests

### Basic Test Execution

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_parser.py

# Run specific test
pytest tests/test_parser.py::test_basic_parsing

# Run with verbose output
pytest -v
```

### Test Coverage

```bash
# Run with coverage
pytest --cov=yuho_v3

# Generate coverage report
pytest --cov=yuho_v3 --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Test Options

```bash
# Run tests in parallel
pytest -n auto

# Run tests with specific markers
pytest -m "not slow"

# Run tests with specific pattern
pytest -k "test_parser"
```

## Writing Tests

### Basic Test Structure

```python
import pytest
from yuho_v3.parser import YuhoParser
from yuho_v3.semantic_analyzer import SemanticAnalyzer

def test_basic_parsing():
    """Test basic parsing functionality"""
    parser = YuhoParser()
    code = """
    struct Person {
        string name,
        int age
    }
    """
    
    ast = parser.parse(code)
    assert ast is not None
    assert len(ast.statements) == 1
    assert ast.statements[0].name == "Person"
```

### Test Fixtures

```python
import pytest

@pytest.fixture
def parser():
    """Create parser instance for testing"""
    return YuhoParser()

@pytest.fixture
def semantic_analyzer():
    """Create semantic analyzer for testing"""
    return SemanticAnalyzer()

@pytest.fixture
def sample_code():
    """Sample Yuho code for testing"""
    return """
    struct Test {
        bool field
    }
    
    match {
        case field := consequence "true";
        case _ := consequence "false";
    }
    """
```

### Parametrized Tests

```python
import pytest

@pytest.mark.parametrize("code,expected", [
    ("int x := 42;", True),
    ("string s := \"hello\";", True),
    ("bool b := TRUE;", True),
    ("invalid syntax", False),
])
def test_variable_declaration(parser, code, expected):
    """Test variable declaration parsing"""
    try:
        ast = parser.parse(code)
        result = ast is not None
    except:
        result = False
    
    assert result == expected
```

## Parser Tests

### Basic Parsing Tests

```python
def test_struct_parsing():
    """Test struct definition parsing"""
    parser = YuhoParser()
    code = """
    struct Person {
        string name,
        int age
    }
    """
    
    ast = parser.parse(code)
    assert ast is not None
    assert len(ast.statements) == 1
    
    struct = ast.statements[0]
    assert struct.name == "Person"
    assert len(struct.members) == 2
    assert struct.members[0].name == "name"
    assert struct.members[1].name == "age"
```

### Error Handling Tests

```python
def test_syntax_error():
    """Test syntax error handling"""
    parser = YuhoParser()
    code = "struct Person { string name, int age"  # Missing closing brace
    
    with pytest.raises(SyntaxError):
        parser.parse(code)
```

### Complex Parsing Tests

```python
def test_match_case_parsing():
    """Test match-case statement parsing"""
    parser = YuhoParser()
    code = """
    match {
        case condition1 := consequence "result1";
        case condition2 := consequence "result2";
        case _ := consequence "default";
    }
    """
    
    ast = parser.parse(code)
    assert ast is not None
    assert len(ast.statements) == 1
    
    match_case = ast.statements[0]
    assert len(match_case.cases) == 3
    assert match_case.cases[0].condition is not None
    assert match_case.cases[1].condition is not None
    assert match_case.cases[2].condition is None  # Default case
```

## Semantic Tests

### Type Checking Tests

```python
def test_type_checking():
    """Test type checking functionality"""
    analyzer = SemanticAnalyzer()
    code = """
    struct Person {
        string name,
        int age
    }
    
    Person person := {
        name := "Alice",
        age := 25
    }
    """
    
    parser = YuhoParser()
    ast = parser.parse(code)
    errors = analyzer.analyze(ast)
    
    assert len(errors) == 0
```

### Error Detection Tests

```python
def test_type_mismatch():
    """Test type mismatch detection"""
    analyzer = SemanticAnalyzer()
    code = """
    int age := "25";  # Type mismatch
    """
    
    parser = YuhoParser()
    ast = parser.parse(code)
    errors = analyzer.analyze(ast)
    
    assert len(errors) > 0
    assert "type mismatch" in str(errors[0]).lower()
```

### Completeness Tests

```python
def test_match_case_completeness():
    """Test match-case completeness"""
    analyzer = SemanticAnalyzer()
    code = """
    bool flag := TRUE;
    
    match flag {
        case TRUE := consequence "true";
        # Missing FALSE case
    }
    """
    
    parser = YuhoParser()
    ast = parser.parse(code)
    errors = analyzer.analyze(ast)
    
    assert len(errors) > 0
    assert "incomplete" in str(errors[0]).lower()
```

## Transpiler Tests

### Mermaid Transpiler Tests

```python
def test_mermaid_flowchart():
    """Test Mermaid flowchart generation"""
    from yuho_v3.transpilers.mermaid_transpiler import MermaidTranspiler
    
    parser = YuhoParser()
    transpiler = MermaidTranspiler()
    
    code = """
    struct Test {
        bool field
    }
    """
    
    ast = parser.parse(code)
    result = transpiler.transpile_to_flowchart(ast)
    
    assert "flowchart TD" in result
    assert "Test" in result
    assert "field: bool" in result
```

### Alloy Transpiler Tests

```python
def test_alloy_generation():
    """Test Alloy specification generation"""
    from yuho_v3.transpilers.alloy_transpiler import AlloyTranspiler
    
    parser = YuhoParser()
    transpiler = AlloyTranspiler()
    
    code = """
    struct Test {
        bool field
    }
    """
    
    ast = parser.parse(code)
    result = transpiler.transpile(ast)
    
    assert "sig Test" in result
    assert "field: Bool" in result
    assert "run {} for 5" in result
```

## Legal Tests

### Legal Accuracy Tests

```python
def test_cheating_offense():
    """Test cheating offense legal accuracy"""
    parser = YuhoParser()
    code = """
    // Section 415 - Cheating
    struct Cheating {
        bool deception,
        bool dishonest,
        bool harm
    }
    
    match {
        case deception && dishonest && harm :=
            consequence "guilty of cheating";
        case _ :=
            consequence "not guilty of cheating";
    }
    """
    
    ast = parser.parse(code)
    assert ast is not None
    
    # Verify legal elements are present
    struct = ast.statements[0]
    assert struct.name == "Cheating"
    assert len(struct.members) == 3
    assert any(member.name == "deception" for member in struct.members)
    assert any(member.name == "dishonest" for member in struct.members)
    assert any(member.name == "harm" for member in struct.members)
```

### Legal Logic Tests

```python
def test_legal_logic_completeness():
    """Test legal logic completeness"""
    parser = YuhoParser()
    code = """
    struct LegalOffense {
        bool element1,
        bool element2,
        bool element3
    }
    
    match {
        case element1 && element2 && element3 :=
            consequence "guilty";
        case _ :=
            consequence "not guilty";
    }
    """
    
    ast = parser.parse(code)
    assert ast is not None
    
    # Verify all elements are required
    match_case = ast.statements[1]
    assert len(match_case.cases) == 2
    assert match_case.cases[0].condition is not None
    assert match_case.cases[1].condition is None  # Default case
```

### Legal Validation Tests

```python
def test_legal_validation():
    """Test legal validation functionality"""
    parser = YuhoParser()
    code = """
    struct Cheating {
        bool deception,
        bool dishonest,
        bool harm
    }
    """
    
    ast = parser.parse(code)
    
    # Verify legal structure
    struct = ast.statements[0]
    assert struct.name == "Cheating"
    
    # Verify required elements
    required_elements = ["deception", "dishonest", "harm"]
    actual_elements = [member.name for member in struct.members]
    
    for element in required_elements:
        assert element in actual_elements
```

## Integration Tests

### Complete Workflow Tests

```python
def test_complete_workflow():
    """Test complete Yuho workflow"""
    parser = YuhoParser()
    analyzer = SemanticAnalyzer()
    transpiler = MermaidTranspiler()
    
    code = """
    struct Test {
        bool field
    }
    
    match {
        case field := consequence "true";
        case _ := consequence "false";
    }
    """
    
    # Parse
    ast = parser.parse(code)
    assert ast is not None
    
    # Analyze
    errors = analyzer.analyze(ast)
    assert len(errors) == 0
    
    # Transpile
    result = transpiler.transpile_to_flowchart(ast)
    assert "flowchart TD" in result
```

### CLI Integration Tests

```python
def test_cli_integration():
    """Test CLI integration"""
    import subprocess
    import tempfile
    import os
    
    code = """
    struct Test {
        bool field
    }
    """
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yh', delete=False) as f:
        f.write(code)
        f.flush()
        
        try:
            # Test check command
            result = subprocess.run(['yuho', 'check', f.name], 
                                  capture_output=True, text=True)
            assert result.returncode == 0
            
            # Test draw command
            result = subprocess.run(['yuho', 'draw', f.name], 
                                  capture_output=True, text=True)
            assert result.returncode == 0
            assert "flowchart TD" in result.stdout
            
        finally:
            os.unlink(f.name)
```

## Performance Tests

### Parsing Performance

```python
import time

def test_parsing_performance():
    """Test parsing performance"""
    parser = YuhoParser()
    code = """
    struct Test {
        bool field
    }
    """ * 100  # Repeat 100 times
    
    start_time = time.time()
    ast = parser.parse(code)
    end_time = time.time()
    
    assert ast is not None
    assert (end_time - start_time) < 1.0  # Should complete in under 1 second
```

### Transpilation Performance

```python
def test_transpilation_performance():
    """Test transpilation performance"""
    parser = YuhoParser()
    transpiler = MermaidTranspiler()
    
    code = """
    struct Test {
        bool field
    }
    """ * 100  # Repeat 100 times
    
    ast = parser.parse(code)
    
    start_time = time.time()
    result = transpiler.transpile_to_flowchart(ast)
    end_time = time.time()
    
    assert result is not None
    assert (end_time - start_time) < 2.0  # Should complete in under 2 seconds
```

## Test Data

### Sample Legal Code

```python
SAMPLE_CHEATING_CODE = """
// Section 415 - Cheating
struct Cheating {
    string accused,
    bool deception,
    bool dishonest,
    bool harm
}

Cheating case1 := {
    accused := "Alice",
    deception := TRUE,
    dishonest := TRUE,
    harm := TRUE
};

match {
    case case1.deception && case1.dishonest && case1.harm :=
        consequence "guilty of cheating";
    case _ :=
        consequence "not guilty of cheating";
}
"""

SAMPLE_THEFT_CODE = """
// Section 378 - Theft
struct Theft {
    bool dishonestIntention,
    bool movableProperty,
    bool withoutConsent,
    bool movedProperty
}

match {
    case dishonestIntention && movableProperty && 
         withoutConsent && movedProperty :=
        consequence "guilty of theft";
    case _ :=
        consequence "not guilty of theft";
}
"""
```

### Test Fixtures

```python
@pytest.fixture
def sample_legal_codes():
    """Sample legal codes for testing"""
    return {
        "cheating": SAMPLE_CHEATING_CODE,
        "theft": SAMPLE_THEFT_CODE
    }

@pytest.fixture
def parser():
    """Parser instance for testing"""
    return YuhoParser()

@pytest.fixture
def analyzer():
    """Semantic analyzer for testing"""
    return SemanticAnalyzer()
```

## Test Configuration

### pytest.ini

```ini
[tool:pytest]
testpaths = yuho_v3/tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -ra -q --strict-markers --cov=yuho_v3 --cov-report=html --cov-report=term-missing
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    legal: marks tests as legal tests
    integration: marks tests as integration tests
```

### conftest.py

```python
import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

@pytest.fixture(scope="session")
def parser():
    """Create parser instance for testing"""
    from yuho_v3.parser import YuhoParser
    return YuhoParser()

@pytest.fixture(scope="session")
def analyzer():
    """Create semantic analyzer for testing"""
    from yuho_v3.semantic_analyzer import SemanticAnalyzer
    return SemanticAnalyzer()
```

## Continuous Integration

### GitHub Actions

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, 3.10, 3.11, 3.12]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v3
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run tests
      run: |
        pytest --cov=yuho_v3 --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

## Best Practices

### Test Organization

- Group related tests together
- Use descriptive test names
- Keep tests focused and simple
- Use fixtures for common setup

### Test Data

- Use realistic test data
- Include edge cases
- Test both valid and invalid inputs
- Use legal examples when appropriate

### Test Coverage

- Aim for high test coverage
- Test all public functions
- Test error conditions
- Test legal accuracy

### Performance

- Test performance characteristics
- Use appropriate timeouts
- Test with realistic data sizes
- Monitor performance regressions

## Troubleshooting

### Common Issues

#### Issue 1: Import Errors

```python
# Problem: Import errors in tests
from yuho_v3.parser import YuhoParser  # ImportError
```

**Solution**: Add parent directory to path:

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
```

#### Issue 2: Test Failures

```python
# Problem: Tests failing unexpectedly
def test_parsing():
    parser = YuhoParser()
    ast = parser.parse("invalid syntax")
    assert ast is not None  # Fails
```

**Solution**: Handle exceptions properly:

```python
def test_parsing():
    parser = YuhoParser()
    with pytest.raises(SyntaxError):
        parser.parse("invalid syntax")
```

#### Issue 3: Coverage Issues

```python
# Problem: Low test coverage
pytest --cov=yuho_v3
# Coverage: 45%
```

**Solution**: Add more tests:

```python
def test_missing_function():
    """Test previously untested function"""
    # Add test for missing function
    pass
```

## Next Steps

- [Contributing Guide](contributing.md) - How to contribute to Yuho
- [Docker Guide](docker.md) - Container development
- [Architecture Guide](architecture.md) - Understanding Yuho's architecture
- [API Reference](../api/parser.md) - Complete API documentation
