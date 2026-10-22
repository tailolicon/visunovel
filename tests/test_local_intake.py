"""Local intake synthetic tests; no third-party chapters."""
import json
import tempfile
import unittest
from pathlib import Path
from tools.local_intake import inspect, record, ROOT

class LocalIntakeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.src = self.base / "chapter-137.txt"
        self.src.write_text("Văn bản tự tạo để kiểm thử.\n", encoding="utf-8")
        self.out = self.base / "private"
    def test_dry_run_has_no_write(self):
        result = record(self.src, 137, self.out, True)
        self.assertTrue(result["dry_run"])
        self.assertFalse(self.out.exists())
    def test_private_manifest_has_no_prose(self):
        result = record(self.src, 137, self.out)
        payload = Path(result["manifest_path"]).read_text(encoding="utf-8")
        self.assertNotIn("Văn bản tự tạo", payload)
        self.assertFalse(json.loads(payload)["public_distribution_authorized"])
        self.assertTrue(self.src.exists())
    def test_same_hash_is_idempotent(self):
        record(self.src, 137, self.out)
        self.assertTrue(record(self.src, 137, self.out)["reused"])
    def test_changed_source_not_overwritten(self):
        record(self.src, 137, self.out)
        self.src.write_text("Đã thay đổi.\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "khác hash"):
            record(self.src, 137, self.out)
    def test_prior_chapters_deferred(self):
        with self.assertRaisesRegex(ValueError, "137"):
            record(self.src, 136, self.out)
    def test_non_text_extension_rejected(self):
        bad = self.base / "chapter.epub"
        bad.write_text("Demo", encoding="utf-8")
        with self.assertRaises(ValueError):
            inspect(bad)
    def test_private_output_must_not_be_repo(self):
        with self.assertRaisesRegex(ValueError, "repository"):
            record(self.src, 137, ROOT / "private")
    def test_source_in_repo_rejected(self):
        with self.assertRaisesRegex(ValueError, "repository"):
            inspect(ROOT / "tests" / "example-source.txt")

if __name__ == "__main__":
    unittest.main()
