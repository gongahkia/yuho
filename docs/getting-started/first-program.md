# Your First Yuho Program

This tutorial will guide you through writing your first Yuho program step by step.

## Hello, Yuho!

Let's start with a simple example that demonstrates the core concepts.

### Step 1: Create the File

Create a new file called `hello.yh`:

```bash
touch hello.yh
```

### Step 2: Define a Struct

Structs are Yuho's primary data structure. Let's define a simple person:

```yh
// Define a Person struct
struct Person {
    string name,
    int age,
    bool isStudent
}
```

### Step 3: Create Variables

Let's create some variables:

```yh
// Simple variable declarations
string greeting := "Hello, Yuho!";
int year := 2024;
bool learning := TRUE;
```

### Step 4: Add Logic with Match-Case

Yuho uses match-case for conditional logic:

```yh
// Check if learning
match {
    case learning == TRUE := consequence "Keep learning!";
    case _ := consequence "Start learning!";
}
```

### Step 5: Complete Program

Here's the complete `hello.yh`:

```yh
// Your first Yuho program

// Define a Person struct
struct Person {
    string name,
    int age,
    bool isStudent
}

// Create variables
string greeting := "Hello, Yuho!";
int year := 2024;
bool learning := TRUE;

// Conditional logic
match {
    case learning == TRUE := consequence "Keep learning!";
    case _ := consequence "Start learning!";
}
```

### Step 6: Check Your Program

Validate your program:

```bash
yuho check hello.yh
```

Expected output:
```
✓ Syntax check passed
✓ Semantic check passed
✓ hello.yh looks good!
```

### Step 7: Visualize Your Program

Generate a flowchart:

```bash
yuho draw hello.yh --format flowchart -o hello_flow.mmd
```

Generate a mindmap:

```bash
yuho draw hello.yh --format mindmap -o hello_mind.mmd
```

## Understanding the Concepts

### Structs

Structs define custom data types with named fields:

```yh
struct StructName {
    type fieldName,
    type anotherField
}
```

### Variables

Variables are declared with type and immutably assigned:

```yh
type variableName := value;
```

### Match-Case

Pattern matching for conditional logic:

```yh
match {
    case condition := consequence result;
    case _ := consequence defaultResult;
}
```

## A Legal Example

Let's create a more practical legal example in `theft.yh`:

```yh
// Simple representation of theft offense

struct Theft {
    string accused,
    string property,
    bool dishonest,
    bool movable,
    bool withoutConsent
}

// Define the logical requirements
match {
    case dishonest && movable && withoutConsent :=
        consequence "guilty of theft";
    case dishonest && movable :=
        consequence "additional investigation required";
    case _ :=
        consequence "not guilty of theft";
}
```

Check this program:

```bash
yuho check theft.yh
yuho draw theft.yh -f flowchart -o theft.mmd
```

## Common Patterns

### Boolean Logic

```yh
bool conditionA := TRUE;
bool conditionB := FALSE;

match {
    case conditionA && conditionB := consequence "Both true";
    case conditionA || conditionB := consequence "At least one true";
    case _ := consequence "Both false";
}
```

### Numeric Comparisons

```yh
int age := 25;

match {
    case age >= 18 := consequence "Adult";
    case age >= 13 := consequence "Teenager";
    case _ := consequence "Child";
}
```

### Multiple Conditions

```yh
bool cond1 := TRUE;
bool cond2 := TRUE;
bool cond3 := FALSE;

match {
    case cond1 && cond2 && cond3 := consequence "All true";
    case cond1 && cond2 := consequence "First two true";
    case cond1 := consequence "Only first true";
    case _ := consequence "None or other combinations";
}
```

## Next Steps

Now that you've written your first Yuho program:

1. [Learn more about syntax](../language/syntax.md)
2. [Explore Yuho types](../language/types.md)
3. [Master match-case patterns](../language/match-case.md)
4. [See real examples](../examples/criminal-law.md)

## Exercises

Try these exercises to practice:

1. Create a struct representing a contract with relevant fields
2. Write a match-case that checks multiple conditions
3. Generate both flowchart and mindmap for your program
4. Experiment with different types (money, date, duration)

## Troubleshooting

### Syntax Errors

Common mistakes:

```yh
// Wrong: Using = instead of :=
int x = 42;  // ❌

// Correct:
int x := 42;  // ✓

// Wrong: Missing semicolon
int y := 10  // ❌

// Correct:
int y := 10;  // ✓

// Wrong: Wrong struct syntax
struct Test {
    string name: "value"  // ❌
}

// Correct:
struct Test {
    string name  // ✓
}
```

### Type Errors

```yh
// Wrong: Type mismatch
int x := "string";  // ❌

// Correct:
int x := 42;  // ✓
string s := "string";  // ✓
```

## Resources

- [Language Reference](../language/overview.md)
- [CLI Commands](../cli/commands.md)
- [More Examples](../examples/patterns.md)

