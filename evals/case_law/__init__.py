"""Case-law differential-testing harness for the Yuho evals pack.

For each canonical Singapore criminal case curated under
``evals/case_law/fixtures/``, two scorers fire:

* ``score_recommend.py`` — runs ``yuho recommend`` against the
  encoded fact pattern and scores top-k accuracy / mean reciprocal
  rank against the actual charge the prosecution brought.
* ``score_contrast.py`` — when the case carries an
  ``alternative_charge`` the court considered (and rejected), runs
  ``yuho contrast(actual_charge, alternative_charge)`` and scores
  the surfaced distinguishing-elements set against the elements
  the court itself said distinguished the two.

Both scorers honour the ``not_legal_advice`` envelope used
elsewhere in the toolchain. Results are structural agreement
rates against an *external* authoritative source — a categorical
lift over the rest of the eval surface, which is self-referential
(scoring Yuho's outputs against Yuho's own ground truth).

See ``evals/case_law/README.md`` for the methodology and threats
to validity.
"""
