# CLI Commands Reference

Complete reference for all Yuho command-line interface commands.

## Overview

Yuho provides a comprehensive CLI for all operations:

```bash
yuho [COMMAND] [OPTIONS] [ARGUMENTS]
```

## Commands

### `yuho check`

Validate Yuho source files for syntax and semantic correctness.

**Usage:**
```bash
yuho check <file_path> [OPTIONS]
```

**Arguments:**
- `file_path` - Path to the `.yh` file to check (required)

**Options:**
- `--verbose`, `-v` - Show detailed output including AST structure

**Examples:**
```bash
# Basic syntax check
yuho check example.yh

# Check with verbose output
yuho check example.yh --verbose

# Check file in subdirectory
yuho check example/cheating/cheating_illustration_A.yh
```

**Output:**
- ✓ Success: Shows syntax and semantic validation passed
- ✗ Error: Shows detailed error messages with suggestions

---

### `yuho draw`

Generate Mermaid diagrams from Yuho source files.

**Usage:**
```bash
yuho draw <file_path> [OPTIONS]
```

**Arguments:**
- `file_path` - Path to the `.yh` file (required)

**Options:**
- `--output`, `-o` - Output file path (default: stdout)
- `--format`, `-f` - Diagram format: `flowchart` or `mindmap` (default: `flowchart`)

**Examples:**
```bash
# Generate flowchart to stdout
yuho draw example.yh

# Generate flowchart to file
yuho draw example.yh --format flowchart -o diagram.mmd

# Generate mindmap
yuho draw example.yh --format mindmap -o mindmap.mmd

# Short form
yuho draw example.yh -f flowchart -o output.mmd
```

**Output Formats:**

**Flowchart** - Shows control flow and logic:
```bash
yuho draw cheating.yh -f flowchart -o cheating_flow.mmd
```

**Mindmap** - Shows hierarchical structure:
```bash
yuho draw cheating.yh -f mindmap -o cheating_mind.mmd
```

---

### `yuho alloy`

Generate Alloy specifications for formal verification.

**Usage:**
```bash
yuho alloy <file_path> [OPTIONS]
```

**Arguments:**
- `file_path` - Path to the `.yh` file (required)

**Options:**
- `--output`, `-o` - Output file path (default: stdout)

**Examples:**
```bash
# Generate Alloy spec to stdout
yuho alloy example.yh

# Save to file
yuho alloy example.yh -o specification.als

# Generate from legal example
yuho alloy example/cheating/s415_cheating_definition.yh -o cheating.als
```

**Output:**
Generates an Alloy specification including:
- Signatures from struct definitions
- Predicates from match-case logic
- Facts from constraints
- Run commands for verification

---

### `yuho draft`

Create a new Yuho file template with basic structure.

**Usage:**
```bash
yuho draft <struct_name> [OPTIONS]
```

**Arguments:**
- `struct_name` - Name of the main struct (required)

**Options:**
- `--output`, `-o` - Output file path (default: `<struct_name>.yh`)

**Examples:**
```bash
# Create template with default filename
yuho draft Theft
# Creates: theft.yh

# Create with custom filename
yuho draft Contract -o my_contract.yh

# Create for legal concept
yuho draft CriminalBreach -o criminal_breach.yh
```

**Generated Template:**
```yh
// Yuho v3.0 - Generated template for StructName

struct StructName {
    // Add your fields here
    // Example:
    // accused: string,
    // action: string,
    // victim: string,
    // consequence: ConsequenceType,
}

// Add match-case logic here
// Example:
// match {
//     case condition := consequence result;
//     case _ := consequence pass;
// }
```

---

### `yuho how`

Display help and usage examples.

**Usage:**
```bash
yuho how
```

**Output:**
Shows comprehensive help including:
- Common usage examples
- File structure guidelines
- Available types
- Links to documentation

**Example:**
```bash
yuho how
```

---

### `yuho-repl`

Start the interactive Yuho REPL (Read-Eval-Print Loop).

**Usage:**
```bash
yuho-repl
```

**REPL Commands:**

| Command | Description |
|---------|-------------|
| `help` | Show REPL help |
| `history` | Show command history |
| `clear` | Clear screen |
| `load <file>` | Load and parse a file |
| `mermaid` | Generate Mermaid from last input |
| `alloy` | Generate Alloy from last input |
| `exit`, `quit` | Exit REPL |

**Examples:**
```bash
# Start REPL
yuho-repl

# In REPL:
yuho> struct Person { string name, int age }
✓ Valid Yuho code

yuho> int x := 42;
✓ Valid Yuho code

yuho> load example.yh
✓ Successfully loaded example.yh

yuho> mermaid
[Shows Mermaid diagram]

yuho> help
[Shows REPL commands]

yuho> exit
```

---

### `yuho --version`

Display Yuho version information.

**Usage:**
```bash
yuho --version
```

**Output:**
```
yuho, version 3.0.0
```

---

### `yuho --help`

Display help information for all commands.

**Usage:**
```bash
yuho --help

# Or for specific command
yuho check --help
yuho draw --help
yuho alloy --help
```

---

## Common Workflows

### Workflow 1: Check and Visualize

```bash
# 1. Check file is valid
yuho check offense.yh

# 2. Generate flowchart
yuho draw offense.yh -f flowchart -o offense_flow.mmd

# 3. Generate mindmap
yuho draw offense.yh -f mindmap -o offense_mind.mmd

# 4. Generate Alloy spec for verification
yuho alloy offense.yh -o offense.als
```

### Workflow 2: Create New Statute

```bash
# 1. Create template
yuho draft Theft -o theft.yh

# 2. Edit the file (add fields and logic)
vim theft.yh

# 3. Check for errors
yuho check theft.yh

# 4. Generate diagrams
yuho draw theft.yh -f flowchart -o theft_diagram.mmd
```

### Workflow 3: Interactive Development

```bash
# 1. Start REPL
yuho-repl

# 2. Try out syntax interactively
yuho> struct Test { string field }

# 3. Load a file to test
yuho> load example.yh

# 4. Generate output
yuho> mermaid
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Syntax error |
| 2 | Semantic error |
| 3 | File not found |
| 4 | Invalid arguments |

---

## Environment Variables

Currently, Yuho does not use environment variables, but future versions may support:

- `YUHO_CONFIG` - Path to configuration file
- `YUHO_LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)

---

## Tips and Tricks

### Batch Processing

```bash
# Check all files in a directory
for file in example/cheating/*.yh; do
    yuho check "$file"
done

# Generate diagrams for all files
for file in *.yh; do
    yuho draw "$file" -f flowchart -o "${file%.yh}.mmd"
done
```

### Piping Output

```bash
# Check and save results
yuho check example.yh > check_results.txt 2>&1

# Generate and view immediately
yuho draw example.yh | less
```

### Using with Git Hooks

```bash
# Pre-commit hook to check all .yh files
#!/bin/bash
for file in $(git diff --cached --name-only --diff-filter=ACM | grep '\.yh$'); do
    yuho check "$file" || exit 1
done
```

---

## Troubleshooting

### Command Not Found

```bash
# Ensure Yuho is installed
pip install -e .

# Check installation
which yuho
yuho --version
```

### File Not Found Errors

```bash
# Use absolute paths
yuho check /full/path/to/file.yh

# Or navigate to directory
cd /path/to/files
yuho check file.yh
```

### Import Errors

```bash
# Ensure dependencies are installed
pip install -r requirements.txt

# Reinstall Yuho
pip install -e . --force-reinstall
```

---

## See Also

- [REPL Guide](repl.md)
- [Quick Start](../getting-started/quickstart.md)
- [Examples](../examples/criminal-law.md)
- [Language Syntax](../language/syntax.md)

