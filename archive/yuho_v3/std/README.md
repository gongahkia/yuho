# Yuho Standard Library for Singapore Law

This directory contains the Yuho standard library - a comprehensive collection of Singapore legal provisions modeled in the Yuho DSL.

## Structure

```
std/
├── criminal/           # Criminal law
│   ├── penal_code_cheating.yh
│   ├── penal_code_theft.yh
│   └── ...
├── contracts/          # Contract law
│   ├── contract_formation.yh
│   ├── remedies.yh
│   └── ...
├── property/           # Property law
├── torts/              # Tort law
└── constitutional/     # Constitutional law
```

## Usage

Import modules from the standard library in your Yuho files:

```yuho
import std.criminal.penal_code_cheating
import std.contracts.contract_formation

// Use the imported types and tests
example MyCase := CheatingOffense {
    // ... your case details
}
```

## Criminal Law

### Penal Code

- **penal_code_cheating.yh** - Section 415: Cheating
  - `CheatingOffense` struct
  - `legal_test Cheating`
  - Principles and examples

- **penal_code_theft.yh** - Sections 378, 380: Theft
  - `TheftOffense` struct
  - `TheftInDwellingHouse` (Section 380)
  - `legal_test Theft`
  - Principles and examples

- **penal_code_assault.yh** - Sections 351-358: Assault and Criminal Force
  - `AssaultOffense` and `CriminalForceOffense` structs
  - `VoluntarilyCausingHurt` (Section 323)
  - `VoluntarilyCausingGrievousHurt` (Section 325)
  - Distinction between assault and criminal force

### Evidence Act

- **evidence_act_admissibility.yh** - Admissibility of Evidence
  - Documentary, digital, and expert evidence types
  - Confession voluntariness requirements
  - Hearsay and relevance principles
  - Chain of custody tracking

## Contract Law

### Formation

- **contract_formation.yh** - Contract formation principles
  - `Contract` struct
  - `Offer`, `Acceptance`, `Consideration` structs
  - `legal_test ValidContract`
  - Principles for valid contract formation

### Remedies

- **remedies.yh** - Remedies for breach of contract
  - Damages (direct, consequential, liquidated)
  - Specific performance
  - Injunctions
  - Mitigation and remoteness principles

### Misrepresentation

- **misrepresentation.yh** - Fraudulent, negligent, and innocent misrepresentation
  - Elements of misrepresentation
  - Remedies (rescission and damages)
  - Bars to rescission

## Property Law

- **land_titles.yh** - Land Titles Act
  - Indefeasibility of title (Section 46)
  - Caveats and their effects
  - Freehold vs leasehold tenure
  - HDB flat ownership restrictions
  - Property sale and purchase transactions

## Tort Law

- **negligence.yh** - Law of Negligence
  - Duty of care (Spandeck test)
  - Standard of care (Bolam test for professionals)
  - Causation (but-for and remoteness)
  - Damages and contributory negligence

- **defamation.yh** - Defamation (libel and slander)
  - Elements of defamation
  - Defenses: justification, fair comment, qualified privilege
  - Offer of amends (Section 7 Defamation Act)
  - Remedies and damages

## Constitutional Law

- **fundamental_liberties.yh** - Part IV of the Constitution
  - Liberty of person (Article 9)
  - Equality before law (Article 12)
  - Freedom of speech, assembly, association (Article 14)
  - Freedom of religion (Article 15)
  - Preventive detention (Article 149)

- **judicial_review.yh** - Judicial Review of Administrative Action
  - Grounds: illegality, irrationality, procedural impropriety, unconstitutionality
  - Prerogative orders (mandatory, prohibiting, quashing)
  - Natural justice and ultra vires principles

## Features

Each module includes:

1. **Structs** - Model legal entities (offenses, contracts, etc.)
2. **Legal Tests** - Encode elements of offenses/validity
3. **Examples** - Concrete instances demonstrating usage
4. **Principles** - Fundamental legal principles encoded formally
5. **Citations** - Links to actual statutes and precedents

## Validation

All standard library modules:
- ✅ Type-check correctly
- ✅ Include proper citations
- ✅ Follow Singapore law accurately
- ✅ Include working examples
- ✅ Document legal principles

## Testing

Test a standard library module:

```bash
yuho check std/criminal/penal_code_cheating.yh
yuho transpile std/criminal/penal_code_cheating.yh --target typescript
```

## Contributing

To add new modules:

1. Follow the existing structure
2. Include proper `@citation` annotations
3. Add at least one working example
4. Document key principles
5. Test with `yuho check`

## Legal Accuracy

**IMPORTANT:** This standard library is for educational and development purposes. It models Singapore law but is not a substitute for professional legal advice. Always consult qualified legal professionals for actual legal matters.

## License

MIT License - see root LICENSE file
