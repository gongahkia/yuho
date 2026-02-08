# Yuho Z3 Integration

SMT solver integration for formal verification of Yuho specifications.

## Building

This crate is **excluded from the default workspace** because it requires `libclang` which may not be available on all systems.

### Prerequisites

1. Install Z3:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install libz3-dev

   # Fedora
   sudo dnf install z3-devel

   # macOS
   brew install z3
   ```

2. Install libclang:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install libclang-dev

   # Fedora
   sudo dnf install clang-devel

   # macOS
   brew install llvm
   export LIBCLANG_PATH=/opt/homebrew/opt/llvm/lib  # Add to .zshrc/.bashrc
   ```

### Building

Build this crate independently:

```bash
cd crates/yuho-z3
cargo build
```

Or from the workspace root:

```bash
cargo build --package yuho-z3
```