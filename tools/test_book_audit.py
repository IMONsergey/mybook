import csv
import json
from pathlib import Path
import tempfile
import unittest
from PIL import Image
from book_audit import audit


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'manuscript').mkdir()
        (self.root / 'assets/figures').mkdir(parents=True)
        self.source = self.root / 'manuscript/source.md'
        self.source.write_text('# Тест\n\nТочный текст.\n\n[[FIGURE:a.png|Сравнение]]\n')
        self.manifest = self.root / 'assets/figures/manifest.json'
        self.row = dict(path='a.png', width=300, height=200, alt='Два предмета')
        self.manifest.write_text(json.dumps([self.row]))
        Image.new('RGB', (300, 200)).save(self.root / 'assets/figures/a.png')
        (self.root / 'assets/rights.csv').write_text('asset_id,status\na.png,author_confirmed\n')

    def codes(self):
        return {i['code'] for i in audit(self.root)['issues']}

    def test_clean_and_read_only(self):
        before = self.source.read_bytes()
        result = audit(self.root)
        self.assertEqual(result['issues'], [])
        self.assertEqual(result['assets'][0]['width_mm_at_300ppi'], 25.4)
        self.assertEqual(before, self.source.read_bytes())

    def test_missing_asset(self):
        (self.root / 'assets/figures/a.png').unlink()
        self.assertIn('missing_figure', self.codes())

    def test_duplicate_manifest(self):
        self.manifest.write_text(json.dumps([self.row, self.row]))
        self.assertIn('duplicate_manifest', self.codes())

    def test_path_escape(self):
        self.source.write_text('[[FIGURE:../../outside.png|Предмет]]')
        self.assertIn('unsafe_path', self.codes())

    def test_dimensions(self):
        self.row['width'] = 500
        self.manifest.write_text(json.dumps([self.row]))
        self.assertIn('dimension_mismatch', self.codes())

    def test_typography_and_urls(self):
        self.source.write_text(self.source.read_text() + '\nЕще ещё — https://example.com/a/a\n')
        self.assertIn('yo', self.codes())
        self.assertIn('em_dash', self.codes())
        self.assertNotIn('repeated_word', self.codes())

    def test_missing_alt_and_rights(self):
        self.row['alt'] = ''
        self.manifest.write_text(json.dumps([self.row]))
        (self.root / 'assets/rights.csv').unlink()
        self.assertTrue({'missing_alt', 'rights_registry', 'rights_unverified'} <= self.codes())

    def test_malformed_figure(self):
        self.source.write_text('[[FIGURE:a.png]]')
        self.assertIn('malformed_figure', self.codes())


if __name__ == '__main__':
    unittest.main()
