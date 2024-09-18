# Logic evaluation 

* Boolean minimization in `prop_eval.py`

> [!WARNING]
> Continue to add these functions in Python to this file directory in the future
>
> 4. SAT Solvers
> 5. Multi-Level Minimization
> 6. Factorization
> 7. Complementation
> 8. Heuristic minimzation
> 9. Add further examples of wrongful Yuho logic soon

## Usage

```console
$ python3 learn.py
```

## Rationale
  
There are many benefits to implementing a logic engine capable of heuristic and boolean minimization.  
  
By substituting truth values with statutory elements, complex statements evaluate to less complex ones.   
  
### Rightful examples

Rightful formulas are minimized to their fundamental propositions.

| Complex | Minimized | More |
| :--- | :--- | :--- |
| `"Driving while intoxicated" IS NOT NOT NOT NOT OFFENCE` | `"Driving while intoxicated" IS OFFENCE` | NIL |
| `("Carrying a concealed weapon" AND "Committing theft") IS OFFENCE` | `"Committing theft" IS OFFENCE AND "Carrying a concealed weapon" IS OFFENCE` | NIL |
| `"Resisting arrest" AND NOT "Under the influence of alcohol" IS OFFENCE` | `"Resisting arrest" IS OFFENCE AND "Under the influence of alcohol" NOT OFFENCE` | NIL |
| `"Entering the premises without permission" IF AND ONLY IF "Breaking a window" ` | `"Breaking a window" THEN ONLY "Entering the premises without permission"` | Also minimized to `ONLY "Breaking a window" -> "Entering the premises without permission"` |
| `NOT "Assaulting a police officer" IF AND ONLY IF "Acting in self-defense"` |`"Acting in self-defense" THEN ONLY NOT "Assaulting a police officer"` | Also minimized to `ONLY "Acting in self-defense" -> NOT "Assaulting a police officer"` |
| `NOT ("Possessing stolen goods" AND "Fleeing from police") IF AND ONLY IF "Being innocent"` | `"Being innocent" THEN ONLY NOT "Possessing stolen goods" OR NOT "Fleeing from police"` | Also minimized to `ONLY "Being innocent" -> NOT "Posessing stolen goods" OR NOT "Fleeing from police"` |

### Wrongful examples

Wrongful formulas are flagged.

| Complex | Minimized | More |
| :--- | :--- | :--- |
| `"Selling prohibited substances" IS OFFENCE AND IS NOT OFFENCE` | ERROR | Flagged with `WRONGFUL: CONTRADICTION` |
| `"Selling prohibited substances" IS OFFENCE OR IS NOT OFFENCE` | ERROR | Flagged with `WRONGFUL: TAUTOLOGY` |
| `"Selling prohibited substances" IS OFFENCE IF "Selling prohibited substances IS OFFENCE` | ERROR | Flagged with `WRONGFUL: CIRCULAR_REASONING` |