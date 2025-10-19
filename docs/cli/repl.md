# REPL (Read-Eval-Print Loop)

The `yuho-repl` command starts an interactive Yuho shell for experimentation and development.

## Overview

The Yuho REPL provides:

- **Interactive Development** - Test code snippets immediately
- **Syntax Validation** - Check code as you type
- **Output Generation** - Generate Mermaid and Alloy from code
- **Learning Tool** - Experiment with Yuho syntax

## Starting the REPL

### Basic Usage

```bash
yuho-repl
```

### Example Session

```bash
$ yuho-repl
yuho> struct Person { string name, int age }
✓ Valid Yuho code

yuho> Person alice := { name := "Alice", age := 25 }
✓ Valid Yuho code

yuho> match alice.age { case 25 := consequence "age 25"; case _ := consequence "other age"; }
✓ Valid Yuho code

yuho> help
[Shows REPL commands]

yuho> exit
```

## REPL Commands

### `help`

Show available REPL commands:

```bash
yuho> help
Available commands:
  help     - Show this help message
  history  - Show command history
  clear    - Clear screen
  load     - Load and parse a file
  mermaid  - Generate Mermaid from last input
  alloy    - Generate Alloy from last input
  exit     - Exit REPL
  quit     - Exit REPL
```

### `history`

Show command history:

```bash
yuho> history
1: struct Person { string name, int age }
2: Person alice := { name := "Alice", age := 25 }
3: match alice.age { case 25 := consequence "age 25"; case _ := consequence "other age"; }
4: help
```

### `clear`

Clear the screen:

```bash
yuho> clear
[Screen cleared]
```

### `load <file>`

Load and parse a Yuho file:

```bash
yuho> load examples/cheating/cheating_illustration_A.yh
✓ Successfully loaded examples/cheating/cheating_illustration_A.yh
```

### `mermaid`

Generate Mermaid diagram from last input:

```bash
yuho> struct Cheating { bool deception, bool dishonest, bool harm }
✓ Valid Yuho code

yuho> mermaid
flowchart TD
    S0[Cheating]
    S0 --> M1[deception: bool]
    S0 --> M2[dishonest: bool]
    S0 --> M3[harm: bool]
```

### `alloy`

Generate Alloy specification from last input:

```bash
yuho> struct Cheating { bool deception, bool dishonest, bool harm }
✓ Valid Yuho code

yuho> alloy
// Generated Alloy specification from Yuho
module YuhoGenerated

abstract sig Bool {}
one sig True, False extends Bool {}

sig Cheating {
  deception: Bool,
  dishonest: Bool,
  harm: Bool
}

run {} for 5
```

### `exit` / `quit`

Exit the REPL:

```bash
yuho> exit
Goodbye!
```

## Interactive Development

### Step 1: Define Structs

```bash
yuho> struct Person { string name, int age, bool isMinor }
✓ Valid Yuho code
```

### Step 2: Create Instances

```bash
yuho> Person alice := { name := "Alice", age := 25, isMinor := FALSE }
✓ Valid Yuho code
```

### Step 3: Add Logic

```bash
yuho> match alice.isMinor { case TRUE := consequence "juvenile"; case FALSE := consequence "adult"; }
✓ Valid Yuho code
```

### Step 4: Generate Outputs

```bash
yuho> mermaid
[Shows Mermaid diagram]

yuho> alloy
[Shows Alloy specification]
```

## Legal Examples

### Example 1: Cheating Offense

```bash
yuho> struct Cheating { bool deception, bool dishonest, bool harm }
✓ Valid Yuho code

yuho> Cheating case1 := { deception := TRUE, dishonest := TRUE, harm := TRUE }
✓ Valid Yuho code

yuho> match { case case1.deception && case1.dishonest && case1.harm := consequence "guilty"; case _ := consequence "not guilty"; }
✓ Valid Yuho code

yuho> mermaid
flowchart TD
    S0[Cheating]
    S0 --> M1[deception: bool]
    S0 --> M2[dishonest: bool]
    S0 --> M3[harm: bool]
    MC4{Decision}
    MC4 --> C5[Case 1]
    C5 --> CO6[Consequence: guilty]
```

### Example 2: Theft Offense

```bash
yuho> struct Theft { bool dishonestIntention, bool movableProperty, bool withoutConsent, bool movedProperty }
✓ Valid Yuho code

yuho> Theft case1 := { dishonestIntention := TRUE, movableProperty := TRUE, withoutConsent := TRUE, movedProperty := TRUE }
✓ Valid Yuho code

yuho> match { case case1.dishonestIntention && case1.movableProperty && case1.withoutConsent && case1.movedProperty := consequence "guilty of theft"; case _ := consequence "not guilty of theft"; }
✓ Valid Yuho code

yuho> alloy
// Generated Alloy specification from Yuho
module YuhoGenerated

abstract sig Bool {}
one sig True, False extends Bool {}

sig Theft {
  dishonestIntention: Bool,
  movableProperty: Bool,
  withoutConsent: Bool,
  movedProperty: Bool
}

pred MatchCase0[x: univ] {
  (dishonestIntention = True and movableProperty = True and withoutConsent = True and movedProperty = True) => {
    // Consequence: guilty of theft
  }
}

run {} for 5
```

### Example 3: Age-Based Logic

```bash
yuho> int age := 25
✓ Valid Yuho code

yuho> match age { case 18 := consequence "just became adult"; case 21 := consequence "legal drinking age"; case 65 := consequence "retirement age"; case _ := consequence "other age"; }
✓ Valid Yuho code

yuho> mermaid
flowchart TD
    S0[age: int]
    MC1{Decision}
    MC1 --> C2[Case 1]
    MC1 --> C3[Case 2]
    MC1 --> C4[Case 3]
    MC1 --> C5[Default]
    C2 --> CO6[Consequence: just became adult]
    C3 --> CO7[Consequence: legal drinking age]
    C4 --> CO8[Consequence: retirement age]
    C5 --> CO9[Consequence: other age]
```

## Advanced Usage

### Working with Files

```bash
yuho> load examples/cheating/cheating_illustration_A.yh
✓ Successfully loaded examples/cheating/cheating_illustration_A.yh

yuho> mermaid
[Shows Mermaid diagram from loaded file]

yuho> alloy
[Shows Alloy specification from loaded file]
```

### Complex Legal Logic

```bash
yuho> struct LegalCase { string caseNumber, bool isGuilty, money penalty }
✓ Valid Yuho code

yuho> LegalCase case1 := { caseNumber := "CR-2024-001", isGuilty := TRUE, penalty := $1000.00 }
✓ Valid Yuho code

yuho> match case1.isGuilty { case TRUE := consequence "guilty"; case FALSE := consequence "not guilty"; }
✓ Valid Yuho code

yuho> match case1.penalty { case penalty > $500.00 := consequence "high penalty"; case _ := consequence "low penalty"; }
✓ Valid Yuho code
```

### Function Development

```bash
yuho> bool func isEligible(int age) { match age { case 18 := consequence TRUE; case _ := consequence FALSE; } }
✓ Valid Yuho code

yuho> bool result := isEligible(25)
✓ Valid Yuho code

yuho> match result { case TRUE := consequence "eligible"; case FALSE := consequence "not eligible"; }
✓ Valid Yuho code
```

## Best Practices

### 1. Start Simple

```bash
# Start with basic structs
yuho> struct Person { string name, int age }
✓ Valid Yuho code

# Add complexity gradually
yuho> Person alice := { name := "Alice", age := 25 }
✓ Valid Yuho code
```

### 2. Test Incrementally

```bash
# Test each piece
yuho> struct Cheating { bool deception, bool dishonest, bool harm }
✓ Valid Yuho code

# Add logic step by step
yuho> match { case deception && dishonest && harm := consequence "guilty"; case _ := consequence "not guilty"; }
✓ Valid Yuho code
```

### 3. Use Help Commands

```bash
yuho> help
[Shows available commands]

yuho> history
[Shows command history]
```

### 4. Generate Outputs

```bash
yuho> mermaid
[Generate Mermaid diagram]

yuho> alloy
[Generate Alloy specification]
```

## Troubleshooting

### Common Issues

#### Issue 1: Syntax Errors

```bash
yuho> struct Person { string name, int age
✗ Error: Syntax error at line 1: expected '}' but found end of input
```

**Solution**: Fix syntax:

```bash
yuho> struct Person { string name, int age }
✓ Valid Yuho code
```

#### Issue 2: Type Errors

```bash
yuho> int age := "25"
✗ Error: Type mismatch: expected 'int' but found 'string'
```

**Solution**: Use correct types:

```bash
yuho> int age := 25
✓ Valid Yuho code
```

#### Issue 3: Undefined Variables

```bash
yuho> match age { case 25 := consequence "age 25"; case _ := consequence "other age"; }
✗ Error: Variable 'age' not defined
```

**Solution**: Define variable first:

```bash
yuho> int age := 25
✓ Valid Yuho code

yuho> match age { case 25 := consequence "age 25"; case _ := consequence "other age"; }
✓ Valid Yuho code
```

## Performance

### REPL Speed

Typical response times:

| Operation | Time |
|-----------|------|
| Simple struct | <10ms |
| Complex logic | <50ms |
| Mermaid generation | <100ms |
| Alloy generation | <200ms |

### Optimization Tips

1. **Use simple commands** for quick testing
2. **Generate outputs** only when needed
3. **Clear history** periodically
4. **Exit and restart** for fresh session

## Integration with Development

### Development Workflow

```bash
# Start REPL
yuho-repl

# Experiment with code
yuho> struct Test { bool field }
yuho> Test instance := { field := TRUE }
yuho> match instance.field { case TRUE := consequence "true"; case FALSE := consequence "false"; }

# Generate outputs
yuho> mermaid
yuho> alloy

# Exit and save to file
yuho> exit
```

### Learning Workflow

```bash
# Start REPL
yuho-repl

# Learn syntax
yuho> help
yuho> struct Person { string name, int age }
yuho> Person alice := { name := "Alice", age := 25 }

# Experiment with logic
yuho> match alice.age { case 25 := consequence "age 25"; case _ := consequence "other age"; }

# Generate visualizations
yuho> mermaid
yuho> alloy

# Exit
yuho> exit
```

## Next Steps

- [Check Command](check.md) - Validate code from REPL
- [Draw Command](draw.md) - Generate diagrams from files
- [Alloy Command](alloy.md) - Generate Alloy specifications
- [Draft Command](draft.md) - Create new Yuho files
