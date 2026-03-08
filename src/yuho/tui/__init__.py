"""
Yuho TUI - Terminal User Interface powered by Textual.
"""

def run_tui() -> None:
    """Launch the Yuho TUI application."""
    try:
        from yuho.tui.app import YuhoApp
    except ImportError:
        import sys
        print("error: 'textual' package required for TUI.", file=sys.stderr)
        print("install with: pip install textual", file=sys.stderr)
        sys.exit(1)
    app = YuhoApp()
    app.run()
