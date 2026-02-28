"""Unit tests for SourceLocation edge-case behavior."""

from yuho.parser.source_location import SourceLocation


def test_merge_preserves_zero_offset_values() -> None:
    """Merging should keep byte offset 0 when both locations provide offsets."""
    left = SourceLocation(
        file="example.yh",
        line=1,
        col=1,
        end_line=1,
        end_col=5,
        offset=0,
        end_offset=4,
    )
    right = SourceLocation(
        file="example.yh",
        line=2,
        col=1,
        end_line=2,
        end_col=5,
        offset=8,
        end_offset=12,
    )

    merged = left.merge(right)

    assert merged.offset == 0
    assert merged.end_offset == 12
