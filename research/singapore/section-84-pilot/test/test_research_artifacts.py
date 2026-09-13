"""Offline consistency checks for the non-executable section-84 review packet."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import unittest
from urllib.parse import urlparse


HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[2]
BASELINE = 'dffa850468e5547e20077b0da8b805e36b8ac339'
EVIDENCE = {
    'verified_primary_text', 'verified_judicial_holding',
    'official_context_not_binding', 'supported_inference', 'secondary_only',
    'conflicting_or_uncertain', 'qualified_review_required', 'unsupported',
}
DISPOSITIONS = {
    'structurally_representable', 'representable_with_supplied_status',
    'requires_temporal_selector', 'requires_non_kernel_record',
    'requires_anchor_offence', 'capability_gap', 'excluded_from_product_scope',
    'blocked_pending_qualified_review',
}
DOCUMENTS = (
    ROOT / 'docs/rewrite/SINGAPORE-SECTION-84-AUTHORITY-AND-TEMPORAL-RESEARCH.md',
    HERE / 'QUALIFIED-REVIEW-BRIEF.md', HERE / 'README.md',
)


def no_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'duplicate JSON key: {key}')
        result[key] = value
    return result


def load(name: str) -> dict[str, object]:
    data = (HERE / name).read_bytes()
    assert data.endswith(b'\n') and not data.endswith(b'\n\n')
    decoded = json.loads(data.decode('utf-8'), object_pairs_hook=no_duplicate_keys)
    assert data == (json.dumps(decoded, ensure_ascii=False, sort_keys=True,
                               separators=(',', ':')) + '\n').encode('utf-8')
    return decoded


class ResearchArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.authorities = load('AUTHORITY-REGISTER.json')
        cls.propositions = load('PROPOSITION-REVIEW-MATRIX.json')
        cls.temporal = load('TEMPORAL-APPLICABILITY-MATRIX.json')
        cls.lock = load('SOURCE-LOCK.json')

    def test_ids_unique_and_references_resolve(self) -> None:
        authorities = self.authorities['authorities']
        propositions = self.propositions['propositions']
        events = self.temporal['events']
        for rows, field in ((authorities, 'authority_id'),
                            (propositions, 'proposition_id'), (events, 'event_id')):
            ids = [item[field] for item in rows]
            self.assertEqual(len(ids), len(set(ids)))
            self.assertTrue(all(isinstance(item, str) and item for item in ids))
        aid = {item['authority_id'] for item in authorities}
        for row in (*propositions, *events):
            self.assertTrue(row['authority_support'])
            for support in row['authority_support']:
                self.assertIn(support['authority_id'], aid)
                self.assertTrue(support['pinpoint'])

    def test_authority_classification_and_exact_hash_claim(self) -> None:
        for a in self.authorities['authorities']:
            self.assertTrue(a['pinpoints'] and all(a['pinpoints']))
            self.assertEqual(a['access_date'], '2026-09-13')
            self.assertTrue(a['source_classification'])
            self.assertTrue(a['binding_or_contextual'])
            self.assertTrue(a['access_outcome'])
            self.assertTrue(a['capture_form'])
            self.assertIn('does not prove authenticity', a['hash_claim'])
            self.assertIn('not_established', a['redistribution_status'])
            parsed = urlparse(a['official_url'])
            self.assertEqual(parsed.scheme, 'https')
            self.assertTrue(parsed.netloc)
            if 'sha256' in a:
                self.assertRegex(a['sha256'], r'^[0-9a-f]{64}$')
                self.assertIn(a['capture_form'],
                              {'temporary_official_pdf_capture', 'browser_saved_complete_html'})

    def test_propositions_complete_and_no_legal_approval(self) -> None:
        authority_by_id = {a['authority_id']: a for a in self.authorities['authorities']}
        for p in self.propositions['propositions']:
            self.assertRegex(p['proposition_id'], r'^P84-[0-9]{2}$')
            self.assertTrue(p['statement'] and p['category'])
            self.assertTrue(p['statutory_expression_or_period'])
            self.assertIn(p['evidence_status'], EVIDENCE)
            self.assertIn(p['modelling_disposition'], DISPOSITIONS)
            self.assertIn(p['qualified_review_status'],
                          {'pending_qualified_review', 'not_applicable_to_technical_boundary'})
            self.assertIn(p['confidence'], {'high', 'moderate', 'low'})
            self.assertTrue(p['open_reviewer_question'])
            for support in p['authority_support']:
                self.assertTrue(support['support_kind'])
            if p['evidence_status'] == 'verified_primary_text':
                self.assertTrue(any(
                    authority_by_id[s['authority_id']]['authority_type'] in
                    {'gazette_act', 'gazette_notification'}
                    and authority_by_id[s['authority_id']]['access_outcome'] ==
                    'official PDF retrieved'
                    for s in p['authority_support']), p['proposition_id'])
            if p['evidence_status'] == 'verified_judicial_holding':
                self.assertTrue(any(
                    authority_by_id[s['authority_id']]['authority_type'] == 'judgment'
                    and authority_by_id[s['authority_id']]['access_outcome'] ==
                    'official PDF retrieved'
                    for s in p['authority_support']), p['proposition_id'])
        by_id = {p['proposition_id']: p for p in self.propositions['propositions']}
        for proposition_id in ('P84-02', 'P84-03', 'P84-04', 'P84-05'):
            self.assertIn('2020-01-01',
                          by_id[proposition_id]['statutory_expression_or_period'])
        for document in (self.authorities, self.propositions, self.temporal):
            self.assertFalse(document['qualified_review_completed'])

    def test_temporal_dates_are_explicit_and_not_overclaimed(self) -> None:
        for e in self.temporal['events']:
            state = e['date']['state']
            self.assertIn(state, {'known', 'unverified'})
            if state == 'known':
                self.assertRegex(e['date']['value'], r'^\d{4}-\d{2}-\d{2}$')
                if e['legal_effect_status'] == 'verified_in_instrument':
                    self.assertEqual(e['event_kind'], 'commencement')
                    self.assertEqual(e['evidence_status'], 'verified_primary_text')
            else:
                self.assertTrue(e['date']['note'])
                self.assertNotEqual(e['legal_effect_status'], 'verified_in_instrument')
            self.assertIn(e['evidence_status'], EVIDENCE)
            self.assertTrue(e['event_kind'] and e['effect_or_meaning'])

    def test_no_executable_or_court_outcome_claim(self) -> None:
        report = DOCUMENTS[0].read_text(encoding='utf-8')
        brief = DOCUMENTS[1].read_text(encoding='utf-8')
        for body in (report, brief):
            self.assertIn('non-executable', body)
            self.assertIn('not a valid `ModelBundle-v1`', body)
            self.assertIn('court', body.casefold())
        self.assertIn('No qualified reviewer has approved the model', report)
        self.assertIn('qualified_review_confirmed_in_writing', brief)
        self.assertIn('did not give separate answers to Q1–Q10', brief)
        self.assertIn('rule result cannot', report)
        self.assertNotIn('qualified_review_completed":true',
                         (HERE / 'PROPOSITION-REVIEW-MATRIX.json').read_text())

    def test_markdown_structure_and_relative_links(self) -> None:
        links = re.compile(r'\[[^\]]+\]\(([^)]+)\)')
        for path in DOCUMENTS:
            body = path.read_text(encoding='utf-8')
            self.assertTrue(body.startswith('# '))
            self.assertFalse(body.startswith('##'))
            self.assertIn('\n\n', body)
            for target in links.findall(body):
                if target.startswith(('https://', 'http://', '#')):
                    continue
                relative = target.split('#', 1)[0]
                self.assertTrue((path.parent / relative).exists(), (path, target))

    def test_original_lock_bytes_and_external_packet_if_configured(self) -> None:
        old = subprocess.run(
            ['git', 'show', f'{BASELINE}:research/singapore/section-84-pilot/SOURCE-LOCK.json'],
            cwd=ROOT, check=True, capture_output=True,
        ).stdout
        self.assertEqual((HERE / 'SOURCE-LOCK.json').read_bytes(), old)
        source = os.environ.get('YUHO_S84_INPUT_DIR')
        if source:
            for record in self.lock['sources']:
                path = Path(source) / record['original_filename']
                data = path.read_bytes()
                self.assertEqual(len(data), record['byte_length'])
                self.assertEqual(hashlib.sha256(data).hexdigest(), record['sha256'])
        output = os.environ.get('YUHO_S84_OUTPUT_DIR')
        if output:
            for record in self.lock['generated_artifacts']:
                data = (Path(output) / record['path']).read_bytes()
                self.assertEqual(len(data), record['byte_length'])
                self.assertEqual(hashlib.sha256(data).hexdigest(), record['sha256'])


if __name__ == '__main__':
    unittest.main()
