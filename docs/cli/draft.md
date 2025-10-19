# Draft Command

The `yuho draft` command creates new Yuho file templates with basic structure.

## Overview

The `draft` command helps you get started with new Yuho files:

- **Template Generation** - Creates structured templates
- **Legal Context** - Includes legal documentation placeholders
- **Best Practices** - Follows Yuho coding standards
- **Quick Start** - Get coding immediately

## Basic Usage

```bash
yuho draft <struct_name> [OPTIONS]
```

### Examples

```bash
# Create template with default filename
yuho draft Cheating
# Creates: cheating.yh

# Create with custom filename
yuho draft Contract -o my_contract.yh

# Create for legal concept
yuho draft CriminalBreach -o criminal_breach.yh
```

## Command Options

### `--output`, `-o`

Specify output file path:

```bash
yuho draft Cheating -o custom_cheating.yh
```

**Default**: `<struct_name>.yh` (lowercase)

## Generated Template

### Basic Template Structure

```yh
// Yuho v3.0 - Generated template for StructName

struct StructName {
    // Add your fields here
    // Example:
    // accused: string,
    // action: string,
    // victim: string,
    // consequence: ConsequenceType,
}

// Add match-case logic here
// Example:
// match {
//     case condition := consequence result;
//     case _ := consequence pass;
// }
```

### Example: Cheating Template

```bash
yuho draft Cheating
```

**Generated File: `cheating.yh`**
```yh
// Yuho v3.0 - Generated template for Cheating

struct Cheating {
    // Add your fields here
    // Example:
    // accused: string,
    // action: string,
    // victim: string,
    // consequence: ConsequenceType,
}

// Add match-case logic here
// Example:
// match {
//     case condition := consequence result;
//     case _ := consequence pass;
// }
```

### Example: Custom Filename

```bash
yuho draft Theft -o theft_offense.yh
```

**Generated File: `theft_offense.yh`**
```yh
// Yuho v3.0 - Generated template for Theft

struct Theft {
    // Add your fields here
    // Example:
    // accused: string,
    // action: string,
    // victim: string,
    // consequence: ConsequenceType,
}

// Add match-case logic here
// Example:
// match {
//     case condition := consequence result;
//     case _ := consequence pass;
// }
```

## Customizing Templates

### Step 1: Add Legal Context

```yh
// Section 415 - Cheating
// Whoever, by deceiving any person, fraudulently or dishonestly...
struct Cheating {
    // Add your fields here
}
```

### Step 2: Define Struct Fields

```yh
struct Cheating {
    string accused,
    bool deception,
    bool dishonest,
    bool harm
}
```

### Step 3: Add Match-Case Logic

```yh
match {
    case deception && dishonest && harm :=
        consequence "guilty of cheating";
    case _ :=
        consequence "not guilty of cheating";
}
```

### Step 4: Add Variable Declarations

```yh
// Example case
Cheating case1 := {
    accused := "Alice",
    deception := TRUE,
    dishonest := TRUE,
    harm := TRUE
};
```

## Legal Examples

### Example 1: Cheating Offense

```bash
yuho draft Cheating -o cheating.yh
```

**Customized Template:**
```yh
// Section 415 - Cheating
// Whoever, by deceiving any person, fraudulently or dishonestly induces the person so deceived to deliver any property to any person, or to consent that any person shall retain any property, or intentionally induces the person so deceived to do or omit to do anything which he would not do or omit if he were not so deceived, and which act or omission causes or is likely to cause damage or harm to that person in body, mind, reputation or property, is said to "cheat".

struct Cheating {
    string accused,
    bool deception,
    bool dishonest,
    bool harm
}

// Example case
Cheating case1 := {
    accused := "Alice",
    deception := TRUE,
    dishonest := TRUE,
    harm := TRUE
};

match {
    case case1.deception && case1.dishonest && case1.harm :=
        consequence "guilty of cheating";
    case _ :=
        consequence "not guilty of cheating";
}
```

### Example 2: Theft Offense

```bash
yuho draft Theft -o theft.yh
```

**Customized Template:**
```yh
// Section 378 - Theft
// Whoever, intending to take dishonestly any movable property out of the possession of any person without that person's consent, moves that property in order to such taking, is said to commit theft.

struct Theft {
    string accused,
    bool dishonestIntention,
    bool movableProperty,
    bool withoutConsent,
    bool movedProperty
}

// Example case
Theft case1 := {
    accused := "Bob",
    dishonestIntention := TRUE,
    movableProperty := TRUE,
    withoutConsent := TRUE,
    movedProperty := TRUE
};

match {
    case case1.dishonestIntention && case1.movableProperty && 
         case1.withoutConsent && case1.movedProperty :=
        consequence "guilty of theft";
    case _ :=
        consequence "not guilty of theft";
}
```

### Example 3: Contract Formation

```bash
yuho draft Contract -o contract.yh
```

**Customized Template:**
```yh
// Contract Formation
// A contract is formed when there is offer, acceptance, and consideration.

struct Contract {
    string offeror,
    string offeree,
    bool offer,
    bool acceptance,
    bool consideration
}

// Example contract
Contract contract1 := {
    offeror := "Alice",
    offeree := "Bob",
    offer := TRUE,
    acceptance := TRUE,
    consideration := TRUE
};

match {
    case contract1.offer && contract1.acceptance && contract1.consideration :=
        consequence "contract formed";
    case _ :=
        consequence "no contract";
}
```

## Best Practices

### 1. Use Descriptive Struct Names

```bash
# Good: Clear legal context
yuho draft Cheating
yuho draft Theft
yuho draft Contract

# Avoid: Generic names
yuho draft Thing
yuho draft Stuff
yuho draft Example
```

### 2. Use Appropriate Filenames

```bash
# Good: Descriptive filenames
yuho draft Cheating -o cheating_offense.yh
yuho draft Theft -o theft_definition.yh
yuho draft Contract -o contract_formation.yh

# Avoid: Generic filenames
yuho draft Cheating -o example.yh
yuho draft Theft -o test.yh
```

### 3. Add Legal Context

```yh
// Always include legal source
// Section 415 - Cheating
struct Cheating {
    // struct definition
}
```

### 4. Follow Naming Conventions

```bash
# Good: PascalCase for struct names
yuho draft Cheating
yuho draft Theft
yuho draft Contract

# Good: snake_case for filenames
yuho draft Cheating -o cheating_offense.yh
yuho draft Theft -o theft_definition.yh
```

## Common Patterns

### Pattern 1: Criminal Offense

```bash
yuho draft CriminalOffense -o criminal_offense.yh
```

**Template Structure:**
```yh
struct CriminalOffense {
    string accused,
    string victim,
    bool actusReus,
    bool mensRea,
    string consequence
}
```

### Pattern 2: Civil Law

```bash
yuho draft CivilClaim -o civil_claim.yh
```

**Template Structure:**
```yh
struct CivilClaim {
    string plaintiff,
    string defendant,
    bool breach,
    bool damages,
    money amount
}
```

### Pattern 3: Contract Law

```bash
yuho draft Contract -o contract.yh
```

**Template Structure:**
```yh
struct Contract {
    string party1,
    string party2,
    bool offer,
    bool acceptance,
    bool consideration
}
```

## Workflow Integration

### Step 1: Create Template

```bash
yuho draft LegalConcept -o legal_concept.yh
```

### Step 2: Customize Template

```yh
// Add legal context
// Section XXX - Legal Concept
struct LegalConcept {
    // Add fields
    // Add logic
}
```

### Step 3: Validate

```bash
yuho check legal_concept.yh
```

### Step 4: Generate Outputs

```bash
# Generate diagrams
yuho draw legal_concept.yh -f flowchart -o legal_concept_flow.mmd
yuho draw legal_concept.yh -f mindmap -o legal_concept_mind.mmd

# Generate Alloy spec
yuho alloy legal_concept.yh -o legal_concept.als
```

## Troubleshooting

### Common Issues

#### Issue 1: Invalid Struct Name

```bash
$ yuho draft 123Invalid
✗ Error: Invalid struct name
```

**Solution**: Use valid identifier:

```bash
yuho draft ValidStruct
```

#### Issue 2: File Already Exists

```bash
$ yuho draft Cheating
✗ Error: File already exists: cheating.yh
```

**Solution**: Use different filename:

```bash
yuho draft Cheating -o new_cheating.yh
```

#### Issue 3: Permission Denied

```bash
$ yuho draft Cheating -o protected.yh
✗ Error: Permission denied: protected.yh
```

**Solution**: Check file permissions:

```bash
ls -la protected.yh
chmod 644 protected.yh
yuho draft Cheating -o protected.yh
```

## Advanced Usage

### Batch Template Creation

```bash
# Create multiple templates
yuho draft Cheating -o cheating.yh
yuho draft Theft -o theft.yh
yuho draft Contract -o contract.yh
yuho draft Tort -o tort.yh
```

### Template Customization

```bash
# Create template
yuho draft LegalConcept -o legal_concept.yh

# Customize with legal context
# Add Section reference
# Add legal definition
# Add example cases
```

### Integration with Development

```bash
# Create template
yuho draft Cheating -o cheating.yh

# Edit template
vim cheating.yh

# Validate
yuho check cheating.yh

# Generate outputs
yuho draw cheating.yh -f flowchart -o cheating_flow.mmd
yuho alloy cheating.yh -o cheating.als
```

## Performance

### Template Generation Speed

Typical generation times:

| Template Size | Time |
|---------------|------|
| Basic | <10ms |
| Complex | <50ms |
| Very Complex | <100ms |

### Optimization Tips

1. **Use descriptive names** for better organization
2. **Create templates in batches** for efficiency
3. **Customize templates** after generation
4. **Validate templates** before use

## Next Steps

- [Check Command](check.md) - Validate generated templates
- [Draw Command](draw.md) - Generate diagrams from templates
- [Alloy Command](alloy.md) - Generate Alloy specifications
- [REPL](repl.md) - Interactive development
