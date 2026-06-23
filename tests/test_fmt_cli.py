from __future__ import annotations

from yuho.ast import ASTBuilder
from yuho.cli.commands.fmt import _format_module
from yuho.parser import get_parser


def test_formatter_handles_grouped_elements():
    source = """
    statute 1 "Demo" {
        elements {
            all_of {
                actus_reus taking := "takes";
                any_of {
                    mens_rea intent := "intends";
                    mens_rea reckless := "reckless";
                }
            }
        }
    }
    """
    parser = get_parser()
    parsed = parser.parse(source, "<test>")
    assert parsed.is_valid
    ast = ASTBuilder(parsed.source, "<test>").build(parsed.root_node)

    formatted = _format_module(ast)

    assert "all_of {" in formatted
    assert "any_of {" in formatted
    assert 'actus_reus taking := "takes";' in formatted
    assert parser.parse(formatted, "<formatted>").is_valid
