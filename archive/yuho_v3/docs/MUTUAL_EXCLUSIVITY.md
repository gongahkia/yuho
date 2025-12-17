# Mutual Exclusivity Checking

## Overview

Mutually exclusive enums ensure that function code paths can only return ONE variant of an enum, never multiple variants. This is verified at compile time through control flow analysis.

## Syntax

```yuho
mutually_exclusive enum Verdict {
    Guilty,
    NotGuilty,
}
```

## Use Cases

### Legal Verdicts

```yuho
mutually_exclusive enum CriminalVerdict {
    Guilty,
    NotGuilty,
}

// ✅ Valid: returns only one variant
func simple_case() -> CriminalVerdict {
    return CriminalVerdict::Guilty
}

// ❌ Invalid: could return multiple variants
func invalid_case(bool cond) -> CriminalVerdict {
    if cond {
        return CriminalVerdict::Guilty
    }
    return CriminalVerdict::NotGuilty  // ERROR: Multiple return paths
}
```

### Binary Decisions

```yuho
mutually_exclusive enum ApprovalStatus {
    Approved,
    Rejected,
}

func process_application(Application app) -> ApprovalStatus {
    match app.score {
        case score where score >= 70 := ApprovalStatus::Approved
        case _ := ApprovalStatus::Rejected
    }
}
```

## Transpilation

### TypeScript
```typescript
export type Verdict = "Guilty" | "NotGuilty";

// MUTUALLY EXCLUSIVE: Verdict variants must not overlap in return paths
// Static analysis enforces this at compile time
```

### Alloy
```alloy
abstract sig Verdict {}
one sig Guilty extends Verdict {}
one sig NotGuilty extends Verdict {}

// Mutual exclusivity constraint
fact MutuallyExclusiveVerdict {
  no (Guilty & NotGuilty)
}
```

### LaTeX
```latex
\subsection*{Categories: Verdict}
\textbf{MUTUALLY EXCLUSIVE}: Only one variant may be selected.

The following categories are defined:
\begin{itemize}
  \item Guilty
  \item NotGuilty
\end{itemize}
```

## Formal Verification

The Z3 theorem prover verifies:
1. At least 2 variants exist
2. Variants are logically distinct
3. At most one variant can be true

```bash
yuho verify verdict.yh
```

## Best Practices

1. **Use for binary/exclusive outcomes**: Guilty/NotGuilty, Pass/Fail, Approved/Rejected
2. **NOT for flags or states**: Use regular enums for non-exclusive values
3. **Control flow must be clear**: Avoid ambiguous return paths

## Limitations

- Requires control flow analysis (currently basic implementation)
- Match expressions with guards may need manual review
- Cross-function analysis not yet implemented

---

**Version**: 1.0
**Status**: Core infrastructure complete
