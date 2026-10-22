"""Original-demo and synthetic regression cases. No unlicensed novel input."""
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from tools.independent_qa import inspect, digest, save_private

ROOT = Path(__file__).resolve().parents[1]

def setup():
    canon = {
        "works": [{"book_id": "demo", "rights_status": "cleared"}],
        "characters": [{"id": "a", "book_id": "demo"}, {"id": "b", "book_id": "demo"}],
        "relationships": [
            {"book_id": "demo", "speaker": "a", "addressee": "b", "phase": "friends",
             "self_pronoun": "em", "address_pronoun": "chị", "locked": True,
             "reviewed_by": "demo", "evidence": "synthetic", "valid_from_chapter": 1},
            {"book_id": "demo", "speaker": "b", "addressee": "a", "phase": "friends",
             "self_pronoun": "chị", "address_pronoun": "em", "locked": True,
             "reviewed_by": "demo", "evidence": "synthetic", "valid_from_chapter": 1}
        ], "terms": [], "relationship_transitions": []}
    return canon

def dialogue():
    text = "“Chị ơi, em đã tới.”\n\n“Chị nghe rồi, em à.”"
    notes = {"book_id": "demo", "chapter": 1, "dialogues": [
        {"paragraph": 0, "speaker": "a", "addressee": "b", "phase": "friends",
         "self_pronoun": "em", "address_pronoun": "chị", "review_status": "approved", "evidence": "demo p0"},
        {"paragraph": 1, "speaker": "b", "addressee": "a", "phase": "friends",
         "self_pronoun": "chị", "address_pronoun": "em", "review_status": "approved", "evidence": "demo p1"}]}
    return text, notes

def run(source="Có 12 bức thư.\n\nTrời đã sáng.", draft=None, canon=None, annotations=None, **kwargs):
    return inspect(source, draft if draft is not None else source,
                   canon if canon is not None else setup(), "demo", 1,
                   annotations=annotations, **kwargs)

def codes(result):
    return [x["code"] for x in result["findings"]]

class IndependentQATests(unittest.TestCase):
    def test_never_auto_pass(self):
        r = run()
        self.assertEqual(r["qa_status"], "needs_review")
        self.assertFalse(r["publishable"])
        self.assertTrue(r["manual_review_required"])
        self.assertTrue(all(v == "pending" for v in r["manual_checks"].values()))

    def test_missing_paragraph(self):
        self.assertIn("PARAGRAPH_COUNT_MISMATCH", codes(run(draft="Có 12 bức thư.")))

    def test_number_drift(self):
        self.assertIn("NUMBERS_CHANGED", codes(run(draft="Có 13 bức thư.\n\nTrời đã sáng.")))

    def test_unresolved_pronoun(self):
        self.assertIn("UNRESOLVED_MARKER", codes(run(draft="Có 12 bức thư.\n\n[CẦN_XƯNG_HÔ]")))

    def test_duplicate_paragraph(self):
        self.assertIn("SUSPECT_DUPLICATE_PARAGRAPH", codes(run(source="Một.\n\nHai.", draft="Lặp.\n\nLặp.")))

    def test_untranslated_hangul_warning(self):
        r = run(draft="Có 12 bức thư.\n\n안녕하세요")
        self.assertIn("UNTRANSLATED_HANGUL", codes(r))
        self.assertEqual(r["qa_status"], "needs_review")

    def test_hash_mismatch(self):
        self.assertIn("SOURCE_HASH_MISMATCH", codes(run(expected_hash="0" * 64)))
        source = "Có 12 bức thư.\n\nTrời đã sáng."
        self.assertNotIn("SOURCE_HASH_MISMATCH", codes(run(expected_hash=digest(source))))

    def test_locked_glossary_only(self):
        canon = setup()
        canon["terms"] = [{"book_id": "demo", "source": "bức thư", "target": "thư tín", "locked": True}]
        self.assertIn("LOCKED_TERM_MISSING", codes(run(canon=canon)))
        canon["terms"][0]["locked"] = False
        self.assertNotIn("LOCKED_TERM_MISSING", codes(run(canon=canon)))

    def test_dialogue_needs_annotation(self):
        text, notes = dialogue()
        self.assertIn("DIALOGUE_ANNOTATION_MISSING", codes(run(source=text)))
        self.assertEqual(run(source=text, annotations=notes)["blockers"], 0)

    def test_reverse_edge_not_inferred(self):
        text, notes = dialogue()
        canon = setup()
        canon["relationships"].pop()
        self.assertIn("DIRECTED_RELATION_UNVERIFIED", codes(run(source=text, canon=canon, annotations=notes)))

    def test_pronoun_drift(self):
        text, notes = dialogue()
        notes["dialogues"][0]["self_pronoun"] = "tôi"
        r = run(source=text, annotations=notes)
        self.assertIn("PRONOUN_DRIFT", codes(r))
        self.assertIn("PRONOUN_ABSENT_FROM_SPEECH", codes(r))

    def test_narration_not_pronoun_evidence(self):
        text, notes = dialogue()
        text = '“Tôi tới.” An nghĩ đến chị và em.\n\n“Chị nghe rồi, em à.”'
        self.assertIn("PRONOUN_ABSENT_FROM_SPEECH", codes(run(source=text, annotations=notes)))

    def test_unreviewed_dialogue(self):
        text, notes = dialogue()
        notes["dialogues"][0]["review_status"] = "candidate"
        self.assertIn("DIALOGUE_REVIEW_MISSING", codes(run(source=text, annotations=notes)))

    def test_phase_transition_needs_review(self):
        text, notes = dialogue()
        canon = setup()
        canon["relationships"].append({
            "book_id": "demo", "speaker": "a", "addressee": "b", "phase": "allies",
            "self_pronoun": "chị", "address_pronoun": "em", "locked": True,
            "reviewed_by": "demo", "evidence": "synthetic", "valid_from_chapter": 1})
        notes["dialogues"][1].update(speaker="a", addressee="b", phase="allies")
        self.assertIn("PHASE_TRANSITION_UNREVIEWED", codes(run(source=text, canon=canon, annotations=notes)))
        canon["relationship_transitions"].append({
            "book_id": "demo", "speaker": "a", "addressee": "b",
            "from_phase": "friends", "to_phase": "allies", "chapter": 1,
            "paragraph": 1, "review_id": "demo-rev", "reviewed_by": "demo",
            "evidence": "synthetic", "trigger": "synthetic change"})
        self.assertNotIn("PHASE_TRANSITION_UNREVIEWED", codes(run(source=text, canon=canon, annotations=notes)))

    def test_no_raw_text_in_report(self):
        r = run(source="Bí mật 12.\n\nKhông chia sẻ.")
        self.assertNotIn("Bí mật", json.dumps(r, ensure_ascii=False))
        self.assertNotIn("Không chia sẻ", json.dumps(r, ensure_ascii=False))

    def test_report_cannot_escape_private_home(self):
        with TemporaryDirectory() as td:
            root = Path(td) / "private"
            save_private({"qa_status": "needs_review"}, root / "report.json", root=root)
            self.assertTrue((root / "report.json").exists())
            with self.assertRaises(ValueError):
                save_private({}, Path(td) / "leak.json", root=root)

    def test_original_demo_chapters_are_structurally_clean_not_approved(self):
        canon = json.loads((ROOT / "translation/canon.json").read_text(encoding="utf-8"))
        for name in ("binh-minh-01.json", "binh-minh-02.json"):
            ch = json.loads((ROOT / "data/chapters" / name).read_text(encoding="utf-8"))
            prose = "\n\n".join(ch["paragraphs"])
            notes = {"book_id": ch["bookId"], "chapter": ch["chapter"],
                     "scene": ch.get("scene"), "dialogues": ch["dialogues"]}
            r = inspect(prose, prose, canon, ch["bookId"], ch["chapter"], notes)
            self.assertEqual(r["blockers"], 0, (name, r["findings"]))
            self.assertEqual(r["qa_status"], "needs_review")
