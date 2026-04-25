# Error Codes

## API Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `UNAUTHORIZED` | 401 | Missing or invalid Authorization header |
| `RATE_LIMITED` | 429 | Too many requests, check Retry-After header |
| `NOT_FOUND` | 404 | Endpoint does not exist |
| `UNSUPPORTED_MEDIA` | 415 | Content-Type must be application/json |
| `PAYLOAD_TOO_LARGE` | 413 | Request body exceeds 1MB limit |
| `INVALID_JSON` | 400 | Malformed JSON in request body |
| `BAD_REQUEST` | 400 | Invalid Content-Length or other request error |
| `VALIDATION_ERROR` | 400 | Request payload fails schema validation |
| `PARSE_ERROR` | 422 | Yuho source has syntax errors |
| `UNKNOWN` | 500 | Unexpected server error |

## Analysis Error Stages

Returned in validation and check results under `error.stage`:

| Stage | Description | Common Causes |
|-------|-------------|---------------|
| `parse` | Tree-sitter parse failure | Syntax errors, missing semicolons, unclosed braces |
| `ast` | AST construction failure | Malformed tree-sitter output, unsupported node types |
| `scope` | Scope analysis failure | Undefined variables, duplicate declarations |
| `type` | Type checking failure | Type mismatches, unknown type names |
| `lint` | Lint rule violation | Missing elements, naming conventions |
| `transpile` | Transpilation failure | Unsupported AST patterns for target format |

## CLI Exit Codes

See [CLI_EXIT_CODES.md](cli-exit-codes.md).
