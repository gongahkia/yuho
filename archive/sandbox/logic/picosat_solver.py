# NOTE
    # this is code that is not intended, and should never enter into production
    # for learning how to quickly implement a basic version of a PicoSAT solver in Python

import picosat

class PicoSATWrapper:

    def __init__(self, clauses, num_vars):
        self.clauses = clauses  # list of clauses, where each clause is a list of integers as literals
        self.num_vars = num_vars  # number of variables

    def solve(self):
        """
        solves the SAT problem using PicoSAT
        via a Python library, returning a 
        satisfying assignment if the problem is SAT
        and returning None if not
        """
        solver = picosat.init()
        for clause in self.clauses:
            picosat.add(solver, clause)
        result = picosat.solve(solver)
        if result == picosat.SAT:
            solution = picosat.deref(solver, self.num_vars)
            picosat.reset(solver)
            return solution
        else:
            picosat.reset(solver)
            return None