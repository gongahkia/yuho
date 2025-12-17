// Comprehensive tests for legal_test feature (Legal Condition Chains)

use yuho_core::ast::*;
use yuho_core::{lex, parse};

#[test]
fn test_parse_simple_legal_test() {
    let source = r#"
        legal_test Cheating {
            requires deception: bool,
            requires dishonest_intent: bool,
        }
    "#;

    let program = parse(source).expect("Failed to parse legal_test");

    assert_eq!(program.items.len(), 1);

    if let Item::LegalTest(test) = &program.items[0] {
        assert_eq!(test.name, "Cheating");
        assert_eq!(test.requirements.len(), 2);

        assert_eq!(test.requirements[0].name, "deception");
        assert!(matches!(test.requirements[0].ty, Type::Bool));

        assert_eq!(test.requirements[1].name, "dishonest_intent");
        assert!(matches!(test.requirements[1].ty, Type::Bool));
    } else {
        panic!("Expected LegalTest item");
    }
}

#[test]
fn test_parse_empty_legal_test() {
    let source = r#"
        legal_test EmptyTest {
        }
    "#;

    let program = parse(source).expect("Failed to parse empty legal_test");

    if let Item::LegalTest(test) = &program.items[0] {
        assert_eq!(test.name, "EmptyTest");
        assert_eq!(test.requirements.len(), 0);
    } else {
        panic!("Expected LegalTest item");
    }
}

#[test]
fn test_parse_legal_test_with_many_requirements() {
    let source = r#"
        legal_test ComplexOffense {
            requires element_one: bool,
            requires element_two: bool,
            requires element_three: bool,
            requires element_four: bool,
            requires element_five: bool,
        }
    "#;

    let program = parse(source).expect("Failed to parse complex legal_test");

    if let Item::LegalTest(test) = &program.items[0] {
        assert_eq!(test.name, "ComplexOffense");
        assert_eq!(test.requirements.len(), 5);

        for req in &test.requirements {
            assert!(matches!(req.ty, Type::Bool));
        }
    } else {
        panic!("Expected LegalTest item");
    }
}

#[test]
fn test_parse_satisfies_pattern() {
    let source = r#"
        string verdict := match case {
            case satisfies Cheating := "guilty"
            case _ := "not guilty"
        }
    "#;

    let program = parse(source).expect("Failed to parse satisfies pattern");

    assert_eq!(program.items.len(), 1);

    if let Item::Declaration(decl) = &program.items[0] {
        if let Expr::Match(m) = &decl.value {
            assert_eq!(m.cases.len(), 2);

            // First case should be satisfies pattern
            if let Pattern::Satisfies(test_name) = &m.cases[0].pattern {
                assert_eq!(test_name, "Cheating");
            } else {
                panic!("Expected Satisfies pattern");
            }

            // Second case should be wildcard
            assert!(matches!(m.cases[1].pattern, Pattern::Wildcard));
        } else {
            panic!("Expected Match expression");
        }
    } else {
        panic!("Expected Declaration item");
    }
}

#[test]
fn test_parse_legal_test_with_satisfies_usage() {
    let source = r#"
        legal_test Theft {
            requires taking: bool,
            requires without_consent: bool,
            requires dishonest_intent: bool,
        }

        match offense {
            case satisfies Theft := "guilty of theft"
            case _ := "not guilty"
        }
    "#;

    let program = parse(source).expect("Failed to parse legal_test with usage");

    assert_eq!(program.items.len(), 2);

    // First item should be legal_test
    assert!(matches!(program.items[0], Item::LegalTest(_)));

    // Second item should be declaration with match
    if let Item::Declaration(decl) = &program.items[1] {
        if let Expr::Match(m) = &decl.value {
            if let Pattern::Satisfies(test_name) = &m.cases[0].pattern {
                assert_eq!(test_name, "Theft");
            } else {
                panic!("Expected Satisfies pattern");
            }
        } else {
            panic!("Expected Match expression");
        }
    } else {
        panic!("Expected Declaration item");
    }
}

#[test]
fn test_legal_test_keywords_lexing() {
    let source = "legal_test requires satisfies";
    let tokens = lex(source);

    // Should have 3 tokens (no EOF in yuho lexer)
    assert_eq!(tokens.len(), 3);

    assert!(matches!(tokens[0].0, yuho_core::Token::LegalTest));
    assert!(matches!(tokens[1].0, yuho_core::Token::Requires));
    assert!(matches!(tokens[2].0, yuho_core::Token::Satisfies));
}

#[test]
fn test_multiple_legal_tests_in_scope() {
    let source = r#"
        scope criminal_law {
            legal_test Murder {
                requires killing: bool,
                requires malice_aforethought: bool,
            }

            legal_test Manslaughter {
                requires killing: bool,
                requires lack_of_malice: bool,
            }
        }
    "#;

    let program = parse(source).expect("Failed to parse multiple legal_tests");

    if let Item::Scope(scope) = &program.items[0] {
        assert_eq!(scope.items.len(), 2);

        // Both items should be legal tests
        assert!(matches!(scope.items[0], Item::LegalTest(_)));
        assert!(matches!(scope.items[1], Item::LegalTest(_)));

        if let Item::LegalTest(test1) = &scope.items[0] {
            assert_eq!(test1.name, "Murder");
            assert_eq!(test1.requirements.len(), 2);
        }

        if let Item::LegalTest(test2) = &scope.items[1] {
            assert_eq!(test2.name, "Manslaughter");
            assert_eq!(test2.requirements.len(), 2);
        }
    } else {
        panic!("Expected Scope item");
    }
}

#[test]
fn test_legal_test_trailing_comma() {
    let source = r#"
        legal_test Test {
            requires a: bool,
            requires b: bool,
        }
    "#;

    let program = parse(source).expect("Failed to parse legal_test with trailing comma");

    if let Item::LegalTest(test) = &program.items[0] {
        assert_eq!(test.requirements.len(), 2);
    } else {
        panic!("Expected LegalTest item");
    }
}

#[test]
fn test_legal_test_no_trailing_comma() {
    let source = r#"
        legal_test Test {
            requires a: bool,
            requires b: bool
        }
    "#;

    let program = parse(source).expect("Failed to parse legal_test without trailing comma");

    if let Item::LegalTest(test) = &program.items[0] {
        assert_eq!(test.requirements.len(), 2);
    } else {
        panic!("Expected LegalTest item");
    }
}

#[test]
fn test_satisfies_in_nested_match() {
    let source = r#"
        match outer {
            case x := match inner {
                case satisfies Test := "pass"
                case _ := "fail"
            }
            case _ := "default"
        }
    "#;

    let program = parse(source).expect("Failed to parse nested match with satisfies");

    if let Item::Declaration(decl) = &program.items[0] {
        if let Expr::Match(outer_match) = &decl.value {
            if let Expr::Match(inner_match) = &outer_match.cases[0].consequence {
                if let Pattern::Satisfies(test_name) = &inner_match.cases[0].pattern {
                    assert_eq!(test_name, "Test");
                } else {
                    panic!("Expected Satisfies pattern in inner match");
                }
            } else {
                panic!("Expected Match in consequence");
            }
        } else {
            panic!("Expected outer Match");
        }
    } else {
        panic!("Expected Declaration");
    }
}
