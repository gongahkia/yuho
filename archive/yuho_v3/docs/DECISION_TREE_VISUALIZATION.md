# Decision Tree Visualization in Yuho

This document explains the **Decision Tree Visualization** feature in Yuho for analyzing legal decision logic.

## Overview

Legal reasoning often involves complex decision trees based on multiple conditions and outcomes. Yuho can automatically extract these decision trees from match expressions and generate interactive HTML visualizations.

## Usage

### Command Line

```bash
yuho decision-tree liability.yh
yuho decision-tree liability.yh -o analysis.html
```

This generates an interactive HTML file with D3.js visualization of all match expressions found in the program.

## Match Expression Mapping

### Basic Match

```yuho
fn assess_liability(fault: FaultType) -> LiabilityStatus {
    match fault {
        case Negligence := Liable
        case IntentionalWrongdoing := Liable
        case StrictLiability := Liable
        case _ := NotLiable
    }
}
```

**Decision Tree Structure:**
```
Root: Match fault
├─ Decision: Negligence → Action: Liable
├─ Decision: IntentionalWrongdoing → Action: Liable
├─ Decision: StrictLiability → Action: Liable
└─ Default: _ → Action: NotLiable
```

### Nested Conditions

```yuho
fn determine_sentence(offense: CriminalOffense, value: int) -> SentencingSeverity {
    match offense {
        case Theft :=
            if value > 10000 {
                Imprisonment
            } else {
                Fine
            }
        case Fraud := Probation
        case _ := Fine
    }
}
```

**Decision Tree Structure:**
```
Root: Match offense
├─ Decision: Theft
│  └─ Action: if value > 10000 then Imprisonment else Fine
├─ Decision: Fraud
│  └─ Action: Probation
└─ Default: _
   └─ Action: Fine
```

## Visualization Features

### Interactive Elements

- **Expandable Nodes**: Click nodes to expand/collapse subtrees
- **Color Coding**:
  - 🟢 Green: Root (match expression)
  - 🔵 Blue: Decision point (pattern)
  - 🟡 Yellow: Action/outcome
  - ⚫ Gray: Default/wildcard
- **Hover Information**: See full expression text
- **Guard Clauses**: Displays `where` conditions when present

### D3.js Layout

The visualization uses D3.js tree layout with:
- Horizontal orientation (left to right)
- Automatic spacing and alignment
- Smooth transitions and animations
- Responsive sizing

## Node Types

### Root Node (Green)

Represents the match scrutinee (the value being matched):

```yuho
match fault { ... }
```

Root node label: `"Match: fault"`

### Decision Node (Blue)

Represents a pattern case:

```yuho
case Negligence := ...
```

Decision node label: `"Negligence"`

### Action Node (Yellow)

Represents the consequence of matching:

```yuho
case Theft := Liable
```

Action node label: `"Liable"`

### Default Node (Gray)

Represents the wildcard catch-all:

```yuho
case _ := NotLiable
```

Default node label: `"_"`

## Use Cases

### Legal Analysis

1. **Statutory Interpretation**: Visualize how laws apply to different scenarios
2. **Case Assessment**: Map out decision factors in litigation
3. **Risk Analysis**: Show potential outcomes based on evidence
4. **Compliance Checking**: Illustrate regulatory decision paths

### Documentation

- Include in legal briefs to explain reasoning
- Use in training materials for legal staff
- Present to clients to show case evaluation
- Add to reports for stakeholder review

## Example Workflow

1. **Write Yuho code** with match expressions modeling legal decisions
2. **Generate visualization**: `yuho decision-tree contract.yh`
3. **Open in browser**: View `decision-tree.html`
4. **Explore interactively**: Click nodes, examine paths
5. **Export**: Screenshot or embed in documents

## Implementation Details

### AST Traversal

The decision tree builder:
1. Parses the Yuho program into an AST
2. Traverses all items looking for match expressions
3. Extracts match scrutinee and cases
4. Builds a tree structure with DecisionNode types
5. Serializes to JSON for D3.js consumption

### HTML Template

The generated HTML includes:
- D3.js v7 from CDN
- Embedded CSS for styling
- JavaScript for rendering and interaction
- Legend explaining color coding
- Responsive layout for various screen sizes

## Related Features

- **Pattern Matching** - Core language feature
- **Guard Clauses** - Conditional pattern matching with `where`
- **English Transpilation** - Narrative explanation of decision logic
- **Mermaid Diagrams** - Alternative flowchart visualization

## Best Practices

1. **Clear Patterns**: Use descriptive enum variants
2. **Exhaustive Matching**: Cover all cases or use wildcard
3. **Guard Documentation**: Add comments explaining complex guards
4. **Flat Structures**: Avoid deeply nested matches for clearer trees
5. **Naming Convention**: Use meaningful variable names in scrutinees

## Examples

See `examples/decision_trees.yh` for comprehensive examples:
- Liability assessment with fault types
- Criminal sentencing with multiple factors
- Contract validation with nested conditions
- Regulatory compliance decision trees
