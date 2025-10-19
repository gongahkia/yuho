# Lexer API

The Yuho lexer tokenizes source code into a stream of tokens for parsing.

## Overview

The lexer is responsible for:

- **Tokenization** - Converting source code to tokens
- **Token Classification** - Identifying token types
- **Error Detection** - Finding lexical errors
- **Position Tracking** - Recording token positions

## Basic Usage

```python
from yuho_v3.lexer import YuhoLexer

# Create lexer instance
lexer = YuhoLexer()

# Tokenize source code
tokens = lexer.tokenize("struct Person { string name, int age }")

# Process tokens
for token in tokens:
    print(f"{token.type}: {token.value}")
```

## Token Types

### Keywords

```python
# Legal keywords
KEYWORDS = {
    'struct', 'match', 'case', 'consequence', 'func',
    'true', 'false', 'pass', 'referencing', 'from'
}

# Type keywords
TYPE_KEYWORDS = {
    'int', 'float', 'bool', 'string', 'money', 'date',
    'duration', 'percent'
}
```

### Operators

```python
# Arithmetic operators
ARITHMETIC_OPERATORS = {
    '+', '-', '*', '/', '//', '%'
}

# Comparison operators
COMPARISON_OPERATORS = {
    '==', '!=', '>', '<', '>=', '<='
}

# Logical operators
LOGICAL_OPERATORS = {
    'and', 'or', 'not', '&&', '||', '!'
}
```

### Literals

```python
# String literals
STRING_LITERAL = r'"[^"]*"'

# Integer literals
INTEGER_LITERAL = r'\d+'

# Float literals
FLOAT_LITERAL = r'\d+\.\d+'

# Boolean literals
BOOLEAN_LITERAL = r'true|false'

# Money literals
MONEY_LITERAL = r'\$\d+(,\d{3})*(\.\d{2})?'

# Date literals
DATE_LITERAL = r'\d{2}-\d{2}-\d{4}'
```

## Token Structure

### Token Class

```python
@dataclass
class Token:
    type: str
    value: str
    line: int
    column: int
    position: int
```

### Token Properties

- **type** - Token type (keyword, identifier, literal, etc.)
- **value** - Token value as string
- **line** - Line number in source
- **column** - Column number in source
- **position** - Character position in source

## Lexer Implementation

### Basic Lexer Class

```python
class YuhoLexer:
    """Yuho language lexer"""
    
    def __init__(self):
        self.tokens = []
        self.position = 0
        self.line = 1
        self.column = 1
    
    def tokenize(self, source: str) -> List[Token]:
        """Tokenize source code"""
        self.tokens = []
        self.position = 0
        self.line = 1
        self.column = 1
        
        while self.position < len(source):
            self._skip_whitespace()
            if self.position >= len(source):
                break
                
            token = self._next_token()
            if token:
                self.tokens.append(token)
        
        return self.tokens
```

### Token Recognition

```python
def _next_token(self) -> Optional[Token]:
    """Get next token from source"""
    char = self._current_char()
    
    # Keywords and identifiers
    if char.isalpha() or char == '_':
        return self._read_identifier()
    
    # String literals
    elif char == '"':
        return self._read_string()
    
    # Numeric literals
    elif char.isdigit():
        return self._read_number()
    
    # Money literals
    elif char == '$':
        return self._read_money()
    
    # Operators
    elif char in OPERATORS:
        return self._read_operator()
    
    # Punctuation
    elif char in PUNCTUATION:
        return self._read_punctuation()
    
    else:
        raise LexerError(f"Unexpected character: {char}")
```

### Identifier Recognition

```python
def _read_identifier(self) -> Token:
    """Read identifier or keyword"""
    start = self.position
    while self._current_char() and (self._current_char().isalnum() or self._current_char() == '_'):
        self._advance()
    
    value = self.source[start:self.position]
    token_type = 'KEYWORD' if value in KEYWORDS else 'IDENTIFIER'
    
    return Token(
        type=token_type,
        value=value,
        line=self.line,
        column=self.column - len(value),
        position=start
    )
```

### String Recognition

```python
def _read_string(self) -> Token:
    """Read string literal"""
    start = self.position
    self._advance()  # Skip opening quote
    
    while self._current_char() and self._current_char() != '"':
        if self._current_char() == '\\':
            self._advance()  # Skip escape character
        self._advance()
    
    if not self._current_char():
        raise LexerError("Unterminated string literal")
    
    self._advance()  # Skip closing quote
    
    value = self.source[start:self.position]
    
    return Token(
        type='STRING_LITERAL',
        value=value,
        line=self.line,
        column=self.column - len(value),
        position=start
    )
```

### Number Recognition

```python
def _read_number(self) -> Token:
    """Read numeric literal"""
    start = self.position
    
    # Read integer part
    while self._current_char() and self._current_char().isdigit():
        self._advance()
    
    # Check for decimal point
    if self._current_char() == '.':
        self._advance()
        while self._current_char() and self._current_char().isdigit():
            self._advance()
        token_type = 'FLOAT_LITERAL'
    else:
        token_type = 'INTEGER_LITERAL'
    
    value = self.source[start:self.position]
    
    return Token(
        type=token_type,
        value=value,
        line=self.line,
        column=self.column - len(value),
        position=start
    )
```

## Error Handling

### Lexer Errors

```python
class LexerError(Exception):
    """Lexer error exception"""
    
    def __init__(self, message: str, line: int = 0, column: int = 0):
        self.message = message
        self.line = line
        self.column = column
        super().__init__(f"{message} at line {line}, column {column}")
```

### Error Detection

```python
def _validate_token(self, token: Token) -> None:
    """Validate token for errors"""
    if token.type == 'STRING_LITERAL':
        if not token.value.startswith('"') or not token.value.endswith('"'):
            raise LexerError("Invalid string literal", token.line, token.column)
    
    elif token.type == 'MONEY_LITERAL':
        if not token.value.startswith('$'):
            raise LexerError("Invalid money literal", token.line, token.column)
    
    elif token.type == 'DATE_LITERAL':
        if not self._is_valid_date(token.value):
            raise LexerError("Invalid date literal", token.line, token.column)
```

## Advanced Features

### Position Tracking

```python
def _advance(self) -> None:
    """Advance to next character"""
    if self._current_char() == '\n':
        self.line += 1
        self.column = 1
    else:
        self.column += 1
    
    self.position += 1

def _current_char(self) -> Optional[str]:
    """Get current character"""
    if self.position >= len(self.source):
        return None
    return self.source[self.position]
```

### Whitespace Handling

```python
def _skip_whitespace(self) -> None:
    """Skip whitespace characters"""
    while self._current_char() and self._current_char().isspace():
        self._advance()
```

### Comment Handling

```python
def _skip_comment(self) -> None:
    """Skip comment until end of line"""
    while self._current_char() and self._current_char() != '\n':
        self._advance()
```

## Usage Examples

### Basic Tokenization

```python
from yuho_v3.lexer import YuhoLexer

# Create lexer
lexer = YuhoLexer()

# Tokenize simple code
code = "struct Person { string name, int age }"
tokens = lexer.tokenize(code)

# Print tokens
for token in tokens:
    print(f"{token.type}: {token.value}")
```

### Error Handling

```python
try:
    tokens = lexer.tokenize('struct Person { string name, int age')
except LexerError as e:
    print(f"Lexer error: {e}")
    print(f"Line: {e.line}, Column: {e.column}")
```

### Token Analysis

```python
def analyze_tokens(tokens):
    """Analyze token stream"""
    keywords = [t for t in tokens if t.type == 'KEYWORD']
    identifiers = [t for t in tokens if t.type == 'IDENTIFIER']
    literals = [t for t in tokens if t.type.endswith('_LITERAL')]
    
    print(f"Keywords: {len(keywords)}")
    print(f"Identifiers: {len(identifiers)}")
    print(f"Literals: {len(literals)}")
```

## Performance Considerations

### Token Caching

```python
class CachedLexer:
    """Lexer with token caching"""
    
    def __init__(self):
        self.cache = {}
    
    def tokenize(self, source: str) -> List[Token]:
        """Tokenize with caching"""
        if source in self.cache:
            return self.cache[source]
        
        tokens = self._tokenize_internal(source)
        self.cache[source] = tokens
        return tokens
```

### Memory Optimization

```python
class OptimizedLexer:
    """Memory-optimized lexer"""
    
    def __init__(self):
        self.tokens = []
        self.max_tokens = 10000  # Limit token count
    
    def tokenize(self, source: str) -> List[Token]:
        """Tokenize with memory limits"""
        if len(source) > self.max_tokens:
            raise LexerError("Source too large for tokenization")
        
        return self._tokenize_internal(source)
```

## Testing

### Unit Tests

```python
def test_basic_tokenization():
    """Test basic tokenization"""
    lexer = YuhoLexer()
    tokens = lexer.tokenize("struct Person { string name }")
    
    assert len(tokens) == 6
    assert tokens[0].type == 'KEYWORD'
    assert tokens[0].value == 'struct'
    assert tokens[1].type == 'IDENTIFIER'
    assert tokens[1].value == 'Person'
```

### Error Tests

```python
def test_lexer_errors():
    """Test lexer error handling"""
    lexer = YuhoLexer()
    
    with pytest.raises(LexerError):
        lexer.tokenize('struct Person { string name')  # Missing closing brace
```

### Performance Tests

```python
def test_lexer_performance():
    """Test lexer performance"""
    lexer = YuhoLexer()
    code = "struct Person { string name, int age }" * 100
    
    start_time = time.time()
    tokens = lexer.tokenize(code)
    end_time = time.time()
    
    assert (end_time - start_time) < 1.0  # Should complete in under 1 second
```

## Integration

### Parser Integration

```python
from yuho_v3.lexer import YuhoLexer
from yuho_v3.parser import YuhoParser

# Lexer and parser integration
lexer = YuhoLexer()
parser = YuhoParser()

# Tokenize and parse
tokens = lexer.tokenize(source)
ast = parser.parse_tokens(tokens)
```

### CLI Integration

```python
def lex_file(file_path: str) -> List[Token]:
    """Lex file from command line"""
    with open(file_path, 'r') as f:
        source = f.read()
    
    lexer = YuhoLexer()
    return lexer.tokenize(source)
```

## Best Practices

### Error Handling

```python
def safe_tokenize(source: str) -> List[Token]:
    """Safely tokenize source code"""
    try:
        lexer = YuhoLexer()
        return lexer.tokenize(source)
    except LexerError as e:
        print(f"Lexer error: {e}")
        return []
```

### Memory Management

```python
def tokenize_large_file(file_path: str) -> List[Token]:
    """Tokenize large file efficiently"""
    lexer = YuhoLexer()
    tokens = []
    
    with open(file_path, 'r') as f:
        for line in f:
            line_tokens = lexer.tokenize(line)
            tokens.extend(line_tokens)
    
    return tokens
```

### Performance Optimization

```python
def optimized_tokenize(source: str) -> List[Token]:
    """Optimized tokenization"""
    lexer = YuhoLexer()
    
    # Pre-allocate token list
    tokens = []
    tokens.reserve(len(source) // 10)  # Estimate token count
    
    return lexer.tokenize(source)
```

## Troubleshooting

### Common Issues

#### Issue 1: Token Recognition

```python
# Problem: Incorrect token recognition
tokens = lexer.tokenize("struct Person")
# Expected: [KEYWORD: struct, IDENTIFIER: Person]
# Actual: [IDENTIFIER: struct, IDENTIFIER: Person]
```

**Solution**: Check keyword definitions:

```python
KEYWORDS = {
    'struct', 'match', 'case', 'consequence', 'func',
    'true', 'false', 'pass', 'referencing', 'from'
}
```

#### Issue 2: Position Tracking

```python
# Problem: Incorrect position tracking
token = lexer.tokenize("struct Person")[0]
# Expected: line=1, column=1
# Actual: line=1, column=7
```

**Solution**: Fix position tracking:

```python
def _advance(self) -> None:
    """Advance to next character"""
    if self._current_char() == '\n':
        self.line += 1
        self.column = 1
    else:
        self.column += 1
    
    self.position += 1
```

#### Issue 3: Memory Usage

```python
# Problem: High memory usage
tokens = lexer.tokenize(large_source)
# Memory usage too high
```

**Solution**: Use streaming tokenization:

```python
def stream_tokenize(source: str):
    """Stream tokens instead of storing all"""
    lexer = YuhoLexer()
    for token in lexer.tokenize(source):
        yield token
```

## Next Steps

- [Parser API](parser.md) - Parsing tokens into AST
- [AST API](ast.md) - Abstract Syntax Tree nodes
- [Semantic API](semantic.md) - Semantic analysis
- [Transpilers API](transpilers.md) - Code generation
