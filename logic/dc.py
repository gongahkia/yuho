# NOTE
    # just a module file

def dont_care_conditions(truth_table, variables, dont_care):
    """
    handles don't care conditions 
    in the generated truth table
    
    parameters:
    * truth_table (list of dicts): generated truth table
    * variables (list): list of variables used in the propositional formula
    * dont_care (list of dicts): list of don't care conditions
    
    returns:
    * list of dicts: truth table with don't care conditions handled
    """
    for row in truth_table:
        if any(all(row[var] == dc[var] for var in variables) for dc in dont_care):
            row['Result'] = None
    return truth_table