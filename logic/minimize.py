# NOTE
    # this is code that is not intended, and should never enter into production
    # for learning how to write boolean and heuristic minimization and other optimizations

import eval as e
import prime as p

def single_level_minimization(formula, variables):
    """
    carry out basic boolean minimization 
    on the specified propositional formula 
    by applying the generated truth table
    
    parameters:
    * formula (str): propositional formula to evaluate and minimize
    * variables (list): list of variables used in the propositional formula

    returns:
    * str: minimized propositonal formula based on logical equivalence
    """
    truth_table = e.evaluate_formula(formula, variables)
    all_true = all(row['Result'] for row in truth_table)
    all_false = all(not row['Result'] for row in truth_table)
    if all_true:
        return "TRUE (tautology)"
    elif all_false:
        return "FALSE (contradiction)"
    return "the formula CANNOT be further minimized"

def multi_level_minimization(truth_table, variables):
    """
    perform multi-level minimization 
    on the propositional formula
    
    parameters:
    * truth_table (list of dicts): generated truth table
    * variables (list): list of variables used in the propositional formula
    
    returns:
    * str: minimized multi-level propositional formula
    """
    prime_imps = p.prime_implicants(truth_table, variables)
    if not prime_imps:
        return "FALSE"
    return " AND ".join([" OR ".join(imp) for imp in prime_imps])

def heuristic_minimization(truth_table, variables):
    """
    heuristically minimize the 
    propositional formula by 
    identifying redundant terms
    
    parameters:
    * truth_table (list of dicts): generated truth table
    * variables (list): list of variables used in the propositional formula
    
    returns:
    * str: minimized boolean expression using heuristic methods
    """
    prime_imps = p.prime_implicants(truth_table, variables)
    essential_terms = [imp for imp in prime_imps if not any(other_imp != imp and set(imp).issubset(set(other_imp)) for other_imp in prime_imps)]
    if not essential_terms:
        return "FALSE"
    return " AND ".join([" OR ".join(imp) for imp in essential_terms])