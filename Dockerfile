# AEC-grade reproducibility image for the Yuho paper.
#
# Goal: a clean container in which every empirical claim in the
# paper — coverage stats, AKN round-trip 524/524, contrast bulk run,
# evals fake-run, case-law differential testing, paper smoke build —
# regenerates from the encoded library with one command.
#
# Build:
#     docker build -t yuho:latest .
#
# Run claims-verification (~5 minutes, no network during build except
# image install):
#     docker run --rm yuho:latest make -C /workspace paper-reproduce
#
# Run a full paper rebuild (LaTeX, ~3-5 minutes additional):
#     docker run --rm yuho:latest make -C /workspace/paper smoke
#
# The image installs:
#   - Python 3.12 + Yuho's [dev] extras (Z3, hypothesis, etc.)
#   - Node 22 + tree-sitter-cli (for grammar regeneration)
#   - xmllint (for AKN OASIS-XSD round-trip validation)
#   - texlive (article-class smoke build of the paper; the full
#     acmart build needs additional CTAN packages, see Dockerfile.paper)
FROM python:3.12-slim AS base

# System packages: xmllint for AKN validation; build-essential for
# tree-sitter native extension; node for mmdc + tree-sitter CLI;
# texlive-* for the smoke paper build (full acmart needs additional
# packages — covered in a separate Dockerfile.paper layer if needed).
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
COPY paper ./paper
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

# Default entrypoint surfaces the reproducibility Make target.
CMD ["make", "paper-reproduce"]
