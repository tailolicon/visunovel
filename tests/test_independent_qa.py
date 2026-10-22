"""Synthetic, offline regression tests. No third-party chapter content."""
import copy
import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from translation import independent_qa as qa

SRC = "The door opened.\n\nThe worker left."
DST = "Cửa mở ra.\n\nNgười thợ rời đi."
CANON = {
    "works": [
        {"book_id": "novel", "rights_status": "pending", "allowed_to_publish": False},
        {"book_id": "demo", "rights_status": "cleared", "allowed_to_publish": True}
    ],
    "characters": [], "terms": [],
    "relationships": [{
        "book_id": "demo", "speaker": "a", "addressee": "b", "phase": "early",
        "valid_from_chapter": 1, "valid_to_chapter": None, "locked": True,
        "self_pronoun": "em", "address_pronoun": "chị",
        "evidence": "Synthetic demo source", "reviewed_by": "demo-author"
    }]
}

def meta(book="novel", source=SRC):
    return {
        "book_id": book, "chapter": 137, "source_sha256": qa.digest(source),
        "qa_status": "needs_review", "draft_only": True, "public_release_authorized": False
    }

def run(draft=DST, source=SRC, manifest=None, book="novel", canon=CANON):
    return qa.audit(source, draft, book, 137, canon, meta(book, source) if manifest is None else manifest)

def reviewed(speaker="a", addressee="b", phase="early"):
    return {
        "paragraph": 0, "speaker": speaker, "addressee": addressee, "phase": phase,
        "self_pronoun": "em", "address_pronoun": "chị",
        "source_scene_ref": "synthetic demo scene 1", "reviewed_by": "demo-author",
        "review_id": "demo-review-1", "review_status": "approved"
    }

class StructuralQATests(unittest.TestCase):
    def assertBlock(self, result, name):
        self.assertIn(name, result["blockers"], result)

    def test_private_draft_can_pass_structural_while_public_blocked(self):
        result = run()
        self.assertEqual(result["blockers"], [])
        self.assertEqual(result["private_structural_qa"], "PASS_STRUCTURAL_ONLY")
        self.assertIn("public_rights_pending", result["release_blockers"])
        self.assertEqual(result["public_release"], "BLOCKED")
        self.assertEqual(result["literary_qa"], "NOT_REVIEWED")

    def test_demo_still_not_literary_approved(self):
        self.assertEqual(run(book="demo")["literary_qa"], "NOT_REVIEWED")

    def test_missing_paragraph(self):
        self.assertBlock(run(draft="Cửa mở ra."), "paragraph_count_mismatch")

    def test_unresolved_pronoun(self):
        self.assertBlock(run(draft=DST+" [CẦN_XƯNG_HÔ]"), "unresolved_address")

    def test_untranslated_korean_is_flagged(self):
        self.assertIn("possible_untranslated_korean", run(draft=DST+" 안녕")["warnings"])

    def test_source_checksum(self):
        manifest = meta()
        manifest["source_sha256"] = "wrong"
        self.assertBlock(run(manifest=manifest), "source_checksum_mismatch")

    def test_draft_checksum(self):
        manifest = meta()
        manifest["draft_sha256"] = "wrong"
        self.assertBlock(run(manifest=manifest), "draft_checksum_mismatch")

    def test_unapproved_state(self):
        manifest = meta()
        manifest.update(qa_status="approved", public_release_authorized=True)
        result = run(manifest=manifest)
        self.assertBlock(result, "unreviewed_approval_claim")
        self.assertBlock(result, "unsafe_publication_flag")

    def test_invalid_manifest_identity(self):
        manifest = meta()
        manifest["chapter"] = True
        self.assertBlock(run(manifest=manifest), "manifest_identity_mismatch")

    def test_hash_normalized_newlines(self):
        self.assertEqual(qa.digest("a\r\nb"), qa.digest("a\nb"))

    def test_report_does_not_contain_text(self):
        self.assertNotIn(SRC, json.dumps(run(), ensure_ascii=False))
        self.assertNotIn(DST, json.dumps(run(), ensure_ascii=False))

    def test_no_auto_inference_of_reverse_direction(self):
        manifest = meta("demo")
        manifest["dialogue_reviews"] = [reviewed("b", "a")]
        self.assertBlock(run(book="demo", manifest=manifest), "unverified_directed_pronoun_pair")

    def test_approved_directed_pair_requires_matching_phase(self):
        manifest = meta("demo")
        manifest["dialogue_reviews"] = [reviewed(phase="later")]
        self.assertBlock(run(book="demo", manifest=manifest), "unverified_directed_pronoun_pair")

    def test_reviewed_synthetic_pair_is_structural_only(self):
        manifest = meta("demo")
        manifest["dialogue_reviews"] = [reviewed()]
        result = run(book="demo", manifest=manifest)
        self.assertEqual(result["blockers"], [])
        self.assertEqual(result["literary_qa"], "NOT_REVIEWED")

    def test_missing_scene_review(self):
        manifest = meta("demo")
        row = reviewed()
        row.pop("source_scene_ref")
        manifest["dialogue_reviews"] = [row]
        self.assertBlock(run(book="demo", manifest=manifest), "approved_dialogue_lacks_scene_review")

    def test_pending_pair_is_not_approved(self):
        manifest = meta("demo")
        row = reviewed()
        row["review_status"] = "pending"
        manifest["dialogue_reviews"] = [row]
        result = run(book="demo", manifest=manifest)
        self.assertIn("directed_dialogue_review_pending", result["warnings"])

    def test_duplicate_pair_annotation(self):
        manifest = meta("demo")
        manifest["dialogue_reviews"] = [reviewed(), reviewed()]
        self.assertBlock(run(book="demo", manifest=manifest), "duplicate_directed_dialogue_review")

    def test_invalid_paragraph_index(self):
        manifest = meta("demo")
        row = reviewed()
        row["paragraph"] = 100
        manifest["dialogue_reviews"] = [row]
        self.assertBlock(run(book="demo", manifest=manifest), "dialogue_paragraph_out_of_range")

    def test_no_manifest_is_not_approval(self):
        result = qa.audit(SRC, DST, "demo", 137, CANON)
        self.assertIn("directed_dialogue_review_missing", result["warnings"])

class PrivacyCLITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.private = self.root / "private"
        self.source = self.root / "source.txt"
        self.draft = self.root / "draft.txt"
        self.source.write_text(SRC, encoding="utf-8")
        self.draft.write_text(DST, encoding="utf-8")

    def cli(self, extra=()):
        argv = ["independent_qa", str(self.source), str(self.draft),
                "--book-id", "nhung-la-thu-binh-minh", "--chapter", "137", *extra]
        with patch.object(qa, "PRIVATE_HOME", self.private), patch.object(sys, "argv", argv):
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                return qa.main()

    def test_private_report_created_with_restrictive_permissions(self):
        self.assertEqual(self.cli(), 0)
        files = list((self.private / "qa").glob("*.json"))
        self.assertEqual(len(files), 1)
        self.assertEqual(os.stat(files[0]).st_mode & 0o777, 0o600)
        self.assertEqual(os.stat(self.private).st_mode & 0o777, 0o700)
        self.assertEqual(json.loads(files[0].read_text())["public_release"], "BLOCKED")

    def test_cannot_write_report_outside_private_home(self):
        external = self.root / "leak.json"
        self.assertEqual(self.cli(["--report", str(external)]), 2)
        self.assertFalse(external.exists())

    def test_existing_report_never_overwritten(self):
        self.assertEqual(self.cli(), 0)
        path = next((self.private / "qa").glob("*.json"))
        before = path.read_bytes()
        self.assertEqual(self.cli(), 2)
        self.assertEqual(path.read_bytes(), before)

    def test_symlink_source_rejected(self):
        link = self.root / "link.txt"
        link.symlink_to(self.source)
        self.source = link
        self.assertEqual(self.cli(), 2)

    def test_repo_input_rejected(self):
        self.source = qa.ROOT / "tests" / "example-source.txt"
        self.assertEqual(self.cli(), 2)

    def test_manifest_inside_repo_rejected(self):
        self.assertEqual(self.cli(["--manifest", str(qa.ROOT / "translation" / "canon.json")]), 2)

if __name__ == "__main__":
    unittest.main()
