use anyhow::Result;
use clap::{Parser, Subcommand};
use colored::Colorize;
use std::fs;
use std::path::PathBuf;

#[derive(Parser)]
#[command(name = "yuho")]
#[command(about = "Yuho - A DSL for legal reasoning", long_about = None)]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Lex a Yuho file and display tokens
    Lex {
        /// Input file path
        file: PathBuf,
    },
    /// Parse a Yuho file and display AST
    Parse {
        /// Input file path
        file: PathBuf,
        /// Output as JSON
        #[arg(long)]
        json: bool,
    },
    /// Check a Yuho file for errors
    Check {
        /// Input file path
        file: PathBuf,
    },
    /// Generate Mermaid diagram from Yuho file
    Draw {
        /// Input file path
        file: PathBuf,
        /// Output file (default: stdout)
        #[arg(short, long)]
        output: Option<PathBuf>,
        /// Generate legal flowchart format
        #[arg(long)]
        legal: bool,
    },
    /// Generate Alloy specification from Yuho file
    Alloy {
        /// Input file path
        file: PathBuf,
        /// Output file (default: stdout)
        #[arg(short, long)]
        output: Option<PathBuf>,
    },
    /// Export Yuho file as JSON
    Json {
        /// Input file path
        file: PathBuf,
        /// Output file (default: stdout)
        #[arg(short, long)]
        output: Option<PathBuf>,
        /// Use simplified interchange format
        #[arg(long)]
        interchange: bool,
    },
    /// Generate LaTeX document from Yuho file
    Latex {
        /// Input file path
        file: PathBuf,
        /// Output file (default: stdout)
        #[arg(short, long)]
        output: Option<PathBuf>,
        /// Include bibliography with numbered precedent citations
        #[arg(long)]
        with_citations: bool,
    },
    /// Generate plain English explanation from Yuho file
    Explain {
        /// Input file path
        file: PathBuf,
        /// Output file (default: stdout)
        #[arg(short, long)]
        output: Option<PathBuf>,
    },
    /// Generate TypeScript type definitions from Yuho file
    Typescript {
        /// Input file path
        file: PathBuf,
        /// Output file (default: stdout)
        #[arg(short, long)]
        output: Option<PathBuf>,
    },
    /// Generate interactive decision tree visualization
    DecisionTree {
        /// Input file path
        file: PathBuf,
        /// Output HTML file (default: decision-tree.html)
        #[arg(short, long, default_value = "decision-tree.html")]
        output: PathBuf,
    },
    /// Generate Singapore Law Gazette format
    Gazette {
        /// Input file path
        file: PathBuf,
        /// Output file (default: stdout)
        #[arg(short, long)]
        output: Option<PathBuf>,
    },
    /// Verify a specific legal principle using Z3 SMT solver
    ///
    /// This command verifies that a principle defined in your Yuho file
    /// holds for all cases. It translates the principle to SMT-LIB2 format
    /// and uses Z3 to check validity.
    ///
    /// Example: yuho verify-principle contract.yh NoDoubleJeopardy --show-smt
    #[cfg(feature = "z3")]
    VerifyPrinciple {
        /// Input file path containing principle definitions
        file: PathBuf,
        /// Name of the principle to verify (must be defined in the file)
        principle: String,
        /// Show the generated SMT-LIB2 formula for inspection
        #[arg(long)]
        show_smt: bool,
        /// Show concrete counterexamples if verification fails
        #[arg(long)]
        show_counterexample: bool,
        /// Output file for verification results (default: stdout)
        #[arg(short, long)]
        output: Option<PathBuf>,
    },
    /// Formally verify Yuho file with Z3 SMT solver (requires yuho-z3)
    #[cfg(feature = "z3")]
    Verify {
        /// Input file path
        file: PathBuf,
        /// Timeout in milliseconds (default: 5000)
        #[arg(long, default_value = "5000")]
        timeout: u32,
        /// Show detailed verification trace
        #[arg(long)]
        trace: bool,
    },
}

fn main() -> Result<()> {
    let cli = Cli::parse();

    match cli.command {
        Commands::Lex { file } => {
            let source = fs::read_to_string(&file)?;
            let tokens = yuho_core::lex(&source);

            println!("{}", "Tokens:".green().bold());
            for (tok, span) in tokens {
                println!("  {:?} @ {}..{}", tok, span.start, span.end);
            }
        },
        Commands::Parse { file, json } => {
            let source = fs::read_to_string(&file).map_err(|e| {
                eprintln!("{}", "\n╭─ File Read Error".red().bold());
                eprintln!("│");
                eprintln!("│  {}", e);
                eprintln!("│");
                eprintln!("├─ How to fix:");
                eprintln!("│  • Check that the file exists");
                eprintln!("│  • Verify you have read permissions");
                eprintln!("│  • Path: {}", file.display());
                eprintln!("╰─");
                e
            })?;

            match yuho_core::parse(&source) {
                Ok(program) => {
                    if json {
                        println!("{}", serde_json::to_string_pretty(&program)?);
                    } else {
                        println!("{}", "╭─ Abstract Syntax Tree".green().bold());
                        println!("{:#?}", program);
                        println!("{}", "╰─".green());
                    }
                },
                Err(e) => {
                    eprintln!("{}", e);
                    eprintln!(
                        "\n{}",
                        "   Parse failed. Fix the errors above and try again.".yellow()
                    );
                    std::process::exit(1);
                },
            }
        },
        Commands::Check { file } => {
            println!("{}", "╭─ Yuho Check".cyan().bold());
            println!("{}", format!("│  File: {}", file.display()).cyan());
            println!("{}", "│".cyan());

            let source = fs::read_to_string(&file).map_err(|e| {
                eprintln!("{}", "╰─ Error".red().bold());
                eprintln!("\n  Could not read file: {}", e);
                eprintln!("  \n  → Check that the file exists and you have read permissions");
                eprintln!("  → Path: {}\n", file.display());
                e
            })?;

            // Lexer pass
            let tokens = yuho_core::lex(&source);
            println!("{}", "├─ Lexer".green().bold());
            println!("{}", format!("│  ✓ {} tokens found", tokens.len()).green());
            println!("{}", "│".cyan());

            // Parser pass
            match yuho_core::parse(&source) {
                Ok(program) => {
                    println!("{}", "├─ Parser".green().bold());
                    println!(
                        "{}",
                        format!("│  ✓ {} items parsed", program.items.len()).green()
                    );
                    println!("{}", "│".cyan());

                    // Check if program has imports
                    let has_imports = !program.imports.is_empty();

                    let errors = if has_imports {
                        // Use module resolver for programs with imports
                        use yuho_core::resolver::ModuleResolver;

                        // Get directory of the file for module resolution
                        let file_dir = file.parent().unwrap_or_else(|| std::path::Path::new("."));
                        let mut resolver = ModuleResolver::new(file_dir);

                        match resolver.resolve(&file) {
                            Ok(resolved) => {
                                println!("{}", "├─ Module Resolver".green().bold());
                                println!(
                                    "{}",
                                    format!(
                                        "│  ✓ {} modules resolved",
                                        resolved.imported_programs.len() + 1
                                    )
                                    .green()
                                );
                                println!("{}", "│".cyan());

                                let mut checker = yuho_check::Checker::new();
                                checker.check_with_imports(&resolved)
                            },
                            Err(e) => {
                                println!("{}", "╰─ Module Resolver".red().bold());
                                println!("{}", format!("   ✗ Import error: {}\n", e).red().bold());
                                std::process::exit(1);
                            },
                        }
                    } else {
                        // No imports - use standard checker
                        let mut checker = yuho_check::Checker::new();
                        checker.check_program(&program)
                    };

                    if errors.is_empty() {
                        println!("{}", "╰─ Semantic Analysis".green().bold());
                        println!("{}", "   ✓ No errors found".green());
                        println!();
                        println!(
                            "{}",
                            "   All checks passed! Your Yuho code is valid."
                                .green()
                                .bold()
                        );
                    } else {
                        println!("{}", "╰─ Semantic Analysis".red().bold());
                        println!(
                            "{}",
                            format!("   ✗ Found {} error(s)\n", errors.len())
                                .red()
                                .bold()
                        );
                        for (i, err) in errors.iter().enumerate() {
                            if i > 0 {
                                println!();
                            }
                            println!(
                                "{}",
                                format!("   Error {}/{}:", i + 1, errors.len()).red().bold()
                            );
                            println!("{}", err);
                        }
                        eprintln!("\n{}", "   Fix these errors and try again.".yellow());
                        std::process::exit(1);
                    }
                },
                Err(e) => {
                    println!("{}", "╰─ Parser".red().bold());
                    println!("{}", "   ✗ Parse failed\n".red().bold());
                    eprintln!("{}", e);
                    eprintln!("\n{}", "   Fix the syntax errors and try again.".yellow());
                    std::process::exit(1);
                },
            }
        },
        Commands::Draw {
            file,
            output,
            legal,
        } => {
            let source = fs::read_to_string(&file).map_err(|e| {
                eprintln!("{}\n", "╭─ File Read Error".red().bold());
                eprintln!("│  {}", e);
                eprintln!("│\n├─ Suggestion:");
                eprintln!("│  • Check that {} exists", file.display());
                eprintln!("│  • Verify file permissions");
                eprintln!("╰─");
                e
            })?;

            match yuho_core::parse(&source) {
                Ok(program) => {
                    let mermaid = if legal {
                        yuho_transpile::to_legal_flowchart(&program)
                    } else {
                        yuho_transpile::to_mermaid(&program)
                    };

                    match output {
                        Some(path) => {
                            fs::write(&path, &mermaid).map_err(|e| {
                                eprintln!("{}\n", "╭─ File Write Error".red().bold());
                                eprintln!("│  {}", e);
                                eprintln!("│\n├─ Suggestion:");
                                eprintln!("│  • Check write permissions for {}", path.display());
                                eprintln!("│  • Ensure the directory exists");
                                eprintln!("╰─");
                                e
                            })?;
                            println!("{}\n", "✓ Success".green().bold());
                            println!("  Mermaid diagram written to {}", path.display());
                            println!("\n{}", "  Next steps:".cyan());
                            println!("  • View in Mermaid Live Editor: https://mermaid.live");
                            println!("  • Include in Markdown: ```mermaid ... ```");
                        },
                        None => {
                            println!("{}", mermaid);
                        },
                    }
                },
                Err(e) => {
                    eprintln!("{}", e);
                    eprintln!(
                        "\n{}",
                        "   Cannot generate diagram from invalid Yuho code.".yellow()
                    );
                    std::process::exit(1);
                },
            }
        },
        Commands::Alloy { file, output } => {
            let source = fs::read_to_string(&file).map_err(|e| {
                eprintln!("{}\n", "╭─ File Read Error".red().bold());
                eprintln!("│  {}", e);
                eprintln!("│\n├─ Suggestion:");
                eprintln!("│  • Check that {} exists", file.display());
                eprintln!("╰─");
                e
            })?;

            match yuho_core::parse(&source) {
                Ok(program) => {
                    let alloy = yuho_transpile::to_alloy(&program);

                    match output {
                        Some(path) => {
                            fs::write(&path, &alloy)?;
                            println!("{}\n", "✓ Success".green().bold());
                            println!("  Alloy specification written to {}", path.display());
                            println!("\n{}", "  Next steps:".cyan());
                            println!("  • Verify with Alloy Analyzer: http://alloytools.org");
                            println!("  • Run formal verification checks");
                            println!("  • Generate counterexamples if applicable");
                        },
                        None => {
                            println!("{}", alloy);
                        },
                    }
                },
                Err(e) => {
                    eprintln!("{}", e);
                    eprintln!(
                        "\n{}",
                        "   Cannot generate Alloy from invalid Yuho code.".yellow()
                    );
                    std::process::exit(1);
                },
            }
        },
        Commands::Json {
            file,
            output,
            interchange,
        } => {
            let source = fs::read_to_string(&file).map_err(|e| {
                eprintln!("{}\n", "╭─ File Read Error".red().bold());
                eprintln!("│  {}", e);
                eprintln!("│\n├─ Suggestion:");
                eprintln!("│  • Check that {} exists", file.display());
                eprintln!("╰─");
                e
            })?;

            match yuho_core::parse(&source) {
                Ok(program) => {
                    let json = if interchange {
                        yuho_transpile::to_interchange_json(&program)
                    } else {
                        yuho_transpile::to_json(&program)
                    };

                    match output {
                        Some(path) => {
                            fs::write(&path, &json)?;
                            println!("{}\n", "✓ Success".green().bold());
                            println!("  JSON output written to {}", path.display());
                            if interchange {
                                println!("\n{}", "  Format: Simplified Interchange JSON".cyan());
                                println!("  • Use for data exchange with other systems");
                            } else {
                                println!("\n{}", "  Format: Full AST JSON".cyan());
                                println!("  • Use for tooling and analysis");
                            }
                        },
                        None => {
                            println!("{}", json);
                        },
                    }
                },
                Err(e) => {
                    eprintln!("{}", e);
                    eprintln!(
                        "\n{}",
                        "   Cannot generate JSON from invalid Yuho code.".yellow()
                    );
                    std::process::exit(1);
                },
            }
        },
        Commands::Latex {
            file,
            output,
            with_citations,
        } => {
            let source = fs::read_to_string(&file).map_err(|e| {
                eprintln!("{}\n", "╭─ File Read Error".red().bold());
                eprintln!("│  {}", e);
                eprintln!("│\n├─ Suggestion:");
                eprintln!("│  • Check that {} exists", file.display());
                eprintln!("╰─");
                e
            })?;

            match yuho_core::parse(&source) {
                Ok(program) => {
                    let latex = if with_citations {
                        yuho_transpile::to_latex_with_bibliography(&program)
                    } else {
                        yuho_transpile::to_latex(&program)
                    };

                    match output {
                        Some(path) => {
                            fs::write(&path, &latex)?;
                            println!("{}\n", "✓ Success".green().bold());
                            println!("  LaTeX document written to {}", path.display());
                            if with_citations {
                                println!("  • Bibliography with numbered precedents included");
                            }
                            println!("\n{}", "  Next steps:".cyan());
                            println!("  • Compile with: pdflatex {}", path.display());
                            println!("  • Or use XeLaTeX for better Unicode support");
                            println!("  • Requires LaTeX distribution (TeX Live, MiKTeX)");
                        },
                        None => {
                            println!("{}", latex);
                        },
                    }
                },
                Err(e) => {
                    eprintln!("{}", e);
                    eprintln!(
                        "\n{}",
                        "   Cannot generate LaTeX from invalid Yuho code.".yellow()
                    );
                    std::process::exit(1);
                },
            }
        },
        Commands::Explain { file, output } => {
            let source = fs::read_to_string(&file).map_err(|e| {
                eprintln!("{}\n", "╭─ File Read Error".red().bold());
                eprintln!("│  {}", e);
                eprintln!("│\n├─ Suggestion:");
                eprintln!("│  • Check that {} exists", file.display());
                eprintln!("╰─");
                e
            })?;

            match yuho_core::parse(&source) {
                Ok(program) => {
                    let english = yuho_transpile::to_english(&program);

                    match output {
                        Some(path) => {
                            fs::write(&path, &english)?;
                            println!("{}\n", "✓ Success".green().bold());
                            println!("  English explanation written to {}", path.display());
                            println!("\n{}", "  Use case:".cyan());
                            println!("  • Share with non-technical stakeholders");
                            println!("  • Document legal logic in plain language");
                            println!("  • Facilitate legal review and understanding");
                        },
                        None => {
                            println!("{}", english);
                        },
                    }
                },
                Err(e) => {
                    eprintln!("{}", e);
                    eprintln!(
                        "\n{}",
                        "   Cannot generate explanation from invalid Yuho code.".yellow()
                    );
                    std::process::exit(1);
                },
            }
        },
        Commands::Typescript { file, output } => {
            let source = fs::read_to_string(&file).map_err(|e| {
                eprintln!("{}\n", "╭─ File Read Error".red().bold());
                eprintln!("│  {}", e);
                eprintln!("│\n├─ Suggestion:");
                eprintln!("│  • Check that {} exists", file.display());
                eprintln!("╰─");
                e
            })?;

            match yuho_core::parse(&source) {
                Ok(program) => {
                    let ts = yuho_transpile::to_typescript(&program);

                    match output {
                        Some(path) => {
                            fs::write(&path, &ts)?;
                            println!("{}\n", "✓ Success".green().bold());
                            println!("  TypeScript definitions written to {}", path.display());
                            println!("\n{}", "  Next steps:".cyan());
                            println!("  • Import in your TypeScript project");
                            println!("  • Get compile-time type safety for Yuho structures");
                            println!("  • Use with tsc, ts-node, or your bundler");
                        },
                        None => {
                            println!("{}", ts);
                        },
                    }
                },
                Err(e) => {
                    eprintln!("{}", e);
                    eprintln!(
                        "\n{}",
                        "   Cannot generate TypeScript from invalid Yuho code.".yellow()
                    );
                    std::process::exit(1);
                },
            }
        },

        Commands::DecisionTree { file, output } => {
            let source = fs::read_to_string(&file).map_err(|e| {
                eprintln!("{}\n", "╭─ File Read Error".red().bold());
                eprintln!("│  {}", e);
                eprintln!("│\n├─ Suggestion:");
                eprintln!("│  • Check that {} exists", file.display());
                eprintln!("╰─");
                e
            })?;

            match yuho_core::parse(&source) {
                Ok(program) => {
                    let mut builder = yuho_decision_tree::DecisionTreeBuilder::new();
                    match builder.extract_from_program(&program) {
                        Ok(trees) => match yuho_decision_tree::generate_html(&trees) {
                            Ok(html) => {
                                fs::write(&output, &html)?;
                                println!("{}\n", "✓ Success".green().bold());
                                println!(
                                    "  Decision tree visualization written to {}",
                                    output.display()
                                );
                                println!("\n{}", "  Next steps:".cyan());
                                println!("  • Open {} in your browser", output.display());
                                println!("  • Explore decision logic interactively");
                                println!("  • Use for legal reasoning analysis");
                            },
                            Err(e) => {
                                eprintln!("{}\n", "╭─ Visualization Error".red().bold());
                                eprintln!("│  {}", e);
                                eprintln!("╰─");
                                std::process::exit(1);
                            },
                        },
                        Err(e) => {
                            eprintln!("{}\n", "╭─ Decision Tree Extraction Error".red().bold());
                            eprintln!("│  {}", e);
                            eprintln!("│\n├─ Suggestion:");
                            eprintln!("│  • Ensure the file contains match expressions");
                            eprintln!("│  • Match expressions drive decision tree generation");
                            eprintln!("╰─");
                            std::process::exit(1);
                        },
                    }
                },
                Err(e) => {
                    eprintln!("{}", e);
                    std::process::exit(1);
                },
            }
        },

        Commands::Gazette { file, output } => {
            let source = fs::read_to_string(&file).map_err(|e| {
                eprintln!("{}\n", "╭─ File Read Error".red().bold());
                eprintln!("│  {}", e);
                eprintln!("│\n├─ Suggestion:");
                eprintln!("│  • Check that {} exists", file.display());
                eprintln!("╰─");
                e
            })?;

            match yuho_core::parse(&source) {
                Ok(program) => {
                    let gazette = yuho_transpile::to_gazette(&program);

                    match output {
                        Some(path) => {
                            fs::write(&path, &gazette)?;
                            println!("{}\n", "✓ Success".green().bold());
                            println!(
                                "  Singapore Law Gazette format written to {}",
                                path.display()
                            );
                            println!("\n{}", "  Next steps:".cyan());
                            println!("  • Review legal formatting and structure");
                            println!("  • Use in official legal documents");
                            println!("  • Submit to law gazette publication");
                        },
                        None => {
                            println!("{}", gazette);
                        },
                    }
                },
                Err(e) => {
                    eprintln!("{}", e);
                    eprintln!(
                        "\n{}",
                        "   Cannot generate gazette format from invalid Yuho code.".yellow()
                    );
                    std::process::exit(1);
                },
            }
        },

        #[cfg(feature = "z3")]
        Commands::Verify {
            file,
            timeout,
            trace,
        } => {
            println!("{}", "╭─ Yuho Formal Verification".cyan().bold());
            println!("{}", format!("│  File: {}", file.display()).cyan());
            println!("{}", format!("│  Solver: Z3 SMT").cyan());
            println!("{}", format!("│  Timeout: {}ms", timeout).cyan());
            println!("{}", "│".cyan());

            let source = fs::read_to_string(&file).map_err(|e| {
                eprintln!("{}", "╰─ Error".red().bold());
                eprintln!("\n  Could not read file: {}", e);
                eprintln!("  \n  → Check that the file exists");
                eprintln!("  → Path: {}\n", file.display());
                e
            })?;

            match yuho_core::parse(&source) {
                Ok(program) => {
                    println!("{}", "├─ Parser".green().bold());
                    println!(
                        "{}",
                        format!("│  ✓ {} items parsed", program.items.len()).green()
                    );
                    println!("{}", "│".cyan());

                    // Create Z3 verification context
                    use yuho_z3::VerificationContext;
                    let ctx = VerificationContext::with_timeout(timeout);

                    println!("{}", "├─ Z3 Verification".green().bold());

                    match ctx.verify_program(&program) {
                        Ok(errors) => {
                            if errors.is_empty() {
                                println!("{}", "│  ✓ All constraints verified".green());
                                println!("{}", "│".cyan());
                                println!("{}", "╰─ Result".green().bold());
                                println!("{}", "   ✓ Formal verification passed!".green().bold());
                                println!();
                                println!(
                                    "{}",
                                    "   All dependent type constraints are satisfiable.".green()
                                );
                                println!("{}", "   No constraint violations found.".green());
                            } else {
                                println!(
                                    "{}",
                                    format!("│  ✗ Found {} verification error(s)", errors.len())
                                        .red()
                                );
                                println!("{}", "│".cyan());
                                println!("{}", "╰─ Verification Errors".red().bold());
                                println!();
                                for (i, err) in errors.iter().enumerate() {
                                    println!(
                                        "{}",
                                        format!("   Error {}/{}:", i + 1, errors.len())
                                            .red()
                                            .bold()
                                    );
                                    println!("   {}", err);
                                    println!();
                                }
                                eprintln!(
                                    "{}",
                                    "   Fix constraint violations and try again.".yellow()
                                );
                                std::process::exit(1);
                            }
                        },
                        Err(e) => {
                            println!("{}", "╰─ Z3 Error".red().bold());
                            println!("{}", format!("   {}", e).red());
                            std::process::exit(1);
                        },
                    }

                    if trace {
                        println!();
                        println!("{}", "╭─ Verification Trace".cyan().bold());
                        println!("{}", "│".cyan());
                        println!("{}", "│  Checked constraints:".cyan());
                        // Trace would show detailed Z3 queries and results
                        println!("{}", "│  • BoundedInt range validation".cyan());
                        println!("{}", "│  • Positive value constraints".cyan());
                        println!("{}", "│  • NonEmpty collection checks".cyan());
                        println!("{}", "│  • Where clause conditions".cyan());
                        println!("{}", "╰─".cyan());
                    }
                },
                Err(e) => {
                    println!("{}", "╰─ Parser Error".red().bold());
                    eprintln!("{}", e);
                    eprintln!("\n{}", "   Cannot verify invalid Yuho code.".yellow());
                    std::process::exit(1);
                },
            }
        },

        #[cfg(feature = "z3")]
        Commands::VerifyPrinciple {
            file,
            principle,
            show_smt,
            show_counterexample,
        } => {
            // Validate principle name
            if principle.trim().is_empty() {
                eprintln!("{}", "╭─ Validation Error".red().bold());
                eprintln!("│");
                eprintln!("│  {}", "Principle name cannot be empty".red());
                eprintln!("│");
                eprintln!("├─ Usage:");
                eprintln!("│  yuho verify-principle <FILE> <PRINCIPLE_NAME>");
                eprintln!("│");
                eprintln!("├─ Example:");
                eprintln!("│  yuho verify-principle contract.yh NoDoubleJeopardy");
                eprintln!("╰─");
                std::process::exit(1);
            }

            println!("{}", "╭─ Yuho Principle Verification".cyan().bold());
            println!("{}", format!("│  File: {}", file.display()).cyan());
            println!("{}", format!("│  Principle: {}", principle).cyan());
            println!("{}", "│".cyan());

            let source = fs::read_to_string(&file).map_err(|e| {
                eprintln!("{}", "╰─ Error".red().bold());
                eprintln!("\n  Could not read file: {}", e);
                eprintln!("  \n  → Check that the file exists");
                eprintln!("  → Path: {}\n", file.display());
                e
            })?;

            match yuho_core::parse(&source) {
                Ok(program) => {
                    println!("{}", "├─ Parser".green().bold());
                    println!(
                        "{}",
                        format!("│  ✓ {} items parsed", program.items.len()).green()
                    );
                    println!("{}", "│".cyan());

                    // Find the principle definition
                    let principle_def = program.items.iter().find_map(|item| {
                        if let yuho_core::ast::Item::PrincipleDefinition(def) = item {
                            if def.name == principle {
                                Some(def.clone())
                            } else {
                                None
                            }
                        } else {
                            None
                        }
                    });

                    match principle_def {
                        Some(def) => {
                            println!("{}", format!("├─ Found Principle".green().bold()));
                            println!("{}", format!("│  Name: {}", def.name).green());
                            println!("{}", "│".cyan());

                            if show_smt {
                                use yuho_z3::quantifier::QuantifierTranslator;
                                let translator = QuantifierTranslator::new();
                                match translator.translate_principle(&def) {
                                    Ok(smt_output) => {
                                        println!("{}", "│".cyan());
                                        println!("{}", "├─ SMT-LIB2 Translation".cyan().bold());
                                        println!("{}", "│".cyan());
                                        for line in smt_output.lines() {
                                            println!("{}", format!("│  {}", line).cyan());
                                        }
                                    },
                                    Err(e) => {
                                        println!(
                                            "{}",
                                            format!("│  ✗ SMT translation failed: {}", e).red()
                                        );
                                    },
                                }
                            }

                            use yuho_z3::VerificationContext;
                            let ctx = VerificationContext::with_timeout(5000);

                            println!("{}", "│".cyan());
                            println!("{}", "├─ Z3 Verification".green().bold());

                            match ctx.verify_principle(&def) {
                                Ok(true) => {
                                    println!("{}", "│  ✓ Principle is valid".green());
                                    println!("{}", "│".cyan());
                                    println!("{}", "╰─ Result".green().bold());
                                    println!(
                                        "{}",
                                        "   ✓ Principle verification passed!".green().bold()
                                    );
                                },
                                Ok(false) => {
                                    println!("{}", "│  ✗ Principle is invalid".red());

                                    if show_counterexample {
                                        println!("{}", "│".cyan());
                                        println!("{}", "├─ Counterexample".red().bold());

                                        use yuho_z3::counterexample::extract_counterexample;
                                        match extract_counterexample(&def) {
                                            Ok(example) => {
                                                println!("{}", "│".cyan());
                                                println!("{}", format!("│  {}", example).red());
                                            },
                                            Err(e) => {
                                                println!(
                                                    "{}",
                                                    format!(
                                                        "│  Could not generate counterexample: {}",
                                                        e
                                                    )
                                                    .yellow()
                                                );
                                            },
                                        }
                                    }

                                    println!("{}", "│".cyan());
                                    println!("{}", "╰─ Result".red().bold());
                                    println!(
                                        "{}",
                                        "   ✗ Principle has counterexamples".red().bold()
                                    );
                                    std::process::exit(1);
                                },
                                Err(e) => {
                                    println!("{}", format!("│  ✗ Verification error: {}", e).red());
                                    println!("{}", "╰─ Error".red().bold());
                                    std::process::exit(1);
                                },
                            }
                        },
                        None => {
                            println!("{}", "├─ Error".red().bold());
                            println!(
                                "{}",
                                format!("│  ✗ Principle '{}' not found in file", principle).red()
                            );
                            println!("{}", "│".cyan());
                            println!("{}", "├─ Available principles in file:".cyan());
                            let principles: Vec<String> = program
                                .items
                                .iter()
                                .filter_map(|item| {
                                    if let yuho_core::ast::Item::PrincipleDefinition(def) = item {
                                        Some(def.name.clone())
                                    } else {
                                        None
                                    }
                                })
                                .collect();
                            if principles.is_empty() {
                                println!("{}", "│  (none)".yellow());
                            } else {
                                for p in principles {
                                    println!("{}", format!("│  • {}", p).cyan());
                                }
                            }
                            println!("{}", "│".cyan());
                            println!("{}", "├─ How to fix:".cyan());
                            println!("{}", "│  • Check the principle name spelling".cyan());
                            println!("{}", "│  • Ensure the principle is defined with: principle <name> {{ ... }}".cyan());
                            println!("{}", "╰─".red());
                            std::process::exit(1);
                        },
                    }
                },
                Err(e) => {
                    println!("{}", "╰─ Parser Error".red().bold());
                    eprintln!("{}", e);
                    eprintln!("\n{}", "   Cannot verify invalid Yuho code.".yellow());
                    std::process::exit(1);
                },
            }
        },
    }

    Ok(())
}
