# NOTE
    # just a module file

def complement_formula(truth_table, variables):
    """
    generate the complement of 
    a given propositional formula 
    using the generated truth table
    
    parameters:
    * truth_table (list of dicts): generated truth table
    * variables (list): list of variables used in the propositional formula
    
    returns:
    * list of dicts: truth table for the complemented propositional formula
    """
    for row in truth_table:
        row['Result'] = not row['Result']
    return truth_table