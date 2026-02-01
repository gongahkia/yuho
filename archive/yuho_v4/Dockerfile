# Multi-stage Dockerfile for Yuho v4.0
# Production-ready containerization with security best practices

# Stage 1: Base image with Python
FROM python:3.11-slim-bookworm AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100

# Create non-root user for security
RUN groupadd -r yuho && useradd -r -g yuho yuho

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Stage 2: Builder with dependencies
FROM base AS builder

# Set working directory
WORKDIR /build

# Copy dependency files
COPY requirements.txt requirements-dev.txt ./

# Install Python dependencies in a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install production dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# Stage 3: Development image with all tools
FROM builder AS development

# Install development dependencies
RUN pip install -r requirements-dev.txt

# Copy application code
COPY --chown=yuho:yuho . /app
WORKDIR /app

# Install Yuho in editable mode
RUN pip install -e .

# Switch to non-root user
USER yuho

# Default command for development
CMD ["yuho-repl"]

# Stage 4: Testing image
FROM development AS testing

# Switch back to root for test setup
USER root

# Install test dependencies
RUN pip install pytest pytest-cov pytest-xdist

# Run tests as non-root user
USER yuho

# Run tests by default
CMD ["pytest", "-v", "--cov=yuho_v4", "--cov-report=html", "--cov-report=term"]

# Stage 5: Production image (minimal)
FROM base AS production

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Set PATH to use virtual environment
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy only necessary application files
COPY --chown=yuho:yuho yuho_v4/ /app/yuho_v4/
COPY --chown=yuho:yuho setup.py README.md /app/
COPY --chown=yuho:yuho requirements.txt /app/

# Install Yuho
RUN pip install .

# Create directories for user data
RUN mkdir -p /app/workspace && chown -R yuho:yuho /app/workspace

# Switch to non-root user
USER yuho

# Set workspace as volume
VOLUME ["/app/workspace"]

# Set default working directory to workspace
WORKDIR /app/workspace

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD yuho --version || exit 1

# Default command
ENTRYPOINT ["yuho"]
CMD ["--help"]

# Labels for metadata
LABEL org.opencontainers.image.title="Yuho" \
      org.opencontainers.image.description="A domain-specific language for simplifying legal reasoning" \
      org.opencontainers.image.version="4.0.0" \
      org.opencontainers.image.authors="Gabriel Ong" \
      org.opencontainers.image.url="https://github.com/gongahkia/yuho" \
      org.opencontainers.image.source="https://github.com/gongahkia/yuho" \
      org.opencontainers.image.licenses="MIT"

