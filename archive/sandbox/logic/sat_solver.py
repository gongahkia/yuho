# NOTE
    # this is code that is not intended, and should never enter into production
    # for learning the logic behind basic SAT solvers by writing them

import random
from itertools import product

def basic_sat_solver(truth_table):
    """
    simple SAT solver to check 
    if the propositional formula is 
    satisfiable
    
    parameters:
    * truth_table (list of dicts): generated truth table
    
    returns:
    * bool: True if the propositional formula is satisfiable, False if not
    """
    return any(row['Result'] for row in truth_table)

def brute_force_sat_solver(formula, variables):
    """
    brute-force SAT solver that evaluates 
    the propositional formula for all 
    possible combinations of variables
    
    parameters:
    * formula (str): propositional formula to evaluate
    * variables (list): list of variables used in the propositional formula
    
    returns:
    * dict or None: a satisfying assignment (dict) if one exists, or None if the propositional formula is unsatisfiable
    """
    formula = formula.replace('¬', 'not ').replace('∧', ' and ').replace('∨', ' or ')
    formula = formula.replace('⊕', ' != ').replace('→', ' <= ').replace('↔', ' == ')
    for values in product([False, True], repeat=len(variables)):
        assignment = dict(zip(variables, values))
        if eval(formula, {}, assignment):
            return assignment 
    return None 

def dpll_solver(clauses, assignment={}):
    """
    DPLL SAT solver that applies 
    unit propagation and pure 
    literal elimination 
    
    parameters:
    * clauses (list of lists): CNF propositional formula as a list of clauses
    * assignment (dict): current variable assignments
    
    returns:
    * dict or None: a satisfying assignment if one exists, or None if unsatisfiable
    """
    if all(any(literal in assignment and assignment[abs(literal)] == (literal > 0) for literal in clause) for clause in clauses):
        return assignment
    if any(all(literal in assignment and assignment[abs(literal)] == (literal < 0) for literal in clause) for clause in clauses):
        return None
    unit_clauses = [clause for clause in clauses if len(clause) == 1]
    if unit_clauses:
        unit = unit_clauses[0][0]
        assignment[abs(unit)] = (unit > 0)
        return dpll_solver(clauses, assignment)
    all_literals = [literal for clause in clauses for literal in clause]
    for literal in set(all_literals):
        if -literal not in all_literals:
            assignment[abs(literal)] = (literal > 0)
            return dpll_solver(clauses, assignment)
    variable = abs(next(literal for clause in clauses for literal in clause if literal not in assignment))
    assignment_copy = assignment.copy()
    assignment_copy[variable] = True
    result = dpll_solver(clauses, assignment_copy)
    if result is not None:
        return result
    assignment[variable] = False
    return dpll_solver(clauses, assignment)

def walk_sat(clauses, max_flips=1000, p=0.5):
    """
    WalkSAT, a SAT solver that 
    conducts a randomized local 
    search 
    
    parameters:
    * clauses (list of lists): CNF propositional formula as a list of clauses
    * max_flips (int): maximum number of flips before giving up
    * p (float): probability of randomly flipping a variable
    
    returns:
    * dict or None: a satisfying assignment if found, otherwise None
    """
    variables = list(set(abs(literal) for clause in clauses for literal in clause))
    assignment = {var: random.choice([True, False]) for var in variables}
    for _ in range(max_flips):
        unsatisfied_clauses = [clause for clause in clauses if not any(assignment[abs(literal)] == (literal > 0) for literal in clause)]
        if not unsatisfied_clauses:
            return assignment 
        clause = random.choice(unsatisfied_clauses)
        if random.random() < p:
            var_to_flip = abs(random.choice(clause))
        else:
            def score(var):
                return sum(any((literal == var) == assignment[abs(literal)] for literal in c) for c in clauses)
            var_to_flip = max(clause, key=lambda v: score(abs(v)))
        assignment[var_to_flip] = not assignment[var_to_flip]
    return None 