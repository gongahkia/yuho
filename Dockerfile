FROM python:3.12-slim AS builder
RUN apt-get update && apt-get install -y --no-install-recommends gcc libc6-dev && rm -rf /var/lib/apt/lists/*
WORKDIR /build
COPY src/ src/
RUN cd src/tree-sitter-yuho && cc -shared -fPIC -I src src/parser.c src/scanner.c -o ../tree_sitter_yuho/libtree-sitter-yuho.so
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir ./src

FROM python:3.12-slim
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY library/ /app/library/
WORKDIR /app
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1
ENTRYPOINT ["yuho"]
CMD ["api", "--host", "0.0.0.0", "--port", "8080"]
