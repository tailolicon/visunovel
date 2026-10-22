"""Synthetic provenance regression tests: not a recreation of manga or novel text."""
import copy
import unittest
from translation.evidence_lint import validate

def fixture():
    data={
        "book_id":"the-demon-king-overrun",
        "scope":{"vn_manhwa_chapters_in_scope":[1,20],"novel_secondary_chapters_in_scope":[1,20]},
        "requested_source":"https://example.com/series",
        "editorial_release_gate":"NOT_READY_FOR_CANON_LOCK",
        "candidate_identities":[
            {"id":"a","observed":["A"],"sources":["https://example.com/1"],"name_locked":False,"pronoun_locked":False},
            {"id":"b","observed":["B"],"sources":["https://example.com/2"],"name_locked":False,"pronoun_locked":False}],
        "observations":[{"id":"panel1","medium":"manhwa_vi_panel","chapter":1,
                         "source_url":"https://example.com/images/1.jpg","chapter_url":"https://example.com/chapter-1",
                         "claim_vi":"A có mặt trong cảnh này.","about":["a"],"evidence_grade":"panel_observed",
                         "approval":"scene_only"}]
    }
    canon={"relationship_review_queue":[{"book_id":data["book_id"],"speaker_candidate":"a",
           "addressee_candidate":"b","source_evidence_id":"panel1","locked":False,
           "review_status":"pending_panel_verification","proposed_self_pronoun":None,"proposed_address_pronoun":None}],
           "relationships":[]}
    bible={"facts":[{"book_id":data["book_id"],"status":"candidate","locked":False}]}
    return data,canon,bible

class EvidenceTests(unittest.TestCase):
    def assertIssue(self,issues,fragment):
        self.assertTrue(any(fragment in issue for issue in issues),issues)

    def test_baseline(self):
        self.assertEqual(validate(*fixture()),[])

    def test_no_manga_after_chapter_twenty(self):
        data,canon,bible=fixture();data["observations"][0]["chapter"]=21
        self.assertIssue(validate(data,canon,bible),"outside 1–20")

    def test_no_auto_locked_identity(self):
        data,canon,bible=fixture();data["candidate_identities"][0]["name_locked"]=True
        self.assertIssue(validate(data,canon,bible),"candidate must not be locked")

    def test_no_pronoun_promotion(self):
        data,canon,bible=fixture();canon["relationship_review_queue"][0]["proposed_self_pronoun"]="ta"
        self.assertIssue(validate(data,canon,bible),"assigned pronouns")

    def test_secondary_text_not_manga_panel(self):
        data,canon,bible=fixture();data["observations"][0]["medium"]="novel_english_secondary"
        self.assertIssue(validate(data,canon,bible),"non-panel cannot claim visual verification")

    def test_unverified_world_lore_not_promoted(self):
        data,canon,bible=fixture();bible["facts"][0]["status"]="confirmed"
        self.assertIssue(validate(data,canon,bible),"literary candidate must remain unlocked")

    def test_required_evidence_reference(self):
        data,canon,bible=fixture();canon["relationship_review_queue"][0]["source_evidence_id"]="missing"
        self.assertIssue(validate(data,canon,bible),"evidence reference missing")

    def test_no_source_text_copy_in_ledger(self):
        data,canon,bible=fixture();data["observations"][0]["full_text"]="not appropriate"
        self.assertIssue(validate(data,canon,bible),"no original panels/chapter text")

if __name__=="__main__":
    unittest.main()
