# Installation

This guide will help you install Yuho on your system.

## Prerequisites

Before installing Yuho, ensure you have:

- **Python 3.8 or higher**
- **pip** (Python package manager)
- **Git** (for development installation)

### Check Python Version

```bash
python --version
# or
python3 --version
```

You should see output like `Python 3.11.x` or higher.

## Installation Methods

=== "Production (pip)"

    ### Install from PyPI (Recommended)

    Once published, you can install Yuho directly from PyPI:

    ```bash
    pip install yuho
    ```

    Verify the installation:

    ```bash
    yuho --version
    ```

=== "Development (source)"

    ### Install from Source

    For development or to get the latest features:

    1. Clone the repository:

    ```bash
    git clone https://github.com/gongahkia/yuho.git
    cd yuho
    ```

    2. Install in editable mode:

    ```bash
    pip install -e .
    ```

    Or with development dependencies:

    ```bash
    pip install -r requirements-dev.txt
    pip install -e .
    ```

    3. Verify installation:

    ```bash
    yuho --version
    ```

=== "Docker"

    ### Using Docker

    The easiest way to run Yuho without installing Python:

    1. Pull the image (once available):

    ```bash
    docker pull yuho:latest
    ```

    Or build locally:

    ```bash
    git clone https://github.com/gongahkia/yuho.git
    cd yuho
    docker build -t yuho:latest .
    ```

    2. Run Yuho:

    ```bash
    # Check a file
    docker run --rm -v $(pwd):/workspace yuho:latest check example.yh

    # Start REPL
    docker run --rm -it yuho:latest yuho-repl
    ```

    3. Using docker-compose:

    ```bash
    # Development environment
    docker-compose up yuho-dev

    # Run tests
    docker-compose up yuho-test

    # Interactive REPL
    docker-compose run --rm yuho-repl
    ```

## Verify Installation

After installation, verify Yuho is working:

```bash
# Check version
yuho --version

# Get help
yuho --help

# Try the REPL
yuho-repl
```

You should see output indicating Yuho v3.0.0 or later.

## Development Setup

If you plan to contribute to Yuho:

1. Clone and install:

```bash
git clone https://github.com/gongahkia/yuho.git
cd yuho
pip install -r requirements-dev.txt
pip install -e .
```

2. Install pre-commit hooks:

```bash
pre-commit install
```

3. Run tests:

```bash
pytest
```

4. Check code quality:

```bash
black yuho_v3/
flake8 yuho_v3/
mypy yuho_v3/
```

## Platform-Specific Notes

### Linux

Installation should work out of the box on most distributions.

### macOS

Use Homebrew to install Python if needed:

```bash
brew install python@3.11
```

### Windows

1. Install Python from [python.org](https://www.python.org/downloads/)
2. Ensure "Add Python to PATH" is checked during installation
3. Use PowerShell or Command Prompt for commands

## Troubleshooting

### Command not found

If `yuho` command is not found after installation:

1. Check if Python scripts directory is in PATH:

```bash
python -m site --user-base
```

2. Add the scripts directory to your PATH

### Permission errors

On Linux/macOS, you might need:

```bash
pip install --user yuho
```

Or use a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install yuho
```

### Docker issues

Ensure Docker is running:

```bash
docker --version
docker ps
```

## Next Steps

- [Quick Start Guide](quickstart.md) - Get started with Yuho
- [Your First Program](first-program.md) - Write your first Yuho program
- [CLI Commands](../cli/commands.md) - Learn the command-line interface

