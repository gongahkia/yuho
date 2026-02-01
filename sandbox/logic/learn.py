# NOTE
    # this is code that is not intended, and should never enter into production
    # for learning 
        # how to generate truth tables
        # carry out heuristic minimization

import eval as e
import minimize as m

if __name__ == "__main__":

    variables = ["A", "B", "C", "D"]
    custom_formula = "(A∧¬B)∨(C⊕D)"

    truth_table = e.generate_truth_table(variables)
    print("Truth Table for Basic Propositional Formulas with Multiple Variables")
    e.display_truth_table(truth_table, variables)
    print(f"Evaluating the custom formula {custom_formula}")
    truth_table_custom = e.evaluate_formula(custom_formula, variables)
    e.display_truth_table_custom(truth_table_custom, variables)
    minimized_result = m.single_level_minimization(custom_formula, variables)
    print("\nMinimized formula result:", minimized_result)