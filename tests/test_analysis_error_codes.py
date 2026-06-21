"""Analysis error-code stability tests."""

from __future__ import annotations

import re

from yuho.services.analysis import ANALYSIS_ERROR_CODES, analyze_file, analyze_source


def test_analysis_error_code_catalog_is_unique_y_codes() -> None:
    codes = list(ANALYSIS_ERROR_CODES.values())

    assert len(codes) == len(set(codes))
    assert all(re.fullmatch(r"Y\d{4}", code) for code in codes)


def test_file_not_found_uses_stable_error_code() -> None:
    result = analyze_file("/no/such/file.yh")

    assert result.errors[0].error_code == "Y0001"
    assert result.diagnostics()[0]["error_code"] == "Y0001"


def test_null_bytes_use_stable_error_code() -> None:
    result = analyze_source("hello\x00world")

    assert result.errors[0].error_code == "Y0006"
    assert result.diagnostics()[0]["error_code"] == "Y0006"


def test_parse_diagnostics_use_stable_error_codes() -> None:
    result = analyze_source("fn broken( {", run_semantic=False)
    codes = {diagnostic["error_code"] for diagnostic in result.diagnostics()}

    assert codes
    assert all(re.fullmatch(r"Y\d{4}", code) for code in codes)
