import copy
import unittest
from scripts.check_source_queue import validate

def fixture():
    q = {"book_id":"the-demon-king-overrun","source_import":"user_supplied_text_only",
         "public_chapter_publication":"blocked_until_license","defer_chapters_before":137,
         "priority_arc":{"first_novel_chapter":137,"end_novel_chapter":None,"end_confidence":"not_verified",
                         "completion_candidate_novel_chapter":154,"completion_candidate_confidence":"tentative",
                         "confirmed_mobile_by_novel_chapter":160,
                         "story_beats":[{"chapter":137,"status":"located","source_url":"https://example.org/index"}]}}
    r = {"book_id":"the-demon-king-overrun",
         "public_release":{"rights_status":"pending","translation_rights_verified":False,
                           "online_distribution_rights_verified":False,"allowed_to_publish":False,
                           "permission_document":None},
         "personal_reading":{"source_origin":"user_supplied_local_text_only",
                             "remote_ai_requires_explicit_opt_in":True,
                             "upload_to_github":False,"auto_scrape":False,"auto_publish":False},
         "sources":[{"url":"https://example.org/index","may_fetch_full_chapters":False,
                     "may_translate_or_republish":False,"license_evidence":None}]}
    c = {"works":[{"book_id":"the-demon-king-overrun","rights_status":"pending",
                   "allowed_to_publish":False,"allowed_to_translate":False}]}
    return q,r,c

class SourceQueueTests(unittest.TestCase):
    def assertBad(self, args, fragment):
        errors = validate(*args)
        self.assertTrue(any(fragment in e for e in errors), errors)
    def test_baseline(self):
        self.assertEqual(validate(*fixture()), [])
    def test_no_unverified_arc_end(self):
        args = fixture();args[0]["priority_arc"]["end_novel_chapter"] = 155
        self.assertBad(args, "unverified arc end")
    def test_no_chapter_before_137(self):
        args = fixture();args[0]["priority_arc"]["story_beats"][0]["chapter"] = 136
        self.assertBad(args, "invalid novel chapter")
    def test_no_full_text(self):
        args = fixture();args[0]["priority_arc"]["story_beats"][0]["chapter_text"] = "test"
        self.assertBad(args, "chapter text must not be stored")
    def test_no_scraping(self):
        args = fixture();args[1]["personal_reading"]["auto_scrape"] = True
        self.assertBad(args, "auto_scrape")
    def test_no_public_rights_inference(self):
        args = fixture();args[1]["public_release"]["allowed_to_publish"] = True
        self.assertBad(args, "allowed_to_publish")
    def test_no_http_source(self):
        args = fixture();args[1]["sources"][0]["url"] = "http://example.org"
        self.assertBad(args, "HTTPS URL required")
    def test_no_canon_unlock(self):
        args = fixture();args[2]["works"][0]["allowed_to_translate"] = True
        self.assertBad(args, "translation pipeline remains disabled")

if __name__ == "__main__":
    unittest.main()
