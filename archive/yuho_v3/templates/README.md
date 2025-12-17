# Yuho Legal Contract Templates

This directory contains practical, production-ready legal contract templates for Singapore law, written in the Yuho DSL.

## Structure

```
templates/
├── employment/         # Employment contracts
├── confidentiality/    # NDAs and confidentiality agreements
├── services/          # Service agreements
├── property/          # Property and tenancy agreements
└── corporate/         # Corporate agreements
```

## Available Templates

### Employment Contracts

- **full_time_employment.yh** - MOM-compliant full-time employment contract
  - `FullTimeEmploymentContract` - Standard permanent/contract employment
  - `ProbationaryEmploymentContract` - Employment with probation period
  - MOM compliance checks (working hours, leave, CPF, salary payment)
  - Examples: Software Engineer, Graduate Trainee

**Key Features:**
- Employment Act compliance (Cap 91)
- Automatic CPF calculations
- Annual leave minimum (Section 43)
- Medical leave provisions (Section 89)
- Working hours limits (Part IV)
- Salary payment within 7 days

### Non-Disclosure Agreements (NDAs)

- **nda_mutual.yh** - Mutual and Unilateral NDA templates
  - `MutualNDA` - Both parties exchange confidential information
  - `UnilateralNDA` - One party discloses to another
  - Standard exclusions (public domain, already known, etc.)
  - Remedies (specific performance, injunction, liquidated damages)
  - Examples: Tech Partnership, Investor Due Diligence, Employee NDA

**Key Features:**
- Confidentiality period (2-10 years)
- Return of materials obligation
- Non-solicitation clauses (optional)
- Permitted disclosures to employees/advisors
- Singapore law governing clauses

### Service Agreements

- **consulting_agreement.yh** - Professional consulting services
  - `ConsultingServicesAgreement` - General consulting template
  - `SoftwareDevelopmentAgreement` - Extends consulting for software projects
  - `ProfessionalServicesRetainer` - Retainer-based services
  - Payment structures (hourly, daily, monthly, milestone, retainer)
  - Examples: IT Consulting, Web App Development, Legal Retainer

- **saas_agreement.yh** - Software as a Service subscriptions
  - `SaaSAgreement` - Complete SaaS subscription template
  - PDPA compliance and data protection
  - Service level agreements (SLA) with uptime guarantees
  - Examples: Project Management SaaS, Enterprise CRM

**Key Features:**
- Independent contractor status and tax obligations
- IP ownership options (client, consultant, joint, license)
- Professional indemnity requirements
- PDPA compliance for data processing
- Security breach notification (72-hour requirement)
- Service level agreements and uptime guarantees
- Data ownership and encryption requirements

### Property and Tenancy Agreements

- **tenancy_agreement.yh** - Residential tenancy agreements
  - `ResidentialTenancyAgreement` - Full tenancy contract
  - `RoomRentalAgreement` - Simplified room rental
  - Property types (HDB, condo, landed, room)
  - Examples: Condo Tenancy, HDB Tenancy, Room Rental

- **option_to_purchase.yh** - Property sale transactions
  - `OptionToPurchase` - OTP for property purchases
  - `SaleAndPurchaseAgreement` - Full SPA after OTP exercise
  - Option fee (1%) and exercise amount (4-5%)
  - Examples: Condo OTP, HDB Resale OTP

**Key Features:**
- Security deposit rules (1-3 months for tenancy)
- Stamp duty requirements
- HDB minimum occupation period (MOP) compliance
- Utilities and maintenance responsibilities
- Diplomatic clause for early termination
- CPF usage tracking for purchases
- Completion timeline (8-12 weeks standard)
- Caveat rights for purchaser

### Corporate Agreements

- **shareholders_agreement.yh** - Shareholders agreements
  - `ShareholdersAgreement` - Complete shareholders agreement
  - Reserved matters and supermajority voting
  - Transfer restrictions (ROFR, ROFO, tag-along, drag-along)
  - Examples: Tech Startup, Investment with Investor Rights

- **distribution_agreement.yh** - Distribution and agency agreements
  - `DistributionAgreement` - Distribution and sales agency
  - Exclusive and non-exclusive arrangements
  - Tiered commission structures
  - Examples: Electronics Distribution, Sales Agent

**Key Features:**
- Pre-emptive rights protection
- Board composition and director appointment rights
- Reserved matters requiring supermajority (75%+)
- Good leaver / bad leaver provisions
- Deadlock resolution mechanisms
- Territory exclusivity (Singapore, SEA, APAC, Worldwide)
- Sales targets and performance requirements
- Marketing fund contributions

## Usage

Import templates into your Yuho files:

```yuho
import templates.employment.full_time_employment
import templates.confidentiality.nda_mutual

// Use or extend the templates
example MyEmploymentContract := FullTimeEmploymentContract {
    employer_name: "My Company Pte Ltd",
    employee_name: "John Doe",
    // ... fill in details
}

example MyNDA := MutualNDA {
    party1_name: "Company A",
    party2_name: "Company B",
    // ... fill in details
}
```

## Customization

All templates are designed to be extended:

```yuho
// Extend employment contract with custom clauses
struct EmploymentWithIPAssignment extends FullTimeEmploymentContract {
    bool ip_assignment_clause where ip_assignment_clause == true,
    string ip_assignment_description,

    // Add custom restrictions
    bool non_compete_clause,
    optional BoundedInt<1, 2> non_compete_years
}
```

## Compliance

All templates include:

1. **Proper Citations** - `@citation` annotations to relevant statutes
2. **Compliance Checks** - `principle` statements verifying legal requirements
3. **Type Safety** - BoundedInt, Positive types ensure valid ranges
4. **Working Examples** - Concrete instances demonstrating usage

### Employment Contract Compliance

- ✅ Employment Act (Cap 91)
- ✅ Ministry of Manpower (MOM) regulations
- ✅ CPF contributions
- ✅ Working hours limits
- ✅ Leave entitlements

### NDA Compliance

- ✅ Singapore Contract Law
- ✅ Trade secrets protection
- ✅ Equitable remedies
- ✅ Reasonable restraint of trade

### Service Agreement Compliance

- ✅ Independent contractor status (not employment)
- ✅ IP ownership clarity
- ✅ PDPA compliance for SaaS
- ✅ Professional indemnity requirements
- ✅ Service level agreements (SLA)

### Property Agreement Compliance

- ✅ Stamp duty requirements
- ✅ HDB eligibility and MOP
- ✅ Security deposit limits
- ✅ CPF usage tracking
- ✅ Landlord-tenant obligations

### Corporate Agreement Compliance

- ✅ Companies Act (Cap 50)
- ✅ Pre-emptive rights protection
- ✅ Reserved matters supermajority
- ✅ Transfer restrictions (ROFR, tag-along, drag-along)
- ✅ Deadlock resolution mechanisms

## Validation

Test a template:

```bash
yuho check templates/employment/full_time_employment.yh
yuho transpile templates/employment/full_time_employment.yh --target typescript
```

## Legal Notice

**IMPORTANT:** These templates are for educational and development purposes. They model Singapore law but are not a substitute for professional legal advice. Always:

1. Have templates reviewed by qualified Singapore lawyers
2. Customize for your specific circumstances
3. Ensure compliance with latest statutory requirements
4. Consult legal professionals for actual contracts

## Future Enhancements

### Potential Future Templates

- **Commercial Property**
  - Commercial lease agreements
  - Industrial tenancy
  - Office space rental

- **Additional Corporate**
  - Joint venture agreements
  - Licensing agreements
  - Franchise agreements

- **Specialized Agreements**
  - Assignment of IP
  - Settlement agreements
  - Loan agreements

## Contributing

To add new templates:

1. Follow the existing structure
2. Include proper `@citation` annotations
3. Add at least one working example
4. Document compliance principles
5. Test with `yuho check`

## License

MIT License - see root LICENSE file
