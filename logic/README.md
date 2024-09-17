# Logic evaluation

* Boolean minimization in `prop_eval.py`

## Usage

```console
$ python3 learn.py
```

## Rationale

There are benefits to implementing a logic engine capable of heuristic and boolean minimization.  
By substituting truth values with statutory elements, complex statements evaluate to less complex ones and contradictions are easily identified.  

### Examples

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