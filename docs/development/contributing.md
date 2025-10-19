# Contributing to Yuho

Guidelines for contributing to the Yuho project.

## Overview

Yuho is an open-source project that welcomes contributions from the community. This guide explains how to contribute effectively to the project.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- Basic understanding of legal concepts
- Familiarity with domain-specific languages

### Development Setup

1. **Fork the Repository**
   ```bash
   git clone https://github.com/your-username/yuho.git
   cd yuho
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

3. **Install in Development Mode**
   ```bash
   pip install -e .
   ```

4. **Run Tests**
   ```bash
   pytest
   ```

## Contribution Types

### Code Contributions

- **Bug Fixes** - Fix issues in the codebase
- **Feature Additions** - Add new functionality
- **Documentation** - Improve documentation
- **Tests** - Add or improve test coverage

### Legal Contributions

- **Legal Examples** - Add new legal examples
- **Legal Patterns** - Create reusable legal patterns
- **Legal Documentation** - Improve legal documentation
- **Legal Validation** - Ensure legal accuracy

### Documentation Contributions

- **User Guides** - Improve user documentation
- **API Documentation** - Document API functions
- **Tutorials** - Create learning materials
- **Examples** - Add practical examples

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

- Write code following the style guide
- Add tests for new functionality
- Update documentation as needed

### 3. Test Your Changes

```bash
# Run all tests
pytest

# Run specific tests
pytest tests/test_parser.py

# Run with coverage
pytest --cov=yuho_v3
```

### 4. Check Code Quality

```bash
# Format code
black yuho_v3/

# Check style
flake8 yuho_v3/

# Type checking
mypy yuho_v3/
```

### 5. Commit Changes

```bash
git add .
git commit -m "Add feature: brief description"
```

### 6. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

## Code Style Guide

### Python Code

- Follow PEP 8 style guide
- Use type hints for function parameters and return values
- Write docstrings for all public functions
- Use meaningful variable and function names

### Example

```python
def transpile_to_mermaid(program: Program) -> str:
    """
    Generate Mermaid diagram from Yuho program.
    
    Args:
        program: Yuho Program AST
        
    Returns:
        Mermaid diagram syntax
    """
    # Implementation
    pass
```

### Yuho Code

- Use descriptive names for structs and variables
- Include legal context in comments
- Follow the established patterns
- Ensure complete case coverage

### Example

```yh
// Section 415 - Cheating
// Whoever, by deceiving any person, fraudulently or dishonestly...
struct Cheating {
    string accused,
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
```

## Testing Guidelines

### Test Structure

- **Unit Tests** - Test individual functions
- **Integration Tests** - Test complete workflows
- **Legal Tests** - Test legal accuracy
- **Performance Tests** - Test performance characteristics

### Writing Tests

```python
def test_cheating_offense():
    """Test cheating offense validation"""
    parser = YuhoParser()
    code = """
    struct Cheating {
        bool deception,
        bool dishonest,
        bool harm
    }
    
    match {
        case deception && dishonest && harm :=
            consequence "guilty";
        case _ :=
            consequence "not guilty";
    }
    """
    
    ast = parser.parse(code)
    assert ast is not None
    assert len(ast.statements) == 2
```

### Legal Test Examples

```python
def test_legal_accuracy():
    """Test legal accuracy of examples"""
    # Test that cheating examples match Section 415
    # Test that theft examples match Section 378
    # Test that legal logic is correct
    pass
```

## Documentation Guidelines

### User Documentation

- Write for legal professionals and students
- Include legal context and sources
- Provide practical examples
- Use clear, accessible language

### API Documentation

- Document all public functions
- Include parameter and return type information
- Provide usage examples
- Explain legal implications

### Example Documentation

```markdown
# Cheating Offense

## Legal Source

Section 415 of the Penal Code defines cheating as...

## Yuho Representation

```yh
struct Cheating {
    bool deception,
    bool dishonest,
    bool harm
}
```

## Usage

```bash
yuho check cheating.yh
yuho draw cheating.yh -f flowchart -o cheating.mmd
```
```

## Legal Contribution Guidelines

### Legal Accuracy

- Ensure all legal examples are accurate
- Include proper legal citations
- Verify legal logic is correct
- Test with legal professionals

### Legal Examples

- Use real legal cases when possible
- Include proper legal context
- Explain legal reasoning
- Provide legal sources

### Legal Validation

- Test legal examples for accuracy
- Verify legal logic is sound
- Ensure legal completeness
- Check legal consistency

## Pull Request Process

### Before Submitting

1. **Run Tests** - Ensure all tests pass
2. **Check Style** - Follow code style guidelines
3. **Update Documentation** - Update relevant documentation
4. **Test Legal Examples** - Verify legal accuracy

### Pull Request Template

```markdown
## Description

Brief description of changes

## Type of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Legal example addition
- [ ] Other (please describe)

## Legal Impact

- [ ] No legal impact
- [ ] Legal example added
- [ ] Legal logic changed
- [ ] Legal documentation updated

## Testing

- [ ] Tests pass
- [ ] Legal examples validated
- [ ] Documentation updated
- [ ] Style guidelines followed

## Checklist

- [ ] Code follows style guidelines
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Legal accuracy verified
- [ ] Ready for review
```

## Review Process

### Code Review

- Review code quality and style
- Check test coverage
- Verify functionality
- Ensure legal accuracy

### Legal Review

- Verify legal examples are accurate
- Check legal logic is sound
- Ensure legal completeness
- Validate legal sources

### Documentation Review

- Check documentation clarity
- Verify examples work
- Ensure completeness
- Validate legal context

## Issue Reporting

### Bug Reports

When reporting bugs, include:

- **Description** - Clear description of the issue
- **Steps to Reproduce** - How to reproduce the bug
- **Expected Behavior** - What should happen
- **Actual Behavior** - What actually happens
- **Environment** - Python version, OS, etc.

### Feature Requests

When requesting features, include:

- **Description** - Clear description of the feature
- **Use Case** - Why this feature is needed
- **Legal Context** - How it relates to legal reasoning
- **Implementation Ideas** - Suggestions for implementation

### Legal Issues

When reporting legal issues, include:

- **Legal Source** - Relevant legal text
- **Current Implementation** - How it's currently implemented
- **Legal Problem** - What's legally incorrect
- **Suggested Fix** - How to fix the legal issue

## Community Guidelines

### Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow
- Maintain professional standards

### Communication

- Use clear, professional language
- Provide constructive feedback
- Ask questions when needed
- Share knowledge and experience

### Legal Discussion

- Respect legal expertise
- Provide legal sources
- Engage in constructive legal debate
- Maintain legal accuracy

## Development Tools

### IDE Setup

- **VS Code** - Recommended editor
- **Python Extension** - For Python development
- **Markdown Extension** - For documentation
- **Git Extension** - For version control

### Useful Commands

```bash
# Development setup
pip install -e .

# Run tests
pytest

# Format code
black yuho_v3/

# Check style
flake8 yuho_v3/

# Type checking
mypy yuho_v3/

# Generate documentation
mkdocs serve
```

## Getting Help

### Documentation

- Check the documentation first
- Look for existing examples
- Review the language guide
- Check the API reference

### Community

- Ask questions on GitHub Issues
- Join discussions on GitHub Discussions
- Connect with other contributors
- Share your experience

### Legal Questions

- Consult legal professionals
- Review legal sources
- Check legal accuracy
- Validate legal logic

## Recognition

### Contributors

- All contributors are recognized
- Legal contributors are especially valued
- Documentation contributors are appreciated
- Code contributors are essential

### Legal Contributors

- Legal accuracy is crucial
- Legal examples are valuable
- Legal documentation is important
- Legal validation is essential

## Next Steps

- [Testing Guide](testing.md) - How to test Yuho
- [Docker Guide](docker.md) - Container development
- [Architecture Guide](architecture.md) - Understanding Yuho's architecture
- [API Reference](../api/parser.md) - Complete API documentation
