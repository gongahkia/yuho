# NOTE
    # just a module file

def prime_implicants(truth_table, variables):
    """
    identifies prime implicants from the 
    generated truth table
    
    parameters:
    * truth_table (list of dicts): generated truth table with variable assignments and results
    * variables (list): list of variables used in the propositional formula
    
    returns:
    * list: prime implicants in terms of variables
    """
    implicants = []
    for row in truth_table:
        if row['Result']:
            term = []
            for var in variables:
                if row[var]:
                    term.append(var)
                else:
                    term.append(f'¬{var}')
            implicants.append(term)
    return implicants