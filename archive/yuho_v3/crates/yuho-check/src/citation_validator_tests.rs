#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_valid_section() {
        let validator = CitationValidator::new();
        assert!(validator.validate_section("415", "Penal Code").is_ok());
        assert!(validator.validate_section("1", "Contract Act").is_ok());
        assert!(validator.validate_section("415A", "Penal Code").is_ok());
    }

    #[test]
    fn test_invalid_section() {
        let validator = CitationValidator::new();
        assert!(validator.validate_section("", "Penal Code").is_err());
        assert!(validator.validate_section("ABC", "Penal Code").is_err());
        assert!(validator.validate_section("99999", "Penal Code").is_err());
    }

    #[test]
    fn test_valid_subsection() {
        let validator = CitationValidator::new();
        assert!(validator.validate_subsection("", "415", "Penal Code").is_ok());
        assert!(validator.validate_subsection("1", "415", "Penal Code").is_ok());
        assert!(validator.validate_subsection("a", "415", "Penal Code").is_ok());
        assert!(validator.validate_subsection("1a", "415", "Penal Code").is_ok());
    }

    #[test]
    fn test_invalid_subsection() {
        let validator = CitationValidator::new();
        assert!(validator.validate_subsection("@#$", "415", "Penal Code").is_err());
        assert!(validator.validate_subsection("!invalid", "415", "Penal Code").is_err());
    }
}
