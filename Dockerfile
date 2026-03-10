FROM python:3.12-slim AS base

RUN apt-get update && apt-get install -y --no-install-recommends \
    nodejs npm git \
    && npm install -g tree-sitter-cli \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY src/ ./src/
COPY library/ ./library/
COPY examples/ ./examples/

RUN pip install --no-cache-dir -e ./src/tree-sitter-yuho/bindings/python \
    && pip install --no-cache-dir -e ./src

ENTRYPOINT ["yuho"]
CMD ["--help"]
