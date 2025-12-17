#!/bin/bash

# Install Yuho Pre-Commit Hooks
# This script sets up git hooks for automatic code quality checks

echo "Installing Yuho pre-commit hooks..."

# Create pre-commit hook
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash

# Yuho Pre-Commit Hook
# Runs tests, clippy, and formatting checks before allowing commits

set -e

echo "🔍 Running pre-commit checks..."
echo

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check 1: Rust formatting
echo "📝 Checking code formatting..."
if ! cargo fmt --all -- --check; then
    echo -e "${RED}✗ Code formatting check failed${NC}"
    echo -e "${YELLOW}Run 'cargo fmt --all' to fix formatting${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Code formatting check passed${NC}"
echo

# Check 2: Clippy lints
echo "🔎 Running clippy..."
if ! cargo clippy --all-targets --all-features -- -D warnings 2>&1 | grep -v "^warning: "; then
    echo -e "${RED}✗ Clippy found issues${NC}"
    echo -e "${YELLOW}Fix clippy warnings before committing${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Clippy check passed${NC}"
echo

# Check 3: Tests
echo "🧪 Running tests..."
if ! cargo test --all --quiet 2>&1; then
    echo -e "${RED}✗ Tests failed${NC}"
    echo -e "${YELLOW}Fix failing tests before committing${NC}"
    exit 1
fi
echo -e "${GREEN}✓ All tests passed${NC}"
echo

echo -e "${GREEN}✅ All pre-commit checks passed!${NC}"
echo
EOF

# Make hook executable
chmod +x .git/hooks/pre-commit

echo "✅ Pre-commit hook installed successfully!"
echo
echo "The hook will automatically run before each commit to check:"
echo "  • Code formatting (cargo fmt)"
echo "  • Lints (cargo clippy)"
echo "  • Tests (cargo test)"
echo
echo "To bypass the hook (not recommended), use: git commit --no-verify"
