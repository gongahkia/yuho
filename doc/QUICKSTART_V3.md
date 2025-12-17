# Yuho v4.0 Quickstart Guide

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Install Yuho v4.0

```bash
# Install dependencies
pip install -r requirements.txt

# Install Yuho v4.0 (development mode)
pip install -e .
```

### Verify Installation

```bash
yuho --version
# Should output: yuho, version 3.0.0
```

## Basic Usage

### 1. Check a Yuho File

```bash
yuho check example/cheating/cheating_illustration_A.yh
```

### 2. Generate Diagrams

```bash
# Generate flowchart
yuho draw example/cheating/s415_cheating_definition.yh --format flowchart -o cheating_flow.mmd

# Generate mindmap
yuho draw example/cheating/s415_cheating_definition.yh --format mindmap -o cheating_mind.mmd
```

### 3. Generate Alloy Specification

```bash
yuho alloy example/cheating/s415_cheating_definition.yh -o cheating.als
```

### 4. Create New Template

```bash
yuho draft Theft -o theft_definition.yh
```

### 5. Interactive REPL

```bash
yuho-repl
```

Or run the Python module directly:

```bash
python3 yuho_v4/repl.py
```

## Writing Yuho Code

### Basic Structure

```yh
// Comments use // or /* */

// Define a struct for legal concepts
struct Cheating {
    accused: string,
    action: string,
    victim: string,
    deception: bool,
    inducement: bool,
    harm: bool,
}

// Create an instance
Cheating example := {
    accused := "A",
    action := "falsely pretending to be in Government service",
    victim := "Z",
    deception := TRUE,
    inducement := TRUE,
    harm := TRUE,
}

// Use match-case for conditional logic
match {
    case (deception && inducement && harm) := consequence "guilty of cheating";
    case _ := consequence "not guilty";
}
```

### Available Types

- **Basic**: `int`, `float`, `bool`, `string`
- **Legal**: `percent`, `money`, `date`, `duration`
- **Custom**: Any struct you define

### Import System

```yh
// Import from another module
referencing Cheating from s415_cheating_definition

// Use imported struct
s415_cheating_definition.Cheating myCase := {
    // field assignments...
}
```

## CLI Commands Reference

| Command | Description | Example |
|---------|-------------|---------|
| `yuho check <file>` | Validate syntax and semantics | `yuho check contract.yh` |
| `yuho draw <file>` | Generate Mermaid diagrams | `yuho draw --format flowchart file.yh` |
| `yuho alloy <file>` | Generate Alloy specification | `yuho alloy file.yh -o spec.als` |
| `yuho draft <name>` | Create template file | `yuho draft Contract -o contract.yh` |
| `yuho how` | Show help and examples | `yuho how` |

## REPL Commands

In the interactive REPL:

| Command | Description |
|---------|-------------|
| `help` | Show REPL help |
| `history` | Show command history |
| `clear` | Clear screen |
| `load <file>` | Load and parse a file |
| `mermaid` | Generate Mermaid from last input |
| `alloy` | Generate Alloy from last input |
| `exit` | Exit REPL |

## Examples

See the `example/` directory for complete working examples:

- `example/cheating/` - Criminal law cheating offenses
- Various illustration files showing different legal scenarios

## Next Steps

1. Read the [full syntax documentation](SYNTAX.md)
2. Explore [examples](../example/)
3. Check [transpiler outputs](../test/) for verification
4. Contribute to [development](../admin/CONTRIBUTING.md)

## Troubleshooting

### Import Errors
Make sure you're in the project root directory and have installed dependencies:

```bash
pip install -r requirements.txt
```

### Grammar Errors
Check your `.yh` file syntax. Common issues:
- Missing semicolons after statements
- Incorrect struct field syntax (use `:` not `=` for type annotations)
- Mismatched braces `{}`

### File Not Found
Ensure file paths are correct and files have `.yh` extension.