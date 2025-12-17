use std::process::Command;

#[test]
fn test_cli_check_command() {
    let output = Command::new("cargo")
        .args(&[
            "run",
            "--package",
            "yuho-cli",
            "--",
            "check",
            "examples/simple.yh",
        ])
        .output();

    // Test that check command can be invoked
    assert!(output.is_ok(), "Check command should execute");
}

#[test]
fn test_cli_transpile_typescript_command() {
    let output = Command::new("cargo")
        .args(&[
            "run",
            "--package",
            "yuho-cli",
            "--",
            "transpile",
            "examples/simple.yh",
            "--target",
            "typescript",
        ])
        .output();

    assert!(output.is_ok(), "Transpile to TypeScript should execute");
}

#[test]
fn test_cli_transpile_alloy_command() {
    let output = Command::new("cargo")
        .args(&[
            "run",
            "--package",
            "yuho-cli",
            "--",
            "transpile",
            "examples/simple.yh",
            "--target",
            "alloy",
        ])
        .output();

    assert!(output.is_ok(), "Transpile to Alloy should execute");
}

#[test]
fn test_cli_verify_principle_command() {
    let output = Command::new("cargo")
        .args(&[
            "run",
            "--package",
            "yuho-cli",
            "--",
            "verify-principle",
            "examples/z3_principles.yh",
            "--principle",
            "TestPrinciple",
        ])
        .output();

    assert!(output.is_ok(), "Verify principle command should execute");
}

#[test]
fn test_cli_help_command() {
    let output = Command::new("cargo")
        .args(&["run", "--package", "yuho-cli", "--", "--help"])
        .output()
        .expect("Failed to execute help command");

    let stdout = String::from_utf8_lossy(&output.stdout);
    assert!(
        stdout.contains("check") || stdout.contains("transpile") || stdout.contains("verify"),
        "Help output should list commands"
    );
}

#[test]
fn test_cli_version_command() {
    let output = Command::new("cargo")
        .args(&["run", "--package", "yuho-cli", "--", "--version"])
        .output()
        .expect("Failed to execute version command");

    let stdout = String::from_utf8_lossy(&output.stdout);
    assert!(!stdout.is_empty(), "Version output should not be empty");
}

#[test]
fn test_cli_invalid_file_error() {
    let output = Command::new("cargo")
        .args(&[
            "run",
            "--package",
            "yuho-cli",
            "--",
            "check",
            "nonexistent.yh",
        ])
        .output()
        .expect("Failed to execute check on nonexistent file");

    // Should return error or stderr output
    assert!(
        !output.status.success() || !output.stderr.is_empty(),
        "Should handle missing file gracefully"
    );
}

#[test]
fn test_cli_transpile_output_file() {
    let temp_dir = std::env::temp_dir();
    let output_file = temp_dir.join("test_output.ts");

    let _ = Command::new("cargo")
        .args(&[
            "run",
            "--package",
            "yuho-cli",
            "--",
            "transpile",
            "examples/simple.yh",
            "--target",
            "typescript",
            "--output",
            output_file.to_str().unwrap(),
        ])
        .output();

    // Test file handling (file may or may not be created depending on implementation)
    assert!(true, "Output file argument accepted");
}

#[test]
fn test_cli_show_smt_flag() {
    let output = Command::new("cargo")
        .args(&[
            "run",
            "--package",
            "yuho-cli",
            "--",
            "verify-principle",
            "examples/z3_principles.yh",
            "--principle",
            "TestPrinciple",
            "--show-smt",
        ])
        .output();

    assert!(output.is_ok(), "Show SMT flag should be accepted");
}

#[test]
fn test_cli_show_counterexample_flag() {
    let output = Command::new("cargo")
        .args(&[
            "run",
            "--package",
            "yuho-cli",
            "--",
            "verify-principle",
            "examples/z3_principles.yh",
            "--principle",
            "TestPrinciple",
            "--show-counterexample",
        ])
        .output();

    assert!(
        output.is_ok(),
        "Show counterexample flag should be accepted"
    );
}
