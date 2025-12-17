use thiserror::Error;

const DOCS_BASE: &str = "https://github.com/gongahkia/yuho-2/wiki";

#[derive(Error, Debug)]
pub enum YuhoError {
    #[error("\n╭─ Lexer Error at position {position}\n│\n│  {message}\n│\n├─ How to fix:\n│  • Check the syntax near position {position}\n│  • Look for unexpected characters or invalid tokens\n│  • Ensure all strings are properly closed with quotes\n│\n╰─ Documentation: {}/Syntax", DOCS_BASE)]
    LexError { position: usize, message: String },

    #[error("\n╭─ Parse Error at position {position}\n│\n│  {message}\n│\n├─ Common fixes:\n│  • Check for missing braces {{}}, brackets [], or parentheses ()\n│  • Ensure keywords are spelled correctly (struct, enum, scope, match)\n│  • Verify := is used for assignments (not =)\n│  • Make sure each statement ends properly\n│\n├─ Examples:\n│  ✓ Correct:   int age := 25\n│  ✗ Incorrect: int age = 25\n│\n╰─ Documentation: {}/Syntax", DOCS_BASE)]
    ParseError { position: usize, message: String },

    #[error("\n╭─ Type Error\n│\n│  {0}\n│\n├─ How to fix:\n│  • Ensure types match the expected usage\n│  • Check function return types match declarations\n│  • Verify struct field types match initialization\n│\n╰─ Documentation: {}/Types", DOCS_BASE)]
    TypeError(String),

    #[error("\n╭─ Undefined Symbol: '{0}'\n│\n├─ How to fix:\n│  • Define '{0}' before using it\n│  • Check for typos in the name\n│  • Ensure '{0}' is in scope\n│  • If it's a struct/enum, define it before the current location\n│\n├─ Example:\n│  int myVar := 42  // Define first\n│  int result := myVar + 10  // Then use\n│\n╰─ Documentation: {}/Variables-and-Scoping", DOCS_BASE)]
    UndefinedSymbol(String),

    #[error("\n╭─ Duplicate Definition: '{0}'\n│\n├─ How to fix:\n│  • '{0}' is already defined in this scope\n│  • Choose a different name (e.g., '{0}_2', 'new_{0}')\n│  • Remove one of the duplicate definitions\n│  • Consider using different scopes if both are needed\n│\n╰─ Documentation: {}/Variables-and-Scoping", DOCS_BASE)]
    DuplicateDefinition(String),

    #[error("\n╭─ IO Error\n│\n│  {0}\n│\n├─ Common causes:\n│  • File not found or path incorrect\n│  • Insufficient permissions to read/write\n│  • Disk full or other system issues\n│\n╰─ Check file path and permissions")]
    IoError(#[from] std::io::Error),
}

pub type Result<T> = std::result::Result<T, YuhoError>;
