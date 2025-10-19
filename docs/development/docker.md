# Docker Development

Guide to using Docker for Yuho development and deployment.

## Overview

Docker provides a consistent development environment for Yuho across different platforms and simplifies deployment.

## Prerequisites

- Docker installed on your system
- Basic understanding of Docker concepts
- Familiarity with containerization

## Development Setup

### Dockerfile

```dockerfile
# Use Python 3.11 as base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements files
COPY requirements.txt requirements-dev.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r requirements-dev.txt

# Copy source code
COPY . .

# Install Yuho in development mode
RUN pip install -e .

# Set default command
CMD ["yuho", "--help"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  yuho-dev:
    build: .
    volumes:
      - .:/app
      - /app/__pycache__
    working_dir: /app
    command: bash
    stdin_open: true
    tty: true
    environment:
      - PYTHONPATH=/app
      - YUHO_ENV=development

  yuho-test:
    build: .
    volumes:
      - .:/app
    working_dir: /app
    command: pytest
    environment:
      - PYTHONPATH=/app
      - YUHO_ENV=testing

  yuho-docs:
    build: .
    volumes:
      - .:/app
    working_dir: /app
    command: mkdocs serve
    ports:
      - "8000:8000"
    environment:
      - PYTHONPATH=/app
      - YUHO_ENV=documentation
```

## Development Workflow

### Building the Image

```bash
# Build development image
docker build -t yuho-dev .

# Build with specific tag
docker build -t yuho-dev:latest .
```

### Running Development Container

```bash
# Run interactive container
docker run -it --rm yuho-dev bash

# Run with volume mounting
docker run -it --rm -v $(pwd):/app yuho-dev bash

# Run specific command
docker run --rm yuho-dev yuho --help
```

### Using Docker Compose

```bash
# Start development environment
docker-compose up yuho-dev

# Run tests
docker-compose run yuho-test

# Start documentation server
docker-compose up yuho-docs
```

## Development Commands

### Basic Development

```bash
# Enter development container
docker-compose run --rm yuho-dev bash

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install in development mode
pip install -e .

# Run tests
pytest
```

### Code Quality

```bash
# Format code
black yuho_v3/

# Check style
flake8 yuho_v3/

# Type checking
mypy yuho_v3/
```

### Documentation

```bash
# Start documentation server
mkdocs serve

# Build documentation
mkdocs build

# Deploy documentation
mkdocs gh-deploy
```

## Testing with Docker

### Test Container

```dockerfile
# Test-specific Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt requirements-dev.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r requirements-dev.txt

# Copy source code
COPY . .

# Install in development mode
RUN pip install -e .

# Set test command
CMD ["pytest", "--cov=yuho_v3", "--cov-report=html"]
```

### Running Tests

```bash
# Run tests in container
docker run --rm yuho-test

# Run tests with coverage
docker run --rm yuho-test pytest --cov=yuho_v3

# Run specific tests
docker run --rm yuho-test pytest tests/test_parser.py
```

### Test Coverage

```bash
# Generate coverage report
docker run --rm -v $(pwd)/coverage:/app/coverage yuho-test pytest --cov=yuho_v3 --cov-report=html

# View coverage report
open coverage/htmlcov/index.html
```

## Documentation with Docker

### Documentation Container

```dockerfile
# Documentation-specific Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt requirements-dev.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r requirements-dev.txt

# Copy source code
COPY . .

# Install in development mode
RUN pip install -e .

# Install MkDocs
RUN pip install mkdocs mkdocs-material

# Set documentation command
CMD ["mkdocs", "serve", "--dev-addr=0.0.0.0:8000"]
```

### Running Documentation

```bash
# Start documentation server
docker run -p 8000:8000 yuho-docs

# Build documentation
docker run --rm yuho-docs mkdocs build

# Deploy documentation
docker run --rm yuho-docs mkdocs gh-deploy
```

## Production Deployment

### Production Dockerfile

```dockerfile
# Multi-stage build for production
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Install Yuho
RUN pip install .

# Production stage
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy installed packages
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Create non-root user
RUN useradd -m -u 1000 yuho

# Switch to non-root user
USER yuho

# Set default command
CMD ["yuho", "--help"]
```

### Production docker-compose.yml

```yaml
version: '3.8'

services:
  yuho:
    build: .
    ports:
      - "8000:8000"
    environment:
      - YUHO_ENV=production
    volumes:
      - ./data:/app/data
    restart: unless-stopped
```

## Docker Best Practices

### Image Optimization

```dockerfile
# Use specific Python version
FROM python:3.11-slim

# Use multi-stage builds
FROM python:3.11-slim as builder
# ... build stage
FROM python:3.11-slim as production
# ... production stage

# Minimize layers
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Use .dockerignore
# __pycache__
# *.pyc
# .git
# .pytest_cache
# coverage
```

### Security

```dockerfile
# Create non-root user
RUN useradd -m -u 1000 yuho
USER yuho

# Use specific versions
FROM python:3.11-slim

# Remove unnecessary packages
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*
```

### Performance

```dockerfile
# Use build cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code after dependencies
COPY . .

# Use specific Python version
FROM python:3.11-slim
```

## Environment Variables

### Development Environment

```bash
# Development environment variables
export YUHO_ENV=development
export PYTHONPATH=/app
export YUHO_LOG_LEVEL=DEBUG
```

### Production Environment

```bash
# Production environment variables
export YUHO_ENV=production
export YUHO_LOG_LEVEL=INFO
export YUHO_CONFIG=/app/config.yaml
```

### Docker Environment

```yaml
# docker-compose.yml environment
environment:
  - YUHO_ENV=development
  - PYTHONPATH=/app
  - YUHO_LOG_LEVEL=DEBUG
```

## Volume Management

### Development Volumes

```yaml
# docker-compose.yml volumes
volumes:
  - .:/app
  - /app/__pycache__
  - /app/.pytest_cache
```

### Production Volumes

```yaml
# docker-compose.yml volumes
volumes:
  - ./data:/app/data
  - ./logs:/app/logs
  - ./config:/app/config
```

### Volume Permissions

```bash
# Set volume permissions
docker run --rm -v $(pwd):/app yuho-dev chown -R 1000:1000 /app
```

## Networking

### Development Networking

```yaml
# docker-compose.yml networking
services:
  yuho-dev:
    networks:
      - yuho-network

networks:
  yuho-network:
    driver: bridge
```

### Production Networking

```yaml
# docker-compose.yml networking
services:
  yuho:
    networks:
      - yuho-network
    ports:
      - "8000:8000"

networks:
  yuho-network:
    driver: bridge
```

## Monitoring and Logging

### Logging Configuration

```python
# logging.conf
[loggers]
keys=root,yuho

[handlers]
keys=console,file

[formatters]
keys=standard

[logger_root]
level=INFO
handlers=console

[logger_yuho]
level=DEBUG
handlers=console,file
qualname=yuho
propagate=0

[handler_console]
class=StreamHandler
level=DEBUG
formatter=standard
args=(sys.stdout,)

[handler_file]
class=FileHandler
level=DEBUG
formatter=standard
args=('yuho.log',)

[formatter_standard]
format=%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

### Monitoring

```yaml
# docker-compose.yml monitoring
services:
  yuho:
    healthcheck:
      test: ["CMD", "yuho", "--version"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## Troubleshooting

### Common Issues

#### Issue 1: Permission Denied

```bash
# Problem: Permission denied when mounting volumes
docker run -v $(pwd):/app yuho-dev
# Permission denied
```

**Solution**: Fix volume permissions:

```bash
# Fix volume permissions
docker run --rm -v $(pwd):/app yuho-dev chown -R 1000:1000 /app
```

#### Issue 2: Import Errors

```bash
# Problem: Import errors in container
docker run yuho-dev python -c "import yuho_v3"
# ImportError: No module named 'yuho_v3'
```

**Solution**: Set PYTHONPATH:

```bash
# Set PYTHONPATH
docker run -e PYTHONPATH=/app yuho-dev python -c "import yuho_v3"
```

#### Issue 3: Port Conflicts

```bash
# Problem: Port already in use
docker run -p 8000:8000 yuho-docs
# Port 8000 is already in use
```

**Solution**: Use different port:

```bash
# Use different port
docker run -p 8001:8000 yuho-docs
```

### Debugging

```bash
# Debug container
docker run -it --rm yuho-dev bash

# Check container logs
docker logs yuho-container

# Inspect container
docker inspect yuho-container
```

## Advanced Usage

### Multi-Architecture Builds

```bash
# Build for multiple architectures
docker buildx build --platform linux/amd64,linux/arm64 -t yuho:latest .
```

### CI/CD Integration

```yaml
# .github/workflows/docker.yml
name: Docker Build

on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Build Docker image
      run: docker build -t yuho:latest .
    
    - name: Run tests
      run: docker run --rm yuho:latest pytest
    
    - name: Push to registry
      run: docker push yuho:latest
```

### Kubernetes Deployment

```yaml
# kubernetes.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: yuho
spec:
  replicas: 3
  selector:
    matchLabels:
      app: yuho
  template:
    metadata:
      labels:
        app: yuho
    spec:
      containers:
      - name: yuho
        image: yuho:latest
        ports:
        - containerPort: 8000
        env:
        - name: YUHO_ENV
          value: production
```

## Next Steps

- [Contributing Guide](contributing.md) - How to contribute to Yuho
- [Testing Guide](testing.md) - How to test Yuho
- [Architecture Guide](architecture.md) - Understanding Yuho's architecture
- [API Reference](../api/parser.md) - Complete API documentation
