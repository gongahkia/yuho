# NOTE
    # this is code that is not intended, and should never enter into production
    # for learning how to write a basic version of a Conflict-Driven Clause Learning (CDCL) SAT solver that features
        # conflict analysis
        # clause learning
        # non-chronological backtracking

from collections import defaultdict

class CDCLSolver:

    def __init__(self, clauses):
        self.clauses = clauses
        self.num_vars = len(set(abs(literal) for clause in clauses for literal in clause))
        self.assignment = {}  # variable assignments
        self.decision_level = {}  # decision levels
        self.watched_literals = defaultdict(list)  # 2 watched literals for each clause
        self.reason = {}  # reasoning clause for each variable's assignment
        self.decision_stack = []  # stack of decisions to afford backtracking
        self.learned_clauses = []  # clauses learnt from conflicts
        self.conflicts = 0  # number of conflicts

    def solve(self):
        """
        main function to solve the SAT problem 
        using CDCL, that returns a satisfying assignment 
        as a dict if SAT, returns None if UNSAT.k
        """
        for i, clause in enumerate(self.clauses):
            if len(clause) > 0:
                self.watched_literals[clause[0]].append(i)
                if len(clause) > 1:
                    self.watched_literals[clause[1]].append(i)
        while True:
            conflict_clause = self.unit_propagation()
            if conflict_clause:
                if len(self.decision_stack) == 0:
                    return None 
                backtrack_level, learned_clause = self.analyze_conflict(conflict_clause)
                self.learned_clauses.append(learned_clause)
                self.backtrack(backtrack_level)
                self.add_learned_clause(learned_clause)
            else:
                if len(self.assignment) == self.num_vars:
                    return self.assignment  # SAT
                decision_var = self.pick_variable()
                self.decision_stack.append((decision_var, len(self.assignment)))
                self.assign(decision_var, True)

    def unit_propagation(self):
        """
        performs unit propagation, where if a clause 
        becomes unit, then assign the value to the 
        variable, and returns the conflicting clause 
        if there's a conflict, otherwise returns None
        """
        while True:
            unit_clauses = []
            for clause in self.clauses + self.learned_clauses:
                unassigned_literals = [lit for lit in clause if abs(lit) not in self.assignment]
                satisfied = any(self.assignment.get(abs(lit), False) == (lit > 0) for lit in clause)
                if not satisfied:
                    if len(unassigned_literals) == 1:  
                        unit_clauses.append(unassigned_literals[0])
                    elif len(unassigned_literals) == 0:  
                        return clause  
            if len(unit_clauses) == 0:
                break  
            for lit in unit_clauses:
                self.assign(abs(lit), lit > 0)
        return None  

    def analyze_conflict(self, conflict_clause):
        """
        analyzes the conflict and 
        learns a new clause, then 
        returns the backtrack level 
        and the learned clause
        """
        learned_clause = []
        seen_vars = set()
        backtrack_level = 0
        for literal in conflict_clause:
            var = abs(literal)
            if var in self.assignment and self.decision_level[var] > backtrack_level:
                backtrack_level = self.decision_level[var]
            if var not in seen_vars:
                learned_clause.append(literal if self.assignment[var] else -literal)
                seen_vars.add(var)
        learned_clause.sort(key=lambda lit: self.decision_level[abs(lit)], reverse=True)
        if len(learned_clause) > 1:
            backtrack_level = self.decision_level[abs(learned_clause[1])]
        else:
            backtrack_level = 0
        return backtrack_level, learned_clause

    def backtrack(self, level):
        """
        performs backtracking to a 
        given decision level
        """
        while self.decision_stack and self.decision_stack[-1][1] > level:
            var, _ = self.decision_stack.pop()
            del self.assignment[var]
            del self.decision_level[var]

    def assign(self, var, value):
        """
        assigns a variable a specified 
        Boolean value, either True or 
        False
        """
        self.assignment[var] = value
        self.decision_level[var] = len(self.decision_stack)

    def add_learned_clause(self, clause):
        """
        adds the learned clause to the 
        clause set
        """
        self.clauses.append(clause)
        self.watched_literals[clause[0]].append(len(self.clauses) - 1)
        if len(clause) > 1:
            self.watched_literals[clause[1]].append(len(self.clauses) - 1)

    def pick_variable(self):
        """
        heuristic to pick the next 
        variable to assign
        """
        unassigned_vars = [var for var in range(1, self.num_vars + 1) if var not in self.assignment]
        return unassigned_vars[0] if unassigned_vars else None