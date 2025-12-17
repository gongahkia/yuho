# Conflict Detection Example

This example demonstrates Yuho's conflict detection system using simplified versions of the Singapore Contract Act and Consumer Protection Act.

## Files

- `contract_act.yh` - Contract law definitions
- `consumer_protection.yh` - Consumer protection definitions
- `main.yh` - Main file with conflict check

## Running the Example

```bash
yuho check main.yh
```

## Expected Output

The conflict detector will identify that `ContractValidity` enum has conflicting definitions:
- Contract Act uses: `Valid`, `Void`, `Voidable`
- Consumer Protection uses: `Enforceable`, `Unenforceable`

## Real-World Application

In practice, this type of conflict detection helps:
1. Ensure consistency across related statutes
2. Identify where laws need harmonization
3. Detect unintentional contradictions in legal codes
4. Support legal code refactoring and consolidation

## Resolving the Conflict

To resolve this conflict, you could:

### Option 1: Unify the Enums

Use a single shared enum definition:

```yuho
enum ContractValidity {
    Valid,
    Void,
    Voidable,
    Enforceable,
    Unenforceable,
}
```

### Option 2: Use Different Names

Rename the enums to reflect their specific context:

```yuho
// contract_act.yh
enum GeneralContractValidity { ... }

// consumer_protection.yh
enum ConsumerContractEnforceability { ... }
```

### Option 3: Use Type Aliases

Map one to the other if they're semantically equivalent:

```yuho
// consumer_protection.yh
type ContractValidity := GeneralContractValidity
```
