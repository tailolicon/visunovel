"""Synthetic regression tests for private draft QA."""
import unittest
from translation.independent_qa import audit, digest

SRC = "The door opened.\n\nThe worker left."
DST = "Cửa mở ra.\n\nNgười thợ rời đi."
CANON = {"works": [
    {"book_id":"novel", "rights_status":"pending", "allowed_to_publish":False},
    {"book_id":"demo", "rights_status":"cleared", "allowed_to_publish":True}
], "terms":[]}

def run(draft=DST, source=SRC, meta=None, book="novel", canon=CANON):
    if meta is None:
        meta={"book_id":book,"chapter":137,"source_sha256":digest(source),
              "qa_status":"needs_review","draft_only":True,
              "public_release_authorized":False}
    return audit(source,draft,book,137,canon,meta)

class DraftQATests(unittest.TestCase):
    def test_private_work_not_publishable(self):
        r=run()
        self.assertIn("public_rights_pending",r["blockers"])
        self.assertEqual(r["public_release"],"BLOCKED")

    def test_demo_still_needs_editor(self):
        r=run(book="demo")
        self.assertEqual(r["blockers"],[])
        self.assertEqual(r["literary_qa"],"NOT_REVIEWED")

    def test_missing_paragraph(self):
        self.assertIn("paragraph_count_mismatch",run(draft="Cửa mở ra.")["blockers"])

    def test_unresolved_pronoun(self):
        self.assertIn("unresolved_address",run(draft=DST+" [CẦN_XƯNG_HÔ]")["blockers"])

    def test_korean_residue(self):
        self.assertIn("possible_untranslated_korean",run(draft=DST+" 안녕")["warnings"])

    def test_checksum(self):
        m={"book_id":"novel","chapter":137,"source_sha256":"bad"}
        self.assertIn("source_checksum_mismatch",run(meta=m)["blockers"])

    def test_unapproved_state(self):
        m={"book_id":"novel","chapter":137,"source_sha256":digest(SRC),
           "qa_status":"approved","public_release_authorized":True}
        r=run(meta=m)
        self.assertIn("unreviewed_approval_claim",r["blockers"])
        self.assertIn("unsafe_publication_flag",r["blockers"])

    def test_hash_newlines(self):
        self.assertEqual(digest("a\r\nb"),digest("a\nb"))

    def test_no_chapter_text_in_report(self):
        self.assertNotIn(SRC,str(run()))
        self.assertNotIn(DST,str(run()))

if __name__=="__main__":
    unittest.main()
