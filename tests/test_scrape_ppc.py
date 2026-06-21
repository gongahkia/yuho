"""Tests for the Pakistan Penal Code PDF scraper."""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))


def test_parse_pdf_text_uses_toc_titles_and_body_text():
    import scrape_ppc as scraper

    text = """
THE PAKISTAN PENAL CODE,1860
CONTENTS
1.          Title and extent of operation of the Code.
2.          Punishment of offences committed within Pakistan.
299.        Definitions.
300.        Qatl-i-amd.
511.        Punishment for attempting to commit offences punishable with imprisonment for life.
THE PAKISTAN PENAL CODE
1. Title and extent of operation of the Code. This Act shall be called the Pakistan Penal Code.
2. Punishment of offences committed within Pakistan. Every person shall be liable.
299. Definitions. In this Chapter, unless there is anything repugnant in the subject or context.
300. Qatl-e-amd. Whoever, with the intention of causing death, causes death.
511. Punishment for attempting to commit offences punishable with imprisonment for life. Whoever attempts.
"""

    sections = scraper.parse_pdf_text(text)

    assert [section.number for section in sections] == ["1", "2", "299", "300", "511"]
    assert sections[0].marginal_note == "Title and extent of operation of the Code."
    assert sections[0].text == "This Act shall be called the Pakistan Penal Code."
    assert sections[2].marginal_note == "Definitions."
    assert sections[3].text == "Qatl-e-amd. Whoever, with the intention of causing death, causes death."


def test_parse_pdf_text_normalizes_spaced_letter_sections():
    import scrape_ppc as scraper

    text = """
CONTENTS
295 A. Deliberate and malicious acts intended to outrage religious feelings.
THE PAKISTAN PENAL CODE
1. Title and extent of operation of the Code. Body.
295 A. Deliberate and malicious acts intended to outrage religious feelings. Body text.
"""

    sections = scraper.parse_pdf_text(text)

    assert sections[-1].number == "295A"
    assert sections[-1].marginal_note == "Deliberate and malicious acts intended to outrage religious feelings."


def test_parse_pdf_text_handles_amendment_marker_before_section_number():
    import scrape_ppc as scraper

    text = """
CONTENTS
299. Definitions.
THE PAKISTAN PENAL CODE
1. Title and extent of operation of the Code. Body.
1[299. Definitions. In this Chapter, unless there is anything repugnant.
"""

    sections = scraper.parse_pdf_text(text)

    assert sections[-1].number == "299"
    assert sections[-1].marginal_note == "Definitions."
    assert sections[-1].text == "In this Chapter, unless there is anything repugnant."


def test_parse_pdf_text_keeps_footnote_like_section_markers_in_current_body():
    import scrape_ppc as scraper

    text = """
CONTENTS
1. Title and extent of operation of the Code.
153B. Inducing students, etc.
154. Owner or occupier of land on which an unlawful assembly is held.
THE PAKISTAN PENAL CODE
1. Title and extent of operation of the Code. Body.
153B. Inducing students, etc. Main body.
1S. 153B was ins. by amendment.
154. Owner or occupier of land on which an unlawful assembly is held. Next body.
"""

    sections = scraper.parse_pdf_text(text)

    assert [section.number for section in sections] == ["1", "153B", "154"]
    assert "1S. 153B was ins. by amendment." in sections[1].text
