# Logic engine 

* Heuristic evaluation
* Prime Implicant

> [!WARNING]
> FUA continue to add these in the future!

* Don’t Care Conditions
* Tautology
* SAT Solvers
* Multi-Level Minimization
* Factorization
* Complementation
* Boolean minimization in `prop_eval.py`

## Usage

```console
$ python3 learn.py
```

## Rationale

There are benefits to implementing a logic engine capable of heuristic and boolean minimization.  
By substituting truth values with statutory elements, complex statements evaluate to less complex ones and contradictions are easily identified.  

### Examples

<details>
<summary>
<h4>Simple examples</h4>
</summary>
<br>

```txt
"Driving while intoxicated" IS NOT NOT NOT NOT OFFENCE = "Driving while intoxicated" IS OFFENCE
```

```txt
"Carrying a concealed weapon" AND "Committing theft" IS OFFENCE = "Committing theft" IS OFFENCE AND "Carrying a concealed weapon" IS OFFENCE
```

```txt
"Entering the premises without permission" IF AND ONLY IF "Breaking a window" = "Breaking a window" -> "Entering the premises without permission"
```

```txt
NOT "Assaulting a police officer" IF AND ONLY IF "Acting in self-defense" = "Acting in self-defense" -> NOT "Assaulting a police officer"
```

```txt
"Selling prohibited substances" IS OFFENCE AND IS NOT OFFENCE = WRONGFUL_CLAIM: CONTRADICTION
```
</details>

> [!WARNING]
> Continue formatting and logicising the below examples to make sure readable

> [!WARNING]
> Continue adding examples below showing logical fallacies and other contradictions

> [!WARNING]
> Make every evaluated statement as atomic as possible, so should propositional formulas should evaluate to basic truth statements

<details>
<summary>
<h4>Complex examples</h4>
</summary>
<br>

```txt
("Driving while intoxicated" OR ("Committing vandalism" AND NOT "Paying damages")) IS OFFENCE IF AND ONLY IF (NOT "Providing false testimony" OR "Assisting in investigation") = ("Providing false testimony" -> ("Driving while intoxicated" OR ("Committing vandalism" AND NOT "Paying damages"))) AND (("Driving while intoxicated" OR ("Committing vandalism" AND NOT "Paying damages")) -> (NOT "Providing false testimony" OR "Assisting in investigation"))
```

```txt
((NOT "Trespassing" AND "Breaking a window") OR ("Carrying a concealed weapon" AND NOT "Fleeing from the scene")) IS OFFENCE AND (NOT "Committing theft" IF "Breaking a window") IS OFFENCE = 
((NOT "Trespassing" AND "Breaking a window") OR ("Carrying a concealed weapon" AND NOT "Fleeing from the scene")) IS OFFENCE AND ("Breaking a window" -> NOT "Committing theft") IS OFFENCE
```

```txt
("Fraud" OR (NOT "Embezzlement" AND ("Bribery" OR NOT "Tax evasion"))) AND ("Obstruction of justice" OR (NOT "Tax evasion" AND "Perjury")) IS OFFENCE IF AND ONLY IF (NOT "Obstruction of justice" OR "Cooperation with authorities") = ((("Fraud" OR (NOT "Embezzlement" AND ("Bribery" OR NOT "Tax evasion"))) AND ("Obstruction of justice" OR (NOT "Tax evasion" AND "Perjury"))) -> (NOT "Obstruction of justice" OR "Cooperation with authorities")) AND ((NOT "Obstruction of justice" OR "Cooperation with authorities") -> (("Fraud" OR (NOT "Embezzlement" AND ("Bribery" OR NOT "Tax evasion"))) AND ("Obstruction of justice" OR (NOT "Tax evasion" AND "Perjury"))))
```

```txt
(("Forgery" AND "Counterfeiting") OR NOT ("Breaking and entering" AND "Vandalism")) IF "Being an accomplice" IS OFFENCE AND ("Conspiracy" IF "Murder") IS OFFENCE = ("Being an accomplice" -> (("Forgery" AND "Counterfeiting") OR NOT ("Breaking and entering" AND "Vandalism"))) IS OFFENCE AND ("Murder" -> "Conspiracy") IS OFFENCE
```

```txt
NOT (("Money laundering" AND "Identity theft") OR ("Fraud" AND NOT "Forgery")) IS OFFENCE IF ("Assault" AND "Battery") IS NOT OFFENCE = ("Assault" AND "Battery") -> NOT (("Money laundering" AND "Identity theft") OR ("Fraud" AND NOT "Forgery")) IS OFFENCE
```
</details>

> [!WARNING]
> CCLaw talk from today notes
> 
> UK Courts and Drafters have for years talked about the movement from SHALL to MUST
>   MUST: currently used in consequence of breach
>   
> * DSLs need to account for the nuances between SHALL and MUST
> * What is a necessary compulsary consequence, what is a possible consequence
> * DSL needs keywords like ACT, POLICY, REFERENCE, PER, LEGISLATE, INCLUSIVE IF, EXCLUSIVE IF 
> * Must account for the inclusion of common law and obiter
> * Must account for the inclusion of policy and statute
> * DSL must be easy to read and to write
> * Structure matters
> * if and boolean connectives
> * add syntax for error checking like WRONGFUL and RIGHTFUL errors and specification of how an error is wrongful or rightful
> * validation for a given equation 
> 
> * basic inconsitency checking and testing facilities for DSLs
> * DSL must include a syntax to define a given thing recursively
> * give me an IDE that has some autocomplete and linting
> * make the linting and snippets comprehensive
> * DSLs must account for subsidiary legislation as well
> * definitions need to be recursive
> 
> If person must wear seatbelt and they don't, they're in breach of the provision, but could that be interpreted differently
> 
> FUA
>   * also consider changing my code font to iosevka
>   * how can we integrate LLMs that then produce yuho code
>   * https://boostdraft.com