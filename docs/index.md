# Welcome to Yuho

**Yuho** is a domain-specific language (DSL) dedicated to simplifying [legalese](https://www.merriam-webster.com/dictionary/legalese) by providing a programmatic representation of Singapore Law.

## What is Yuho?

Yuho helps law students and legal professionals better understand statutes by providing a flexible, programmatic syntax for representing legal concepts. Current applications focus on Singapore Criminal Law, but the principles can be applied to any jurisdiction that relies on statutes.

## Key Features

- **🎯 Domain-Specific**: Tailored specifically for legal reasoning and statute representation
- **📊 Visual Diagrams**: Transpile to Mermaid flowcharts and mindmaps
- **✅ Formal Verification**: Generate Alloy specifications for logical verification
- **🔍 Type-Safe**: Strong, static typing ensures correctness
- **🚀 CLI Tools**: Comprehensive command-line interface for all operations
- **📝 REPL**: Interactive shell for experimentation

## Why Yuho?

The law is innately complex. [Statutes](https://sso.agc.gov.sg/) are not always easy to understand, especially for incoming law students new to legalese and its logical structure.

Yuho provides:

1. **Clarity**: Make statutory logic explicit and visual
2. **Verification**: Ensure logical consistency through formal methods
3. **Education**: Help students understand legal reasoning patterns
4. **Modularity**: Reusable legal concepts and patterns

## Quick Example

```yh
// Define the legal concept of Cheating
struct Cheating {
    string accused,
    string victim,
    bool deception,
    bool dishonest,
    bool harm
}

// Define the logical requirements
match {
    case deception && dishonest && harm := consequence "guilty of cheating";
    case _ := consequence "not guilty";
}
```

This code can then be:

- ✅ **Validated** for syntax and semantic correctness
- 📊 **Visualized** as flowcharts or mindmaps
- 🔍 **Verified** using formal methods with Alloy

## Getting Started

<div class="grid cards" markdown>

-   :material-clock-fast:{ .lg .middle } **Quick Start**

    ---

    Install Yuho and write your first program in minutes

    [:octicons-arrow-right-24: Quick Start Guide](getting-started/quickstart.md)

-   :material-book-open-variant:{ .lg .middle } **Language Guide**

    ---

    Learn Yuho's syntax, types, and patterns

    [:octicons-arrow-right-24: Language Reference](language/overview.md)

-   :material-code-braces:{ .lg .middle } **Examples**

    ---

    Explore real-world legal examples

    [:octicons-arrow-right-24: See Examples](examples/criminal-law.md)

-   :material-api:{ .lg .middle } **API Reference**

    ---

    Deep dive into Yuho's internals

    [:octicons-arrow-right-24: API Documentation](api/parser.md)

</div>

## Use Cases

### For Law Students

- Understand complex statutes through code
- Visualize legal logic and dependencies
- Test understanding with formal verification

### For Legal Educators

- Create interactive learning materials
- Demonstrate logical reasoning patterns
- Build reusable teaching examples

### For Legal Tech Developers

- Programmatically represent legal knowledge
- Build decision support systems
- Integrate with existing legal tools

## Community

Yuho is open-source and welcomes contributions!

- **GitHub**: [github.com/gongahkia/yuho](https://github.com/gongahkia/yuho)
- **Issues**: [Report bugs or request features](https://github.com/gongahkia/yuho/issues)
- **Contributing**: [Learn how to contribute](development/contributing.md)

## Next Steps

- [Install Yuho](getting-started/installation.md)
- [Write your first program](getting-started/first-program.md)
- [Explore the CLI commands](cli/commands.md)
- [Learn the syntax](language/syntax.md)

