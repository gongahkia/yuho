"""Synthetic tests for the offline section-84 intake; no statutory fixture text."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock


HERE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("s84_extract", HERE / "tools/extract_sources.py")
assert SPEC and SPEC.loader
extract = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(extract)
STAMP = "2026-09-13T05:02:05Z"


def synthetic_page(title: str, act_code: str, sections: dict[str, str]) -> bytes:
    blocks = []
    for number, body in sections.items():
        blocks.append(f'<div class="prov1"><table><tr><td class="prov1Hdr" id="pr{number}-">'
                      f'Heading {number}</td></tr><tr><td class="prov1Txt"><strong>{number}.</strong>'
                      f'{body}</td></tr></table></div>')
    return (f'<!DOCTYPE html><!-- saved from url=(0033)https://sso.agc.gov.sg/Act/{act_code} -->'
            '<html><head><meta http-equiv="Content-Type" content="text/html; charset=UTF-8">'
            f'<title>{title} - Singapore Statutes Online</title></head><body>'
            '<div class="doc-status">Current version as at 13 Sep 2026 </div>'
            '<div class="generated-on">HTML created on: 13 Sep 2026</div>'
            f'<div id="legis"><div class="front">{title} 2020 REVISED EDITION</div>'
            + ''.join(blocks) + '</div></body></html>').encode('utf-8')


def make_inputs(root: Path) -> None:
    for key, title, code, _, required, _ in extract.ACTS:
        sections = {number: 'ordinary content' for number in required}
        if key == 'pc':
            sections['84'] = (' '.join(phrase for _, source, phrase, *_ in extract.ANCHORS
                                     if source == 'pc')
                              + '<table><tr><td class="p1No">(a)</td>'
                              '<td class="pTxt">child &amp; 😀</td></tr></table>')
        if key == 'ea':
            sections['107'] = ' '.join(phrase for _, source, phrase, *_ in extract.ANCHORS
                                       if source == 'ea')
        if key == 'cpc':
            sections['247'] = 'Procedure if accused is suspected to be incapable of making defence'
            sections['251'] = 'Acquittal on ground of unsound mind'
            sections['252'] = 'Safe custody of person acquitted'
        filename = f'{title} - Singapore Statutes Online.html'
        (root / filename).write_bytes(synthetic_page(title, code, sections))
        (root / (filename.removesuffix('.html') + '_files')).mkdir()


class IntakeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.inputs = self.root / 'inputs'
        self.inputs.mkdir()
        make_inputs(self.inputs)

    def packet(self) -> dict[str, bytes]:
        return extract.build_packet(self.inputs, STAMP)

    def test_determinism_canonical_json_and_lf(self) -> None:
        first = self.packet()
        self.assertEqual(first, self.packet())
        for name, value in first.items():
            self.assertTrue(value.endswith(b'\n'))
            self.assertFalse(value.endswith(b'\n\n'))
            self.assertNotIn(b'\r', value)
            if name.endswith('.json'):
                self.assertEqual(value, extract.canonical(json.loads(value)))

    def test_entities_unicode_and_list_separation(self) -> None:
        pc = self.packet()['extracted/penal-code-1871-section-84.txt'].decode()
        self.assertIn('child & 😀', pc)
        self.assertIn('\n(a)\nchild & 😀\n', pc)

    def test_spans_are_exact_utf8_boundaries(self) -> None:
        outputs = self.packet()
        for mapping in json.loads(outputs['STATUTORY-SPAN-MAP.json'])['mappings']:
            source = mapping['source_id']
            name = next(artifact['extracted_filename'] for artifact in
                        json.loads(outputs['EXTRACTION-MANIFEST.json'])['artifacts']
                        if artifact['source_id'] == source)
            data = outputs[name]
            piece = data[mapping['start']:mapping['end']]
            self.assertEqual(hashlib.sha256(piece).hexdigest(), mapping['support_sha256'])
            self.assertEqual(data[:mapping['start']].decode().encode(), data[:mapping['start']])
            self.assertEqual(data[:mapping['end']].decode().encode(), data[:mapping['end']])
            self.assertEqual((mapping['start_line'], mapping['start_col']),
                             extract.line_position(data, mapping['start']))

    def test_missing_duplicate_and_wrong_act(self) -> None:
        original = self.inputs / 'Evidence Act 1893 - Singapore Statutes Online.html'
        backup = original.read_bytes()
        original.unlink()
        with self.assertRaisesRegex(extract.IntakeError, 'top-level'):
            self.packet()
        original.write_bytes(backup)
        (self.inputs / 'Evidence Act 1893 - Singapore Statutes Online.copy.html').write_bytes(backup)
        with self.assertRaisesRegex(extract.IntakeError, 'top-level'):
            self.packet()
        (self.inputs / 'Evidence Act 1893 - Singapore Statutes Online.copy.html').unlink()
        original.write_bytes(backup.replace(b'<title>Evidence Act', b'<title>Wrong Act'))
        with self.assertRaisesRegex(extract.IntakeError, 'wrong or error page'):
            self.packet()

    def test_ambiguous_version_missing_section_and_bad_utf8(self) -> None:
        path = self.inputs / 'Penal Code 1871 - Singapore Statutes Online.html'
        original = path.read_bytes()
        path.write_bytes(original.replace(b'Current version as at 13 Sep 2026', b'Current and historical versions'))
        with self.assertRaisesRegex(extract.IntakeError, 'ambiguous version'):
            self.packet()
        path.write_bytes(original.replace(b'pr84-', b'pr85-'))
        with self.assertRaisesRegex(extract.IntakeError, 'missing provision 84'):
            self.packet()
        path.write_bytes(original + b'\xff')
        with self.assertRaisesRegex(extract.IntakeError, 'UTF-8'):
            self.packet()

    def test_symlinks_path_traversal_and_nested_output(self) -> None:
        path = self.inputs / 'Penal Code 1871 - Singapore Statutes Online.html'
        path.unlink()
        path.symlink_to(self.inputs / 'Evidence Act 1893 - Singapore Statutes Online.html')
        with self.assertRaisesRegex(extract.IntakeError, 'regular file'):
            self.packet()
        for bad in ('../escape', '/absolute', 'x/y', 'x\\y'):
            with self.assertRaises(extract.IntakeError):
                extract.safe_name(bad)

    def test_input_and_output_limits(self) -> None:
        with mock.patch.object(extract, 'MAX_HTML', 100):
            with self.assertRaisesRegex(extract.IntakeError, 'size limit'):
                self.packet()
        with mock.patch.object(extract, 'MAX_TEXT', 100):
            with self.assertRaisesRegex(extract.IntakeError, 'text size limit'):
                self.packet()
        with mock.patch.object(extract, 'MAX_JSON', 100):
            with self.assertRaisesRegex(extract.IntakeError, 'JSON size limit'):
                self.packet()

    def test_atomic_output_and_existing_nonempty_refusal(self) -> None:
        output = self.root / 'packet'
        output.mkdir()
        (output / 'user.txt').write_text('keep me')
        with self.assertRaisesRegex(extract.IntakeError, 'refusing to overwrite'):
            extract.write_packet(output, self.packet())
        self.assertEqual((output / 'user.txt').read_text(), 'keep me')
        self.assertEqual(sorted(p.name for p in output.iterdir()), ['user.txt'])
        fresh = self.root / 'fresh'
        extract.write_packet(fresh, self.packet())
        extract.write_packet(fresh, self.packet())
        self.assertEqual(len(list(fresh.rglob('*'))), 9)

    def test_lock_rejects_tampered_copy(self) -> None:
        outputs = self.packet()
        receipt = json.loads(outputs['SOURCE-RECEIPT.json'])['sources']
        lock = {'transform': extract.TRANSFORM,
                'sources': [{key: source[key] for key in
                             ('source_id', 'original_filename', 'byte_length', 'sha256')}
                            for source in receipt],
                'generated_artifacts': [{'path': name, 'sha256': extract.digest(data),
                                         'byte_length': len(data)}
                                        for name, data in sorted(outputs.items())]}
        path = self.root / 'lock.json'
        path.write_bytes(extract.canonical(lock))
        extract.verify_lock(outputs, self.inputs, path)
        input_path = self.inputs / 'Penal Code 1871 - Singapore Statutes Online.html'
        input_path.write_bytes(input_path.read_bytes().replace(b'child &amp;', b'child and'))
        with self.assertRaisesRegex(extract.IntakeError, 'source lock mismatch'):
            extract.verify_lock(self.packet(), self.inputs, path)

    @unittest.skipUnless(os.environ.get('YUHO_S84_INPUT_DIR'), 'external supplied pages not configured')
    def test_external_regeneration_twice_and_locked_hashes(self) -> None:
        source = Path(os.environ['YUHO_S84_INPUT_DIR'])
        outputs = extract.build_packet(source, STAMP)
        extract.verify_lock(outputs, source, HERE / 'SOURCE-LOCK.json')
        first, second = self.root / 'first', self.root / 'second'
        extract.write_packet(first, outputs)
        extract.write_packet(second, extract.build_packet(source, STAMP))
        self.assertEqual({p.relative_to(first): p.read_bytes() for p in first.rglob('*') if p.is_file()},
                         {p.relative_to(second): p.read_bytes() for p in second.rglob('*') if p.is_file()})


if __name__ == '__main__':
    unittest.main()
