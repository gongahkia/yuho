//! Example: Statute Parsing with LLM
//!
//! Demonstrates statute parsing and Yuho code generation.
//!
//! Run with: cargo run --example statute_parsing -p yuho-llm

use yuho_llm::{provider::MockProvider, statute::StatuteParser};

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("=== Yuho Statute Parser Example ===\n");

    let provider = MockProvider::new();
    let parser = StatuteParser::new(provider);

    let statute_text = r#"
Section 415: Cheating

Whoever by deceiving any person fraudulently or dishonestly induces 
the person so deceived to deliver any property to any person, is said 
to "cheat".
    "#;

    println!("📄 Parsing statute...");
    let result = parser.parse(statute_text).await?;

    println!("\n✅ Result:");
    println!("   Title: {}", result.title);
    println!("   Sections: {}", result.sections.len());
    println!("   Entities: {}", result.entities.len());
    println!("   Confidence: {:.1}%", result.confidence * 100.0);

    println!("\n📋 Generated code:");
    for line in result.generated_code.lines() {
        println!("   {}", line);
    }

    println!("\n=== Complete ===");
    Ok(())
}
