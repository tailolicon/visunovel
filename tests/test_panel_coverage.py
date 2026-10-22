"""Synthetic tests for verified comic-panel coverage."""
import copy
import unittest
from translation.verify_panel_coverage import check

def sample():
    return {
        "editorial_release_gate": "NOT_READY_FOR_CANON_LOCK",
        "covered_vn_manhwa_panels": {"chapters": [1], "panel_count": 1},
        "observations": [{
            "id": "p1", "chapter": 1, "medium": "manhwa_vi_panel",
            "evidence_grade": "panel_observed", "approval": "scene_only",
            "source_url": "https://example.org/panel-1.jpg",
        }],
    }

class CoverageTests(unittest.TestCase):
    def test_valid_sample(self):
        self.assertEqual(check(sample()), [])

    def test_cannot_claim_all_chapters_from_one_image(self):
        data = sample()
        data["covered_vn_manhwa_panels"]["chapters"] = list(range(1, 21))
        self.assertTrue(check(data))

    def test_duplicate_claims_same_image_do_not_inflate_count(self):
        data = sample()
        duplicate = copy.deepcopy(data["observations"][0])
        duplicate["id"] = "p2"
        data["observations"].append(duplicate)
        self.assertEqual(check(data), [])

    def test_english_novel_cannot_claim_vietnamese_dialogue_approval(self):
        data = sample()
        data["observations"][0]["medium"] = "novel_english_secondary"
        data["observations"][0]["evidence_grade"] = "chapter_text_observed"
        data["covered_vn_manhwa_panels"] = {"chapters": [], "panel_count": 0}
        self.assertTrue(check(data))

    def test_wrong_medium_grade_rejected(self):
        data = sample()
        data["observations"][0]["evidence_grade"] = "chapter_text_observed"
        self.assertTrue(check(data))

    def test_out_of_scope_chapter_rejected(self):
        data = sample()
        data["observations"][0]["chapter"] = 21
        self.assertTrue(check(data))

    def test_unreviewed_cannot_unlock_canon(self):
        data = sample()
        data["editorial_release_gate"] = "READY"
        self.assertTrue(check(data))

if __name__ == "__main__":
    unittest.main()
