"""Offline regressions for translator input and chunk boundaries."""
import contextlib
import io
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch
from tools import personal_translate as pt

class PersonalTranslatorRegressions(unittest.TestCase):
    def test_paragraph_order_preserved(self):
        parts = pt.chunk_text("Một.\n\nHai.\n\nBa.", 12)
        self.assertEqual([x for block in parts for x in block], ["Một.", "Hai.", "Ba."])

    def test_long_paragraph_rejected(self):
        with self.assertRaises(ValueError):
            pt.chunk_text("x" * 100, 10)

    def test_utf8_bom_and_newlines(self):
        with TemporaryDirectory() as td:
            p = Path(td) / "sample.txt"
            p.write_bytes(b"\xef\xbb\xbfA\r\n\r\nB\rC")
            self.assertEqual(pt.checked_input(p), "A\n\nB\nC")

    def test_non_text_input_rejected(self):
        with TemporaryDirectory() as td:
            p = Path(td) / "sample.png"
            p.write_text("synthetic")
            with self.assertRaises(ValueError):
                pt.checked_input(p)

    def test_dry_run_does_not_call_api(self):
        with TemporaryDirectory() as td:
            p = Path(td) / "sample.txt"
            p.write_text("Original synthetic sample.", encoding="utf-8")
            opts = SimpleNamespace(input=p, book_id="the-demon-king-overrun",
                                   chapter=137, context=None, output=None,
                                   chunk_chars=800, dry_run=True)
            private = Path(td) / "private"
            with patch.object(pt, "PRIVATE_HOME", private), patch.object(pt, "chat", side_effect=AssertionError("Unexpected API call")):
                with contextlib.redirect_stdout(io.StringIO()):
                    pt.translate(opts)
            self.assertFalse(private.exists())

    def test_http_remote_endpoint_rejected(self):
        with self.assertRaises(ValueError):
            pt.chat("http://example.org/chat", "test", "model", [])

if __name__ == "__main__":
    unittest.main()
