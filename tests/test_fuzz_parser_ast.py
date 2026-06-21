from __future__ import annotations

from scripts.fuzz_parser_ast import fuzz_one_input


def test_fuzz_one_input_ignores_malformed_parse_inputs():
    for payload in (
        b"",
        b"\x00\xff\xfe",
        b"struct {",
        b'statute 1 "Broken" { elements { actus_reus',
    ):
        fuzz_one_input(payload)


def test_fuzz_one_input_builds_ast_for_valid_input():
    fuzz_one_input(
        b"""
        statute 1 "Demo" {
            elements {
                actus_reus taking := "takes";
            }
        }
        """
    )
