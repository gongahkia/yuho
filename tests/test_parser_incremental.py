from __future__ import annotations

import logging

import yuho.parser.wrapper as wrapper
from yuho.parser.wrapper import Parser, TreeEdit, _compute_tree_edit


SOURCE = """
statute 1 "Demo" {
    elements {
        actus_reus taking := "takes";
        mens_rea intent := "intends";
    }
}
"""


def test_incremental_parse_matches_full_parse_for_text_edit():
    parser = Parser()
    first = parser.parse(SOURCE, file="<old>")
    edited = SOURCE.replace('"takes"', '"takes property"')

    incremental = parser.parse_incremental(edited, first, file="<new>")
    full = parser.parse(edited, file="<new>")

    assert incremental.is_valid
    assert str(incremental.root_node) == str(full.root_node)
    assert incremental.root_node.end_point == full.root_node.end_point


def test_incremental_edit_points_count_utf8_columns_as_bytes():
    old_source = 'string label := "cafe"\n'
    new_source = 'string label := "café"\n'

    edit = _compute_tree_edit(old_source, new_source)

    assert edit.start_byte == len('string label := "caf'.encode("utf-8"))
    assert edit.old_end_byte == len('string label := "cafe'.encode("utf-8"))
    assert edit.new_end_byte == len('string label := "café'.encode("utf-8"))
    assert edit.new_end_point == (0, len('string label := "café'.encode("utf-8")))


def test_incremental_parse_falls_back_on_malformed_edit(monkeypatch, caplog):
    parser = Parser()
    first = parser.parse(SOURCE, file="<old>")
    edited = SOURCE.replace('"takes"', '"takes property"')
    bad_edit = TreeEdit(
        start_byte=999,
        old_end_byte=1000,
        new_end_byte=1001,
        start_point=(0, 999),
        old_end_point=(0, 1000),
        new_end_point=(0, 1001),
    )
    monkeypatch.setattr(wrapper, "_compute_tree_edit", lambda _old, _new: bad_edit)

    with caplog.at_level(logging.DEBUG, logger="yuho.parser.wrapper"):
        incremental = parser.parse_incremental(edited, first, file="<new>")

    full = parser.parse(edited, file="<new>")
    assert incremental.is_valid
    assert str(incremental.root_node) == str(full.root_node)
    assert "invalid incremental edit bounds" in caplog.text
