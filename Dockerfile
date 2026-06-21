# Verification image for the Yuho toolchain and encoded corpus.
#
# Goal: a clean container in which the main project checks regenerate
# from the encoded library with one command.
#
# Build:
#     docker build -t yuho:latest .
#
# Run full verification (~5 minutes, no network during build except
# image install):
#     docker run --rm yuho:latest make -C /workspace verify-all
#
# The image installs:
#   - Python 3.12 + Yuho's [dev] extras (Z3, hypothesis, etc.)
#   - Node 22 + tree-sitter-cli (for grammar regeneration)
#   - xmllint (for AKN OASIS-XSD round-trip validation)
FROM python:3.12-slim AS base

# System packages: xmllint for AKN validation; build-essential for
# tree-sitter native extension; node for mmdc + tree-sitter CLI;
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        curl \
        git \
        libxml2-utils \
        nodejs \
        npm \
    && rm -rf /var/lib/apt/lists/*

# tree-sitter CLI — used to regenerate the grammar, harmless if
# unused but cheap to install.
RUN npm install -g tree-sitter-cli@0.23.0 || \
    npm install -g tree-sitter-cli

WORKDIR /workspace

# Copy the project. .dockerignore excludes the venvs / build caches
# so this layer rebuilds quickly when source changes.
COPY pyproject.toml README.md ./
COPY src ./src
COPY library ./library
COPY scripts ./scripts
COPY tests ./tests
COPY evals ./evals
COPY benchmarks ./benchmarks
COPY simulator ./simulator
COPY docs ./docs
COPY editors ./editors
COPY Makefile* ./

# Install the tree-sitter Python bindings + Yuho with dev extras.
# `pip install -e` would re-trigger native compilation on container
# boot; non-editable install bakes everything in.
RUN python -m pip install --upgrade pip && \
    pip install ./src/tree-sitter-yuho/bindings/python && \
    pip install -e .[dev]

# Verify the toolchain at build time so a corrupt image fails fast.
RUN yuho check library/penal_code/s415_cheating/statute.yh

# Default entrypoint surfaces the full verification target.
CMD ["make", "verify-all"]
