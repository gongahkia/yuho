"""Checks for the maintainer-attested, unsigned research-baseline review."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import unittest


PILOT = Path(__file__).resolve().parents[1]
ROOT = PILOT.parents[2]
BASELINE = 'c057fb84000265b412d1b6ca3d050e7b2a1d5eca'
RECORD = PILOT / 'QUALIFIED-REVIEW-RECORD.json'


class ReviewRecordTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        raw = RECORD.read_bytes()
        cls.record = json.loads(raw.decode('utf-8'))
        canonical = json.dumps(cls.record, ensure_ascii=False, sort_keys=True,
                               separators=(',', ':')).encode('utf-8') + b'\n'
        assert raw == canonical

    def test_exact_unsigned_baseline_scope(self) -> None:
        record = self.record
        self.assertEqual(record['schema'], 'yuho.sg-section-84-qualified-review-record/v1')
        self.assertEqual(record['review_status'], 'qualified_review_confirmed_in_writing')
        self.assertEqual(record['reviewed_baseline_commit'], BASELINE)
        self.assertEqual(record['authentication'], 'unsigned')
        self.assertIs(record['digital_signature_present'], False)
        self.assertEqual(record['assertion_basis'],
                         'maintainer_attested_written_confirmation')
        self.assertEqual(record['reviewer_qualification'],
                         'singapore_qualified_criminal_law_reviewer')
        self.assertEqual(record['qualification_verification'], 'maintainer_attested')
        self.assertEqual(record['reviewer_identity_disclosure'], 'withheld')
        self.assertEqual(record['underlying_evidence_retention'],
                         'external_to_repository')
        self.assertEqual(record['underlying_evidence_digest'], {'kind': 'unavailable'})
        self.assertEqual(record['scope_classification'],
                         'research_prototype_subject_to_documented_limitations')
        self.assertEqual(record['per_proposition_response_status'], 'not_recorded')
        self.assertEqual(record['future_bundle_digest_review_status'],
                         'implementation_conformance_review_pending')
        self.assertNotIn('bundle_digest', record)
        self.assertNotIn('reviewed_at', record)
        self.assertNotIn('reviewer_name', record)

    def test_artifacts_are_exact_baseline_bytes(self) -> None:
        artifacts = self.record['reviewed_artifacts']
        paths = [item['path'] for item in artifacts]
        self.assertEqual(paths, sorted(set(paths)))
        self.assertGreaterEqual(len(paths), 6)
        for item in artifacts:
            self.assertFalse(Path(item['path']).is_absolute())
            self.assertNotIn('..', Path(item['path']).parts)
            baseline_bytes = subprocess.run(
                ['git', 'show', f"{BASELINE}:{item['path']}"], cwd=ROOT,
                check=True, capture_output=True,
            ).stdout
            self.assertEqual(hashlib.sha256(baseline_bytes).hexdigest(),
                             item['sha256'])
        for path in self.record['limitations_incorporated_by_reference']:
            self.assertIn(path, paths)

    def test_review_does_not_change_evidence_or_source_lock(self) -> None:
        for name in ('PROPOSITION-REVIEW-MATRIX.json', 'SOURCE-LOCK.json'):
            path = f'research/singapore/section-84-pilot/{name}'
            original = subprocess.run(
                ['git', 'show', f'{BASELINE}:{path}'], cwd=ROOT,
                check=True, capture_output=True,
            ).stdout
            self.assertEqual((PILOT / name).read_bytes(), original)
        matrix = json.loads((PILOT / 'PROPOSITION-REVIEW-MATRIX.json').read_text())
        self.assertFalse(matrix['qualified_review_completed'])
        self.assertTrue(all(item['qualified_review_status'] in
                            {'pending_qualified_review',
                             'not_applicable_to_technical_boundary'}
                            for item in matrix['propositions']))

    def test_no_identity_or_digest_transfer_claim(self) -> None:
        record = self.record
        self.assertIn('not digitally authenticated', record['non_claims'][0])
        self.assertTrue(any('future ModelBundle digest' in item
                            for item in record['non_claims']))
        brief = (PILOT / 'QUALIFIED-REVIEW-BRIEF.md').read_text()
        readme = (PILOT / 'README.md').read_text()
        self.assertIn('no executable section 84 artifact', readme)
        self.assertIn('HTTP 403', readme)
        self.assertIn('did not give separate answers to Q1–Q10', brief)
        self.assertIn('not recorded as ten individual answers', brief)


if __name__ == '__main__':
    unittest.main()
