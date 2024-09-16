from itertools import product
from functools import reduce

def generate_truth_table(variables):
    """
    generate a truth table for the 
    basic propositional formulas, works 
    with a variable number of parameters
    
    parameters:
    * variables (list): list of variables used in the propositional formula

    returns:
    * list of dicts: truth table represented as a list of dictionaries, where each dictionary contains variable assignments and results of the basic formulas
    """
    truth_table = []
    for values in product([False, True], repeat=len(variables)):
        assignment = dict(zip(variables, values))
        for var in variables:
            assignment[f'¬{var}'] = not assignment[var]
        assignment[' ∧ '.join(variables)] = reduce(lambda x, y: x and y, [assignment[var] for var in variables])
        assignment[' ∨ '.join(variables)] = reduce(lambda x, y: x or y, [assignment[var] for var in variables])
        assignment[' ⊕ '.join(variables)] = reduce(lambda x, y: x != y, [assignment[var] for var in variables])
        assignment[' → '.join(variables)] = reduce(lambda x, y: not x or y, [assignment[var] for var in variables])
        assignment[' ↔ '.join(variables)] = reduce(lambda x, y: x == y, [assignment[var] for var in variables])
        truth_table.append(assignment)
    return truth_table

def display_truth_table(truth_table, variables):
    """
    display the truth table in a readable format
    
    parameters:
    * truth_table (list of dicts): generated truth table with variable assignments and results
    * variables (list): list of variables used in the propositional formula
    """
    header = variables + [f'¬{var}' for var in variables] + \
             [' ∧ '.join(variables), ' ∨ '.join(variables), ' ⊕ '.join(variables), 
              ' → '.join(variables), ' ↔ '.join(variables)]
    print("\t".join(header))
    for row in truth_table:
        values = [str(int(row[var])) for var in variables]
        formulas = [str(int(row[formula])) for formula in header[len(variables):]]
        print("\t".join(values + formulas))

def display_truth_table_custom(truth_table, variables):
    """
    display the custom truth table in a readable format 
    
    parameters:
    * truth_table (list of dicts): generated truth table with variable assignments and the result
    * variables (list): list of variables used in the propositional formula
    """
    header = variables + ['Result']
    print("\t".join(header))
    for row in truth_table:
        values = [str(int(row[var])) for var in variables]
        result = str(int(row['Result']))
        print("\t".join(values + [result]))

def evaluate_formula(formula, variables):
    """
    evaluate a custom propositional formula 
    for all truth assignments of the given 
    variables
    
    parameters:
    * formula (str): propositional formula to evaluate using the symbols
    * variables (list): list of variables used in the formula

    returns:
    * list of dicts: truth table where each dictionary contains variable assignments and the result of the propositional formula
    """
    truth_table = []
    formula = formula.replace('¬', 'not ').replace('∧', ' and ').replace('∨', ' or ')
    formula = formula.replace('⊕', ' != ').replace('→', ' <= ').replace('↔', ' == ')
    for values in product([False, True], repeat=len(variables)):
        assignment = dict(zip(variables, values))
        eval_context = {var: assignment[var] for var in variables}
        assignment['Result'] = eval(formula, {}, eval_context)
        truth_table.append(assignment)
    return truth_table

def minimize_formula(formula, variables):
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
    truth_table = evaluate_formula(formula, variables)
    all_true = all(row['Result'] for row in truth_table)
    all_false = all(not row['Result'] for row in truth_table)
    if all_true:
        return "TRUE (tautology)"
    elif all_false:
        return "FALSE (contradiction)"
    return "the formula CANNOT be further minimized"