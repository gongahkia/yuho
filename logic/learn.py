# NOTE
    # this is code that is not intended, and should never enter into production
    # for learning 
        # how to generate truth tables
        # carry out heuristic minimization

import prop_eval as p

if __name__ == "__main__":

    variables = ["A", "B", "C"]
    custom_formula = "A ∨ (¬B ∧ C)"

    truth_table = p.generate_truth_table(variables)
    print("Truth Table for Basic Propositional Formulas with Multiple Variables:")
    p.display_truth_table(truth_table, variables)
    print("---")
    print(f"Evaluating custom formula: {custom_formula}")
    truth_table_custom = p.evaluate_formula(custom_formula, variables)
    p.display_truth_table_custom(truth_table_custom, variables)
    minimized_result = p.minimize_formula(custom_formula, variables)
    print("\nMinimized formula result:", minimized_result)