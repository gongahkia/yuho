// Integration tests for conflict detection

use yuho_check::conflict_detection::*;
use yuho_core::parse;

#[test]
fn test_no_conflicts_empty_programs() {
    let mut detector = ConflictDetector::new();

    let prog1 = parse("").unwrap();
    let prog2 = parse("").unwrap();

    detector.add_program("file1.yh".to_string(), prog1);
    detector.add_program("file2.yh".to_string(), prog2);

    let report = detector.check_conflict("file1.yh", "file2.yh");
    assert!(report.is_none());
}

#[test]
fn test_enum_conflict_different_variants() {
    let mut detector = ConflictDetector::new();

    let source1 = r#"
        enum Status {
            Active,
            Inactive,
        }
    "#;

    let source2 = r#"
        enum Status {
            Running,
            Stopped,
        }
    "#;

    let prog1 = parse(source1).unwrap();
    let prog2 = parse(source2).unwrap();

    detector.add_program("file1.yh".to_string(), prog1);
    detector.add_program("file2.yh".to_string(), prog2);

    let report = detector.check_conflict("file1.yh", "file2.yh");
    assert!(report.is_some());

    let report = report.unwrap();
    assert_eq!(report.conflicts.len(), 1);
    assert!(report.conflicts[0].description.contains("Status"));
    assert!(report.conflicts[0].description.contains("conflicting"));
}

#[test]
fn test_no_conflict_same_enum_different_files() {
    let mut detector = ConflictDetector::new();

    let source1 = r#"
        enum Color {
            Red,
            Green,
            Blue,
        }
    "#;

    let source2 = r#"
        enum Color {
            Red,
            Green,
            Blue,
        }
    "#;

    let prog1 = parse(source1).unwrap();
    let prog2 = parse(source2).unwrap();

    detector.add_program("file1.yh".to_string(), prog1);
    detector.add_program("file2.yh".to_string(), prog2);

    let report = detector.check_conflict("file1.yh", "file2.yh");
    // Same definition should not conflict
    assert!(report.is_none());
}

#[test]
fn test_struct_conflict() {
    let mut detector = ConflictDetector::new();

    let source1 = r#"
        struct Person {
            string name,
            int age,
        }
    "#;

    let source2 = r#"
        struct Person {
            string full_name,
            date birthdate,
        }
    "#;

    let prog1 = parse(source1).unwrap();
    let prog2 = parse(source2).unwrap();

    detector.add_program("file1.yh".to_string(), prog1);
    detector.add_program("file2.yh".to_string(), prog2);

    let report = detector.check_conflict("file1.yh", "file2.yh");
    assert!(report.is_some());

    let report = report.unwrap();
    assert_eq!(report.conflicts.len(), 1);
    assert!(report.conflicts[0].description.contains("Person"));
}

#[test]
fn test_report_formatting() {
    let mut detector = ConflictDetector::new();

    let source1 = r#"
        enum Verdict {
            Guilty,
            NotGuilty,
        }
    "#;

    let source2 = r#"
        enum Verdict {
            Convicted,
            Acquitted,
        }
    "#;

    let prog1 = parse(source1).unwrap();
    let prog2 = parse(source2).unwrap();

    detector.add_program("statute1.yh".to_string(), prog1);
    detector.add_program("statute2.yh".to_string(), prog2);

    let report = detector.check_conflict("statute1.yh", "statute2.yh");
    assert!(report.is_some());

    let report = report.unwrap();
    let formatted = report.format();

    assert!(formatted.contains("CONFLICT REPORT"));
    assert!(formatted.contains("statute1.yh"));
    assert!(formatted.contains("statute2.yh"));
    assert!(formatted.contains("Verdict"));
    assert!(formatted.contains("Conflicts found: 1"));
}

#[test]
fn test_report_json_export() {
    let mut detector = ConflictDetector::new();

    let source1 = r#"enum Status { A, B }"#;
    let source2 = r#"enum Status { C, D }"#;

    let prog1 = parse(source1).unwrap();
    let prog2 = parse(source2).unwrap();

    detector.add_program("f1.yh".to_string(), prog1);
    detector.add_program("f2.yh".to_string(), prog2);

    let report = detector.check_conflict("f1.yh", "f2.yh");
    assert!(report.is_some());

    let report = report.unwrap();
    let json = report.to_json();

    assert!(json.contains(r#""file1":"f1.yh""#));
    assert!(json.contains(r#""file2":"f2.yh""#));
    assert!(json.contains(r#""conflict_count":1"#));
}

#[test]
fn test_legal_test_conflict() {
    let mut detector = ConflictDetector::new();

    let source1 = r#"
        legal_test Fraud {
            requires deception: bool,
            requires damage: bool,
        }
    "#;

    let source2 = r#"
        legal_test Fraud {
            requires lying: bool,
            requires harm: bool,
            requires intent: bool,
        }
    "#;

    let prog1 = parse(source1).unwrap();
    let prog2 = parse(source2).unwrap();

    detector.add_program("file1.yh".to_string(), prog1);
    detector.add_program("file2.yh".to_string(), prog2);

    let report = detector.check_conflict("file1.yh", "file2.yh");
    assert!(report.is_some());

    let report = report.unwrap();
    assert_eq!(report.conflicts.len(), 1);
    assert!(report.conflicts[0].description.contains("Fraud"));
    assert!(report.conflicts[0].description.contains("requirements"));
}

#[test]
fn test_multiple_conflicts() {
    let mut detector = ConflictDetector::new();

    let source1 = r#"
        enum Status { A, B }
        struct Person { string name }
    "#;

    let source2 = r#"
        enum Status { C, D }
        struct Person { int id }
    "#;

    let prog1 = parse(source1).unwrap();
    let prog2 = parse(source2).unwrap();

    detector.add_program("file1.yh".to_string(), prog1);
    detector.add_program("file2.yh".to_string(), prog2);

    let report = detector.check_conflict("file1.yh", "file2.yh");
    assert!(report.is_some());

    let report = report.unwrap();
    assert_eq!(report.conflicts.len(), 2); // Both Status and Person conflict
}
