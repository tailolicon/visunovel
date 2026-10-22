"""Offline regression tests using only original demo fixtures."""
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import private_context as pc

CANON = {
    "works": [{"book_id": "original-demo"}],
    "characters": [
        {"id": "ly", "book_id": "original-demo", "locked": True, "canonical_name": "Ly", "aliases": []},
        {"id": "chau", "book_id": "original-demo", "locked": True, "canonical_name": "Châu", "aliases": []}
    ],
    "relationships": [
        {"book_id": "original-demo", "locked": True, "reviewed_by": "editor", "evidence": "original demo",
         "speaker": "ly", "addressee": "chau", "phase": "acquaintances", "valid_from_chapter": 1,
         "valid_to_chapter": None, "self_pronoun": "em", "address_pronoun": "chị"},
        {"book_id": "original-demo", "locked": True, "reviewed_by": "editor", "evidence": "original demo",
         "speaker": "chau", "addressee": "ly", "phase": "acquaintances", "valid_from_chapter": 1,
         "valid_to_chapter": None, "self_pronoun": "chị", "address_pronoun": "em"}
    ],
    "terms": []
}

class PrivateContextTests(unittest.TestCase):
    def test_directed_edges(self):
        context, issues = pc.chapter_context(CANON, "original-demo", 1, "Ly nhìn Châu.", [
            {"paragraph": 0, "speaker": "ly", "addressee": "chau", "phase": "acquaintances"}])
        self.assertEqual(issues, [])
        edges = {(r["speaker"], r["addressee"]): r for r in context["directed_relations"]}
        self.assertEqual(edges[("ly", "chau")]["self_pronoun"], "em")
        self.assertEqual(edges[("chau", "ly")]["self_pronoun"], "chị")

    def test_unknown_speaker_deferred(self):
        _, issues = pc.chapter_context(CANON, "original-demo", 1, "Ly nhìn Châu.", [
            {"paragraph": 0, "speaker": "unknown", "addressee": "chau", "phase": "acquaintances"}])
        self.assertTrue(any("defer" in i for i in issues))

    def test_wrong_phase_deferred(self):
        _, issues = pc.chapter_context(CANON, "original-demo", 1, "Ly nhìn Châu.", [
            {"paragraph": 0, "speaker": "ly", "addressee": "chau", "phase": "enemies"}])
        self.assertTrue(any("defer" in i for i in issues))

    def test_unknown_work_rejected(self):
        with self.assertRaises(ValueError):
            pc.chapter_context(CANON, "other", 1, "Ly")

    def test_pronoun_and_paragraph_qa(self):
        self.assertEqual(pc.qa_paragraphs("Một.\n\nHai.", "[CẦN_XƯNG_HÔ]"),
                         ["PARAGRAPH_COUNT", "PRONOUN_UNRESOLVED"])

    def test_checkpoint_invalidation(self):
        key = pc.resume_guard(None, "source", CANON, {}, "model-a", 3500)
        self.assertEqual(key, pc.resume_guard({"job_sha256": key}, "source", CANON, {}, "model-a", 3500))
        with self.assertRaises(ValueError):
            pc.resume_guard({"job_sha256": key}, "source", CANON, {}, "model-b", 3500)

    def test_private_path_guard(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "private"
            self.assertEqual(pc.private_path(root / "draft.txt", root=root), root / "draft.txt")
            with self.assertRaises(ValueError):
                pc.private_path(Path(tmp) / "leak.txt", root=root)

if __name__ == "__main__":
    unittest.main()
