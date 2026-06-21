"""Tests for the Malaysia Penal Code Act 574 PDF scraper."""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))


def test_parse_pdf_text_uses_toc_titles_and_trims_next_marginal_note():
    import scrape_malaysia_penal_code as scraper

    text = """
LAWS OF MALAYSIA
ARRANGEMENT OF SECTIONS
  1.      Short title
  2.      Punishment of offences committed within Malaysia
  3.      Punishment of offences committed beyond, but which by law may be
          tried within Malaysia
PENAL CODE
An Act relating to criminal offences.
Short title
1. This Act may be cited as the Penal Code.
Punishment of offences committed within Malaysia
2. Every person shall be liable to punishment under this Code.
Punishment of offences committed beyond, but which by law
may be tried within Malaysia
3. Any person liable by law to be tried for an offence committed beyond Malaysia.
*NOTE--see section 39 of the Abolition of Mandatory Death Penalty Act 2023
[Act 846] w.e.f 4 July 2023 which provides the following provision:
39. Upon the coming into operation of this Act.
"""

    sections = scraper.parse_pdf_text(text)

    assert [section.number for section in sections] == ["1", "2", "3"]
    assert sections[2].marginal_note == (
        "Punishment of offences committed beyond, but which by law may be tried within Malaysia"
    )
    assert sections[0].text == "This Act may be cited as the Penal Code."


def test_parse_pdf_text_keeps_centered_toc_heading_out_of_title():
    import scrape_malaysia_penal_code as scraper

    text = """
ARRANGEMENT OF SECTIONS
  1.      Short title
 420.     Cheating and dishonestly inducing delivery of property

               Fraudulent Deeds and Dispositions of Property

 421.     Dishonest removal
PENAL CODE
An Act relating to criminal offences.
Short title
1. This Act may be cited as the Penal Code.
Cheating and dishonestly inducing delivery of property
420. Whoever cheats and thereby dishonestly induces delivery.
Dishonest removal
421. Whoever dishonestly removes property.
"""

    sections = scraper.parse_pdf_text(text)
    by_number = {section.number: section for section in sections}

    assert by_number["420"].marginal_note == (
        "Cheating and dishonestly inducing delivery of property"
    )
