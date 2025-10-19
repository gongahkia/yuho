# Check Command

The `yuho check` command validates Yuho source files for syntax and semantic correctness.

## Overview

The `check` command performs comprehensive validation of Yuho files:

- **Syntax Validation** - Ensures proper Yuho syntax
- **Semantic Analysis** - Validates types and logic
- **Error Reporting** - Provides detailed error messages
- **Quick Feedback** - Fast validation for development

## Basic Usage

```bash
yuho check <file_path>
```

### Examples

```bash
# Check a single file
yuho check example.yh

# Check with verbose output
yuho check example.yh --verbose

# Check file in subdirectory
yuho check examples/cheating/cheating_illustration_A.yh
```

## Command Options

### `--verbose`, `-v`

Show detailed output including AST structure:

```bash
yuho check example.yh --verbose
```

**Output:**
```
Checking example.yh...
✓ Syntax check passed
✓ Semantic check passed
✓ example.yh looks good! Have confidence your Yuho file is correct
AST Structure:
  Statements: 3
```

## Validation Process

### Step 1: Syntax Validation

The parser checks for:
- Valid Yuho syntax
- Proper struct definitions
- Correct match-case syntax
- Valid function definitions

**Example Error:**
```bash
$ yuho check invalid.yh
✗ Error: Syntax error at line 3: expected 'bool' but found 'boolean'
```

### Step 2: Semantic Analysis

The semantic analyzer checks for:
- Type consistency
- Variable declarations
- Function signatures
- Match-case completeness

**Example Error:**
```bash
$ yuho check invalid.yh
✓ Syntax check passed
✗ Semantic errors found:
  ERROR: Variable 'age' used before declaration
  ERROR: Type mismatch: expected 'int' but found 'string'
```

## Common Validation Errors

### Syntax Errors

#### Error 1: Invalid Type

```yh
// Invalid: 'boolean' should be 'bool'
struct Person {
    string name,
    boolean age  // Error: should be 'bool'
}
```

**Fix:**
```yh
struct Person {
    string name,
    bool age  // Correct
}
```

#### Error 2: Missing Semicolon

```yh
// Invalid: Missing semicolon
int age := 25
string name := "John"

// Fix: Add semicolons
int age := 25;
string name := "John";
```

#### Error 3: Invalid Match-Case

```yh
// Invalid: Missing default case
match {
    case condition1 := consequence result1;
    case condition2 := consequence result2;
    // Missing: case _ := consequence default;
}
```

**Fix:**
```yh
match {
    case condition1 := consequence result1;
    case condition2 := consequence result2;
    case _ := consequence default;
}
```

### Semantic Errors

#### Error 1: Type Mismatch

```yh
// Invalid: string cannot be int
int age := "25";  // Error: string cannot be int
```

**Fix:**
```yh
int age := 25;  // Correct: int value
```

#### Error 2: Undefined Variable

```yh
// Invalid: variable used before declaration
match {
    case age > 18 := consequence "adult";
    case _ := consequence "minor";
}

int age := 25;  // Error: age used before declaration
```

**Fix:**
```yh
int age := 25;

match {
    case age > 18 := consequence "adult";
    case _ := consequence "minor";
}
```

#### Error 3: Incomplete Match-Case

```yh
// Invalid: missing cases for boolean
bool isGuilty := TRUE;

match isGuilty {
    case TRUE := consequence "guilty";
    // Missing: case FALSE := consequence "not guilty";
}
```

**Fix:**
```yh
bool isGuilty := TRUE;

match isGuilty {
    case TRUE := consequence "guilty";
    case FALSE := consequence "not guilty";
}
```

## Validation Examples

### Valid File

```yh
// Section 415 - Cheating
struct Cheating {
    bool deception,
    bool dishonest,
    bool harm
}

Cheating case1 := {
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
```

**Validation Result:**
```bash
$ yuho check cheating.yh
✓ Syntax check passed
✓ Semantic check passed
✓ cheating.yh looks good! Have confidence your Yuho file is correct
```

### Invalid File

```yh
// Section 415 - Cheating
struct Cheating {
    bool deception,
    bool dishonest,
    bool harm
}

Cheating case1 := {
    deception := TRUE,
    dishonest := TRUE,
    harm := TRUE
};

match {
    case case1.deception && case1.dishonest && case1.harm :=
        consequence "guilty of cheating";
    // Missing default case
}
```

**Validation Result:**
```bash
$ yuho check cheating.yh
✓ Syntax check passed
✗ Semantic errors found:
  ERROR: Match-case must include default case
```

## Best Practices

### 1. Check Early and Often

```bash
# Check during development
yuho check example.yh

# Check before committing
yuho check *.yh
```

### 2. Use Verbose Mode for Debugging

```bash
# Get detailed information
yuho check example.yh --verbose
```

### 3. Check All Files

```bash
# Check all .yh files in directory
for file in *.yh; do
    yuho check "$file"
done
```

### 4. Integrate with Development Workflow

```bash
# Pre-commit hook
#!/bin/bash
for file in $(git diff --cached --name-only --diff-filter=ACM | grep '\.yh$'); do
    yuho check "$file" || exit 1
done
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success - file is valid |
| 1 | Syntax error |
| 2 | Semantic error |
| 3 | File not found |
| 4 | Invalid arguments |

## Troubleshooting

### Common Issues

#### Issue 1: File Not Found

```bash
$ yuho check nonexistent.yh
✗ Error: File not found: nonexistent.yh
```

**Solution**: Check file path and ensure file exists:

```bash
ls -la nonexistent.yh
yuho check ./nonexistent.yh
```

#### Issue 2: Permission Denied

```bash
$ yuho check protected.yh
✗ Error: Permission denied: protected.yh
```

**Solution**: Check file permissions:

```bash
ls -la protected.yh
chmod 644 protected.yh
yuho check protected.yh
```

#### Issue 3: Invalid File Extension

```bash
$ yuho check example.txt
✗ Error: Invalid file extension. Expected .yh file
```

**Solution**: Use correct file extension:

```bash
mv example.txt example.yh
yuho check example.yh
```

## Integration with IDEs

### VS Code

Add to `.vscode/tasks.json`:

```json
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Yuho Check",
            "type": "shell",
            "command": "yuho",
            "args": ["check", "${file}"],
            "group": "build",
            "presentation": {
                "echo": true,
                "reveal": "always",
                "focus": false,
                "panel": "shared"
            }
        }
    ]
}
```

### Vim/Neovim

Add to `.vimrc`:

```vim
" Yuho check command
command! YuhoCheck !yuho check %
```

### Emacs

Add to `.emacs`:

```elisp
(defun yuho-check ()
  "Check current Yuho file"
  (interactive)
  (shell-command (concat "yuho check " (buffer-file-name))))
```

## Performance

### Validation Speed

Typical validation times:

| File Size | Statements | Time |
|-----------|------------|------|
| Small | 1-10 | <10ms |
| Medium | 11-100 | <50ms |
| Large | 101-1000 | <500ms |
| Very Large | 1000+ | <2s |

### Optimization Tips

1. **Check individual files** during development
2. **Batch check** multiple files for CI/CD
3. **Use verbose mode** only when debugging
4. **Cache results** for repeated checks

## Next Steps

- [Draw Command](draw.md) - Generate diagrams from valid files
- [Alloy Command](alloy.md) - Generate Alloy specifications
- [Draft Command](draft.md) - Create new Yuho files
- [REPL](repl.md) - Interactive development
