### 1. CLI Help Overview

Shows all 21 available CLI commands.

```bash
yuho --help
```

### 2. Validation with Error Messages

**Success case:**

```bash
yuho check library/penal_code/s415_cheating.yh
```

### 3. Transpilation to Mermaid Diagrams

```bash
yuho transpile library/penal_code/s415_cheating.yh --target mermaid
```

### 4. Transpilation to Plain English

Shows how legal logic is converted to human-readable English.

```bash
yuho transpile library/penal_code/s415_cheating.yh --target english
```

### 5. Live Preview

Shows auto-reloading preview with file changes.

```bash
yuho preview library/penal_code/s415_cheating.yh
```

### 6. AST Visualization

Shows the parsed AST tree structure with statistics.

```bash
yuho ast library/penal_code/s415_cheating.yh
```

### 7. Interactive REPL

Screenshot the REPL interface with some sample commands executed.

```bash
yuho repl
```

Example REPL session to demonstrate:

```
>>> parse "scope test { integer x := 5 }"
>>> transpile --target english
>>> help
>>> exit
```

### 8. Testing with Coverage

```bash
yuho test library/penal_code/s415_cheating.yh --coverage
```

### 9. Diff Between Files

Compare two Yuho files and show semantic differences.

```bash
yuho diff file1.yh file2.yh
```

### 10. JSON Output

Machine-readable structured output for tooling integration.

```bash
yuho transpile library/penal_code/s415_cheating.yh --target json
```