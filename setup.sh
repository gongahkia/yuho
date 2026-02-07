#!/bin/bash
# Yuho Installation Script
# Usage: ./setup.sh [--dev] [--no-venv]
#
# This script handles the complete installation of Yuho including:
# - Installing uv (fast Python package manager)
# - Creating a virtual environment (optional)
# - Installing tree-sitter CLI
# - Building the tree-sitter-yuho grammar
# - Installing the yuho package

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GRAMMAR_DIR="$SCRIPT_DIR/src/tree-sitter-yuho"
SRC_DIR="$SCRIPT_DIR/src"

# Default options
USE_VENV=true
DEV_MODE=false
VERBOSE=false
USE_UV=true

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --no-venv)
            USE_VENV=false
            shift
            ;;
        --dev)
            DEV_MODE=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            echo "Usage: ./setup.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --no-venv    Skip virtual environment creation"
            echo "  --dev        Install development dependencies"
            echo "  -v, --verbose  Show verbose output"
            echo "  -h, --help   Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

log() {
    echo -e "${BLUE}[yuho]${NC} $1"
}

success() {
    echo -e "${GREEN}[yuho]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[yuho]${NC} $1"
}

error() {
    echo -e "${RED}[yuho]${NC} $1"
}

# Check Python version
check_python() {
    log "Checking Python version..."

    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        error "Python not found. Please install Python 3.10 or later."
        exit 1
    fi

    PYTHON_VERSION=$($PYTHON_CMD -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    MAJOR=$($PYTHON_CMD -c "import sys; print(sys.version_info.major)")
    MINOR=$($PYTHON_CMD -c "import sys; print(sys.version_info.minor)")

    if [[ $MAJOR -lt 3 ]] || [[ $MAJOR -eq 3 && $MINOR -lt 10 ]]; then
        error "Python 3.10 or later is required. Found: $PYTHON_VERSION"
        exit 1
    fi

    success "Found Python $PYTHON_VERSION"
}

# Install uv package manager
install_uv() {
    if command -v uv &> /dev/null; then
        UV_VERSION=$(uv --version 2>/dev/null || echo "unknown")
        success "uv already installed: $UV_VERSION"
        return 0
    fi

    log "Installing uv (fast Python package manager)..."

    # Install uv using the official installer
    if curl -LsSf https://astral.sh/uv/install.sh | sh; then
        # Add to PATH for current session
        export PATH="$HOME/.local/bin:$PATH"
        if command -v uv &> /dev/null; then
            success "Installed uv successfully"
            return 0
        fi
    fi

    # Fallback: try pip
    if command -v pip &> /dev/null || command -v pip3 &> /dev/null; then
        log "Trying pip install..."
        pip install uv || pip3 install uv
        if command -v uv &> /dev/null; then
            success "Installed uv via pip"
            return 0
        fi
    fi

    warn "Could not install uv, falling back to pip"
    USE_UV=false
}

# Setup virtual environment
setup_venv() {
    if [[ "$USE_VENV" == false ]]; then
        log "Skipping virtual environment setup"
        if [[ "$USE_UV" == true ]]; then
            PKG_CMD="uv pip"
        else
            PKG_CMD="pip"
        fi
        return
    fi

    VENV_DIR="$SCRIPT_DIR/.venv"

    if [[ -d "$VENV_DIR" ]]; then
        log "Using existing virtual environment at .venv"
    else
        log "Creating virtual environment..."
        if [[ "$USE_UV" == true ]]; then
            uv venv "$VENV_DIR"
        else
            $PYTHON_CMD -m venv "$VENV_DIR"
        fi
        success "Created virtual environment at .venv"
    fi

    # Activate venv
    source "$VENV_DIR/bin/activate"
    
    if [[ "$USE_UV" == true ]]; then
        PKG_CMD="uv pip"
    else
        PKG_CMD="pip"
        # Upgrade pip
        log "Upgrading pip..."
        $PKG_CMD install --upgrade pip -q
    fi
}

# Install tree-sitter CLI
install_tree_sitter_cli() {
    if command -v tree-sitter &> /dev/null; then
        TS_VERSION=$(tree-sitter --version 2>/dev/null || echo "unknown")
        success "tree-sitter CLI already installed: $TS_VERSION"
        return 0
    fi

    log "Installing tree-sitter CLI..."

    # Try npm first (most common)
    if command -v npm &> /dev/null; then
        log "Installing via npm..."
        npm install -g tree-sitter-cli
        if command -v tree-sitter &> /dev/null; then
            success "Installed tree-sitter CLI via npm"
            return 0
        fi
    fi

    # Try homebrew on macOS
    if [[ "$(uname)" == "Darwin" ]] && command -v brew &> /dev/null; then
        log "Installing via Homebrew..."
        brew install tree-sitter
        if command -v tree-sitter &> /dev/null; then
            success "Installed tree-sitter CLI via Homebrew"
            return 0
        fi
    fi

    # Try cargo
    if command -v cargo &> /dev/null; then
        log "Installing via Cargo..."
        cargo install tree-sitter-cli
        if command -v tree-sitter &> /dev/null; then
            success "Installed tree-sitter CLI via Cargo"
            return 0
        fi
    fi

    error "Could not install tree-sitter CLI automatically."
    echo ""
    echo "Please install it manually using one of:"
    echo "  npm install -g tree-sitter-cli"
    echo "  brew install tree-sitter"
    echo "  cargo install tree-sitter-cli"
    echo ""
    exit 1
}

# Build tree-sitter-yuho grammar
build_grammar() {
    log "Building tree-sitter-yuho grammar..."

    cd "$GRAMMAR_DIR"

    # Generate parser from grammar.js
    log "Generating parser..."
    tree-sitter generate

    # Build the shared library
    log "Compiling shared library..."
    tree-sitter build

    # Determine library extension
    if [[ "$(uname)" == "Darwin" ]]; then
        LIB_EXT="dylib"
    else
        LIB_EXT="so"
    fi

    # Find and copy the built library to src/tree_sitter_yuho/
    DEST_DIR="$SRC_DIR/tree_sitter_yuho"
    mkdir -p "$DEST_DIR"

    copied=false
    for lib_name in "yuho.$LIB_EXT" "libtree-sitter-yuho.$LIB_EXT"; do
        if [[ -f "$GRAMMAR_DIR/$lib_name" ]]; then
            cp "$GRAMMAR_DIR/$lib_name" "$DEST_DIR/"
            success "Copied $lib_name to $DEST_DIR"
            copied=true
            break
        fi
    done

    if [[ "$copied" == false ]]; then
        warn "Could not find built library, installation may still work"
    fi

    cd "$SCRIPT_DIR"
    success "Grammar built successfully"
}

# Install yuho package
install_yuho() {
    log "Installing yuho..."

    cd "$SRC_DIR"

    if [[ "$DEV_MODE" == true ]]; then
        $PKG_CMD install -e ".[all]"
    else
        $PKG_CMD install -e .
    fi

    # Install pytest for testing
    log "Installing pytest..."
    $PKG_CMD install pytest

    # Install LSP dependencies
    log "Installing LSP dependencies..."
    $PKG_CMD install pygls lsprotocol

    # Install MCP dependencies
    log "Installing MCP dependencies..."
    $PKG_CMD install mcp

    cd "$SCRIPT_DIR"
    success "Yuho installed successfully"
}

# Verify installation
verify_installation() {
    log "Verifying installation..."

    # Check CLI works
    if yuho --version &> /dev/null; then
        VERSION=$(yuho --version)
        success "CLI working: $VERSION"
    else
        error "CLI verification failed"
        exit 1
    fi

    # Check parser works
    if echo 'struct Test { x: int }' | timeout 5 yuho check - 2>/dev/null; then
        success "Parser working"
    else
        warn "Parser check skipped or failed (may need grammar rebuild)"
    fi
}

# Main installation
main() {
    echo ""
    echo -e "${BLUE}╔══════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║     Yuho Installation Script         ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════╝${NC}"
    echo ""

    check_python
    install_uv
    setup_venv
    install_tree_sitter_cli
    build_grammar
    install_yuho
    verify_installation

    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║     Installation Complete!           ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════╝${NC}"
    echo ""

    if [[ "$USE_VENV" == true ]]; then
        echo "To activate the environment:"
        echo "  source .venv/bin/activate"
        echo ""
    fi

    echo "To get started:"
    echo "  yuho --help"
    echo "  yuho repl"
    echo ""
}

main
