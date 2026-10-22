"""Regression checks for Pages public artifact allowlist (original fixtures only)."""
import json
import tempfile
import unittest
from pathlib import Path
from scripts.check_public_bundle import validate

ASSETS = ('app.js', 'style.css', 'personal.js', 'personal-core.mjs', 'personal-ui.mjs', 'personal.css')

class PublicBundleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / 'data' / 'chapters').mkdir(parents=True)
        (self.root / 'assets').mkdir()
        for name in ('index.html', 'personal.html', '.nojekyll'):
            (self.root / name).write_text('', encoding='utf-8')
        for name in ASSETS:
            (self.root / 'assets' / name).write_text('', encoding='utf-8')
        (self.root / 'data' / 'library.json').write_text(json.dumps({'books': []}), encoding='utf-8')

    def tearDown(self):
        self.tmp.cleanup()

    def test_clean_frontend_passes(self):
        self.assertEqual(validate(self.root), [])

    def test_private_text_is_rejected(self):
        (self.root / 'data' / 'chapters' / '137.txt').write_text('demo', encoding='utf-8')
        self.assertTrue(validate(self.root))

    def test_unlisted_script_is_rejected(self):
        (self.root / 'assets' / 'private.js').write_text('demo', encoding='utf-8')
        self.assertTrue(validate(self.root))

    def test_missing_asset_is_rejected(self):
        (self.root / 'assets' / 'personal.js').unlink()
        self.assertTrue(validate(self.root))

if __name__ == '__main__':
    unittest.main()
