"""Tests for parser hardening, input validation, and TUI utilities."""

import io
import os
import sys
import tempfile
from pathlib import Path

import pytest

try:
    from tree_sitter import Parser as _TSParser
    HAS_TREE_SITTER = True
except ImportError:
    HAS_TREE_SITTER = False

needs_tree_sitter = pytest.mark.skipif(not HAS_TREE_SITTER, reason="tree-sitter not installed")


class TestValidateFilePath:
    """Tests for parser wrapper validate_file_path."""

    def test_valid_yh_file(self, tmp_path):
        p = tmp_path / "test.yh"
        p.write_text("// empty", encoding="utf-8")
        from yuho.parser.wrapper import validate_file_path
        result = validate_file_path(p)
        assert result == p.resolve()

    def test_valid_yuho_file(self, tmp_path):
        p = tmp_path / "test.yuho"
        p.write_text("// empty", encoding="utf-8")
        from yuho.parser.wrapper import validate_file_path
        result = validate_file_path(p)
        assert result == p.resolve()

    def test_nonexistent_file(self, tmp_path):
        from yuho.parser.wrapper import validate_file_path
        with pytest.raises((FileNotFoundError, ValueError)):
            validate_file_path(tmp_path / "nope.yh")

    def test_directory_not_file(self, tmp_path):
        from yuho.parser.wrapper import validate_file_path
        with pytest.raises((ValueError, IsADirectoryError)):
            validate_file_path(tmp_path)

    def test_null_byte_in_path(self):
        from yuho.parser.wrapper import validate_file_path
        with pytest.raises(ValueError, match="null"):
            validate_file_path(Path("test\x00.yh"))


class TestValidateOutputPath:
    """Tests for parser wrapper validate_output_path."""

    def test_valid_output_path(self, tmp_path):
        from yuho.parser.wrapper import validate_output_path
        out = tmp_path / "out.json"
        result = validate_output_path(out)
        assert result == out.resolve()

    def test_parent_not_exist(self, tmp_path):
        from yuho.parser.wrapper import validate_output_path
        with pytest.raises((ValueError, FileNotFoundError)):
            validate_output_path(tmp_path / "no_such_dir" / "file.json")

    def test_null_byte_in_output_path(self):
        from yuho.parser.wrapper import validate_output_path
        with pytest.raises(ValueError, match="null"):
            validate_output_path(Path("out\x00.json"))


class TestValidateSource:
    """Tests for source validation in Parser.validate_source method."""

    def test_null_byte_rejected(self):
        from yuho.parser.wrapper import Parser
        parser = Parser()
        with pytest.raises(ValueError, match="null"):
            parser.validate_source("statute \x00 bad", "<test>")

    def test_bom_stripped(self):
        from yuho.parser.wrapper import Parser
        parser = Parser()
        result = parser.validate_source("\ufeffstatute code", "<test>")
        assert not result.startswith("\ufeff")

    def test_empty_source_ok(self):
        from yuho.parser.wrapper import Parser
        parser = Parser()
        result = parser.validate_source("", "<test>")
        assert result == ""


@needs_tree_sitter
class TestParserHardening:
    """Tests for parser parse() hardening (requires tree-sitter)."""

    def test_parse_empty_source(self):
        from yuho.parser import get_parser
        parser = get_parser()
        result = parser.parse("", "<test>")
        assert result is not None

    def test_parse_valid_source(self):
        from yuho.parser import get_parser
        parser = get_parser()
        src = 'statute "299" "Culpable Homicide" {}'
        result = parser.parse(src, "<test>")
        assert result is not None

    def test_parse_file_nonexistent(self):
        from yuho.parser import get_parser
        parser = get_parser()
        with pytest.raises((FileNotFoundError, ValueError, SystemExit)):
            parser.parse_file("/nonexistent/path/file.yh")


class TestAnalysisService:
    """Tests for analysis service hardening."""

    def test_analyze_nonexistent_file(self):
        from yuho.services.analysis import analyze_file
        result = analyze_file("/no/such/file.yh")
        assert not result.is_valid
        assert any("not found" in e.message.lower() for e in result.errors)

    def test_analyze_null_bytes(self):
        from yuho.services.analysis import analyze_source
        result = analyze_source("hello\x00world")
        assert not result.is_valid

    @needs_tree_sitter
    def test_analyze_empty_source(self):
        from yuho.services.analysis import analyze_source
        result = analyze_source("")
        assert result is not None

    def test_analyze_directory_not_file(self, tmp_path):
        from yuho.services.analysis import analyze_file
        result = analyze_file(str(tmp_path))
        assert not result.is_valid

    @needs_tree_sitter
    def test_analyze_bom_stripped(self):
        from yuho.services.analysis import analyze_source
        result = analyze_source("\ufeff// comment")
        assert "\ufeff" not in result.source


class TestCaptureCliUtil:
    """Tests for TUI capture_cli utility."""

    def test_capture_stdout(self):
        from yuho.tui.app import capture_cli
        def writer():
            print("hello")
        out, err = capture_cli(writer)
        assert "hello" in out

    def test_capture_systemexit(self):
        from yuho.tui.app import capture_cli
        def exiter():
            print("before")
            sys.exit(1)
        out, err = capture_cli(exiter)
        assert "before" in out

    def test_capture_exception(self):
        from yuho.tui.app import capture_cli
        def raiser():
            raise RuntimeError("boom")
        out, err = capture_cli(raiser)
        assert "boom" in err

    def test_strip_ansi(self):
        from yuho.tui.app import _strip_ansi
        assert _strip_ansi("\x1b[31mred\x1b[0m") == "red"
        assert _strip_ansi("no ansi") == "no ansi"

    def test_capture_click_echo(self):
        import click
        from yuho.tui.app import capture_cli
        def clicker():
            click.echo("click output")
        out, err = capture_cli(clicker)
        assert "click output" in out


class TestClipboardHelper:
    """Tests for clipboard helper."""

    def test_copy_returns_bool(self):
        from yuho.tui.app import _copy_to_clipboard
        result = _copy_to_clipboard("test")
        assert isinstance(result, bool)
