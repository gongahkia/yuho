# Conflict Detection

## Overview

Yuho's conflict detection system analyzes multiple legal specification files to identify logical contradictions and inconsistencies. This is essential for ensuring that different statutes, regulations, or legal provisions don't contradict each other.

## Syntax

```yuho
verify no_conflict between file1.yh and file2.yh
```

## Use Cases

### Statutory Consistency

```yuho
// contract_act.yh
enum ContractValidity {
    Valid,
    Void,
    Voidable,
}

// consumer_protection.yh
enum ContractValidity {
    Enforceable,
    Unenforceable,
}

// main.yh
verify no_conflict between contract_act.yh and consumer_protection.yh
// ERROR: Enum 'ContractValidity' has conflicting definitions
```

### Cross-Statute Verification

```yuho
// penal_code.yh
legal_test Theft {
    requires dishonest_intent: bool,
    requires movable_property: bool,
    requires without_consent: bool,
}

// criminal_procedure.yh
legal_test Theft {
    requires criminal_intent: bool,
    requires stolen_goods: bool,
}

verify no_conflict between penal_code.yh and criminal_procedure.yh
// ERROR: Legal test 'Theft' has conflicting requirements
```

## Types of Conflicts Detected

### 1. Enum Conflicts

Different enum variants for the same enum name:

```yuho
// File 1
enum Status { Active, Inactive }

// File 2
enum Status { Running, Stopped }

// CONFLICT: Same name, different variants
```

### 2. Struct Conflicts

Different field definitions for the same struct:

```yuho
// File 1
struct Person {
    string name,
    int age,
}

// File 2
struct Person {
    string full_name,
    date birthdate,
}

// CONFLICT: Same name, different fields
```

### 3. Legal Test Conflicts

Different requirements for the same legal test:

```yuho
// File 1
legal_test Murder {
    requires intent: bool,
    requires act: bool,
}

// File 2
legal_test Murder {
    requires mens_rea: bool,
    requires actus_reus: bool,
    requires causation: bool,
}

// CONFLICT: Different requirement sets
```

## Conflict Reports

### Human-Readable Format

```
┌─ CONFLICT REPORT
│
│  Files: contract_act.yh and consumer_protection.yh
│  Conflicts found: 1
│
├─ DETAILS
│
│  [1] Enum 'ContractValidity' has conflicting definitions: ["Valid", "Void", "Voidable"] vs ["Enforceable", "Unenforceable"]
│      contract_act.yh at 10:150
│      consumer_protection.yh at 8:120
│
└─ END OF REPORT
```

### JSON Format

```json
{
  "file1": "contract_act.yh",
  "file2": "consumer_protection.yh",
  "conflict_count": 1,
  "conflicts": [
    {
      "description": "Enum 'ContractValidity' has conflicting definitions",
      "loc1_start": 10,
      "loc1_end": 150,
      "loc2_start": 8,
      "loc2_end": 120
    }
  ]
}
```

## Usage in Code

### Basic Conflict Detection

```rust
use yuho_check::conflict_detection::ConflictDetector;
use yuho_core::parse;

let mut detector = ConflictDetector::new();

// Load programs
let prog1 = parse("enum Status { A, B }")?;
let prog2 = parse("enum Status { C, D }")?;

detector.add_program("file1.yh".to_string(), prog1);
detector.add_program("file2.yh".to_string(), prog2);

// Check for conflicts
if let Some(report) = detector.check_conflict("file1.yh", "file2.yh") {
    println!("{}", report.format());
}
```

### With Z3 Verification

```rust
let detector = ConflictDetector::with_z3();
// Enables deeper semantic analysis using Z3 theorem prover
```

### Export Reports

```rust
let report = detector.check_conflict("f1.yh", "f2.yh").unwrap();

// Human-readable
println!("{}", report.format());

// JSON
println!("{}", report.to_json());
```

## Best Practices

1. **Run Before Deployment**: Always verify no conflicts between related legal files before deployment
2. **Version Control**: Track conflict checks in your build process
3. **Incremental Checks**: Check new files against existing ones when adding to a legal codebase
4. **Documentation**: Document intentional differences between similar provisions

## Limitations

### Current Version

- Conflicts are detected at the syntactic level (name and structure)
- Semantic equivalence is not yet detected (e.g., `age` vs `years_old`)
- Cross-file dependency analysis is basic

### Future Enhancements

- **Deep Semantic Analysis**: Use Z3 to detect logical contradictions
- **Equivalence Detection**: Recognize semantically equivalent but syntactically different definitions
- **Conflict Resolution Suggestions**: Propose ways to resolve detected conflicts
- **Batch Analysis**: Check multiple files simultaneously

## CLI Usage

```bash
# Check two files
yuho conflict contract_act.yh consumer_protection.yh

# Check with JSON output
yuho conflict --format=json file1.yh file2.yh

# Enable Z3 verification
yuho conflict --z3 file1.yh file2.yh

# Check all files in directory
yuho conflict --all statutes/
```

## Integration with Build Systems

### Cargo Build Script

```rust
// build.rs
use yuho_check::conflict_detection::ConflictDetector;

fn main() {
    let mut detector = ConflictDetector::new();

    // Load all .yh files
    for file in glob("legal/*.yh").unwrap() {
        let content = std::fs::read_to_string(&file).unwrap();
        let program = yuho_core::parse(&content).unwrap();
        detector.add_program(file, program);
    }

    // Check all pairs for conflicts
    // ... report any issues
}
```

## Examples

See `/examples/conflict_detection/` for:
- Cross-statute verification
- Regulatory consistency checks
- Multi-jurisdictional analysis
- Amendment conflict detection

---

**Version**: 1.0
**Status**: Core functionality complete, Z3 integration in progress
