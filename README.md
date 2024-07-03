![](https://img.shields.io/badge/yuho_1.0-WIP-orange)

> [!WARNING]
> To see what's currently being worked, see [napkin.txt](napkin.txt).

# `yuho`

Yuho is a functional domain-specific language providing a programmatic representation of Singapore Criminal Law.

## Rationale

> to add here

## Scope

Development is currently scoped by the [Penal Code 1871](https://sso.agc.gov.sg/Act/PC1871).

The below are covered.

1. **Penal Code (Chapter 224)** - Defines criminal offenses and penalties.

The below are not covered.

2. **Criminal Procedure Code (Chapter 68)** - Governs the procedure for criminal justice.
3. **Misuse of Drugs Act (Chapter 185)** - Addresses drug-related offenses.
4. **Women’s Charter (Chapter 353)** - Protects women and children, including provisions on family violence.
5. **Protection from Harassment Act (Chapter 256A)** - Deals with harassment and anti-social behavior.
6. **Kidnapping Act (Chapter 151)** - Covers kidnapping and abduction offenses.
7. **Sedition Act (Chapter 290)** - Addresses seditious acts, speech, and publications.
8. **Official Secrets Act (Chapter 213)** - Protects state secrets and official information.
9. **Vandalism Act (Chapter 341)** - Addresses vandalism and property defacement.
10. **Corruption, Drug Trafficking and Other Serious Crimes (Confiscation of Benefits) Act (Chapter 65A)** - Provides for the confiscation of benefits from serious crimes.
11. **Prevention of Corruption Act (Chapter 241)** - Addresses corruption offenses.
12. **Public Order Act (Chapter 257A)** - Governs public order and assemblies.
13. **Societies Act (Chapter 311)** - Regulates societies and associations.
14. **Internal Security Act (Chapter 143)** - Addresses national security and preventive detention.
15. **Moneylenders Act (Chapter 188)** - Regulates moneylending activities.
16. **Gambling Control Act 2022** - Governs gambling activities.
17. **Remote Gambling Act (Chapter 269A)** - Regulates remote gambling.
18. **Casino Control Act (Chapter 33A)** - Regulates casinos and gambling.
19. **Undesirable Publications Act (Chapter 338)** - Addresses undesirable publications.
20. **Terrorism (Suppression of Financing) Act (Chapter 325)** - Addresses terrorism financing.
21. **Extradition Act (Chapter 103)** - Governs extradition of offenders.
22. **Mutual Assistance in Criminal Matters Act (Chapter 190A)** - Provides for mutual legal assistance in criminal matters.
23. **Computer Misuse Act (Chapter 50A)** - Addresses cybercrimes and computer misuse.
24. **Strategic Goods (Control) Act (Chapter 300)** - Controls the transfer of strategic goods.
25. **Enlistment Act (Chapter 93)** - Governs national service and enlistment.
26. **Road Traffic Act (Chapter 276)** - Governs road traffic offenses.
27. **Liquor Control (Supply and Consumption) Act 2015** - Regulates liquor supply and consumption.
28. **Employment of Foreign Manpower Act (Chapter 91A)** - Regulates employment of foreign workers.
29. **Immigration Act (Chapter 133)** - Governs immigration offenses.
30. **Passports Act (Chapter 220)** - Governs passport-related offenses.
31. **Public Entertainments Act (Chapter 257)** - Regulates public entertainments.
32. **Films Act (Chapter 107)** - Governs film distribution and exhibition.
33. **Broadcasting Act (Chapter 28)** - Regulates broadcasting services.
34. **Public Order and Safety (Special Powers) Act 2018** - Provides special powers for public order and safety.
35. **Terrorism (Suppression of Bombings) Act (Chapter 324A)** - Addresses terrorism bombings.
36. **Terrorism (Suppression of Maritime Navigation) Act (Chapter 324B)** - Addresses maritime terrorism.
37. **Coroners Act (Chapter 63A)** - Governs coronial investigations.
38. **Registration of Criminals Act (Chapter 268)** - Regulates the registration of criminals.
39. **Minor Offences Act (Chapter 184)** - Governs minor offenses.
40. **Maritime and Port Authority of Singapore Act (Chapter 170A)** - Regulates maritime and port activities.
41. **Merchant Shipping Act (Chapter 179)** - Governs merchant shipping and related offenses.
42. **International Child Abduction Act (Chapter 143C)** - Addresses international child abduction.
43. **International Transfer of Prisoners Act (Chapter 183B)** - Governs the transfer of prisoners between countries.

## Documentation

* [Grammer specification](grammer)
* [Language specification](doc/syntax.md)
* [Example](example)

## Usage

### CLI 

```console
$ git clone https://github.com/gongahkia/yuho
$ cd yuho  
$ make config
$ make build
```

## Contribute

Yuho is open-source. Contribution guidelines are found at [CONTRIBUTING.md](CONTRIBUTING.md).

## References

### Analogues

Yuho takes inspiration from the following projects.

* [Catala](https://github.com/CatalaLang): Language syntax that explicitly mimicks logical structure of the Law, focused on general Socio-fiscal legislature in most jurisidictions.
* [Natural L4](https://github.com/smucclaw/dsl): Language with an English-like syntax that transpiles to multiple targets, focused on codification of contracts and Singapore Contract Law.
* [Blawx](https://github.com/Lexpedite/blawx): User-friendly web-based tool for Rules as Code, a declarative logic knowledge representation tool for encoding, testing and using rules.
* [Morphir](https://github.com/finos/morphir): Technology agnostic toolkit for digitisation of business models and their underlying decision logic, enabling automation in fintech.

### Research

* [A Logic for Statutes](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3088206) by Sarah B Lawsky
* [Symbolic and automatic differentiation of languages](https://dl.acm.org/doi/10.1145/3473583) by Conal Elliott
* [Legal Rules, Legal Reasoning, and Nonmonotonic Logic](https://philpapers.org/rec/RIGLRL-2) by Adam W Rigoni
* [Law and logic: A review from an argumentation perspective](https://www.sciencedirect.com/science/article/pii/S0004370215000910) by Henry Prakken, Giovanni Sartor
* [Defeasible semantics for L4](https://ink.library.smu.edu.sg/cclaw/5/) by Guido Governatori, Meng Weng Wong
* [CLAWs and Effect](https://www.lawsociety.org.sg/publication/claws-and-effect/) by Alexis N Chun
