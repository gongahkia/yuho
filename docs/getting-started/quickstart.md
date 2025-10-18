# Quick Start

Get up and running with Yuho in 5 minutes!

## Installation

First, install Yuho:

```bash
pip install -e .
```

Verify installation:

```bash
yuho --version
```

## Your First Yuho Program

Create a file called `first.yh`:

```yh
// Define a simple struct
struct Person {
    string name,
    int age
}

// Create a variable
int x := 42;

// Use match-case for logic
match {
    case x > 0 := consequence TRUE;
    case _ := consequence FALSE;
}
```

## Check Your Code

Validate syntax and semantics:

```bash
yuho check first.yh
```

You should see:
```
✓ Syntax check passed
✓ Semantic check passed
✓ first.yh looks good!
```

## Generate Visualizations

Create a flowchart diagram:

```bash
yuho draw first.yh --format flowchart -o first.mmd
```

Create a mindmap:

```bash
yuho draw first.yh --format mindmap -o first_mindmap.mmd
```

## Generate Formal Specification

Create an Alloy specification for verification:

```bash
yuho alloy first.yh -o first.als
```

## Interactive REPL

Start the interactive shell:

```bash
yuho-repl
```

Try some commands:

```
yuho> struct Test { string name }
✓ Valid Yuho code

yuho> int x := 42;
✓ Valid Yuho code

yuho> help
[Shows available commands]

yuho> exit
```

## Legal Example

Let's create a real legal statute representation. Create `cheating.yh`:

```yh
// Section 415 of the Penal Code - Cheating
struct Cheating {
    string accused,
    string victim,
    string action,
    bool deception,
    bool dishonest,
    bool inducedAction,
    bool causedHarm
}

// Logical requirements for cheating offense
match {
    case deception && dishonest && inducedAction && causedHarm :=
        consequence "guilty of cheating";
    case _ :=
        consequence "not guilty";
}
```

Check it:

```bash
yuho check cheating.yh
```

Generate flowchart:

```bash
yuho draw cheating.yh --format flowchart -o cheating_flow.mmd
```

## Common CLI Commands

| Command | Purpose | Example |
|---------|---------|---------|
| `check` | Validate syntax and semantics | `yuho check file.yh` |
| `draw` | Generate Mermaid diagrams | `yuho draw file.yh -f flowchart` |
| `alloy` | Generate Alloy specification | `yuho alloy file.yh -o spec.als` |
| `draft` | Create template file | `yuho draft MyStruct -o file.yh` |
| `how` | Show usage examples | `yuho how` |

## Next Steps

Now that you've got the basics:

1. [Learn the full syntax](../language/syntax.md)
2. [Explore more examples](../examples/criminal-law.md)
3. [Understand match-case patterns](../language/match-case.md)
4. [Use the CLI effectively](../cli/commands.md)

## Troubleshooting

### Syntax Error

If you get a syntax error:

- Check that you're using `:=` for assignment (not `=`)
- Ensure all statements end with `;`
- Verify struct field syntax uses `,` between fields

### File Not Found

- Ensure you're in the correct directory
- Use absolute or relative paths correctly
- Check file has `.yh` extension

### Import Errors

If Python import errors occur:

```bash
pip install -r requirements.txt
pip install -e .
```

## Getting Help

- Use `yuho --help` for command-line help
- Use `yuho how` for usage examples
- Check [FAQ](../about/faq.md) for common questions
- Visit [GitHub Issues](https://github.com/gongahkia/yuho/issues) for support

