"""Synthetic provenance tests; no comic images or original chapters included."""
import copy
import unittest
from translation.edition_provenance_lint import check

def sample():
    return {
        "requested_source": "https://selected.example/series",
        "sources": [
            {"id":"mirror", "url":"https://mirror.example/series", "medium":"manhwa_vi_panel", "selected_baseline":False},
            {"id":"en", "url":"https://english.example/series", "medium":"novel_english_secondary", "selected_baseline":False}
        ],
        "observations": [
            {"id":"p1", "source_edition_id":"mirror", "medium":"manhwa_vi_panel",
             "source_url":"https://img.mirror.example/panel.jpg", "panel_number":3,
             "selected_baseline_verified":False, "edition_match_status":"unverified",
             "speaker_identity_status":"unknown","addressee_identity_status":"unknown"}
        ]
    }

class EditionProvenanceTests(unittest.TestCase):
    def assertProblem(self, data, part):
        self.assertTrue(any(part in p for p in check(data)), check(data))

    def test_valid_mirror_is_not_primary(self):
        self.assertEqual(check(sample()), [])

    def test_missing_edition_reference(self):
        data=sample();data["observations"][0]["source_edition_id"]="unknown"
        self.assertProblem(data,"unknown edition ID")

    def test_mirror_cannot_claim_selected(self):
        data=sample();data["observations"][0]["selected_baseline_verified"]=True
        self.assertProblem(data,"mirror cannot certify")

    def test_mirror_source_cannot_be_selected(self):
        data=sample();data["sources"][0]["selected_baseline"]=True
        self.assertProblem(data,"mirror cannot impersonate")

    def test_wrong_image_host(self):
        data=sample();data["observations"][0]["source_url"]="https://unrelated.example/11.jpg"
        self.assertProblem(data,"not attributable")

    def test_panel_number_required(self):
        data=sample();data["observations"][0].pop("panel_number")
        self.assertProblem(data,"panel_number")

    def test_speaker_status_required(self):
        data=sample();data["observations"][0].pop("addressee_identity_status")
        self.assertProblem(data,"speaker/addressee")

    def test_cannot_claim_primary_without_review(self):
        data=sample()
        data["sources"].append({"id":"selected","url":"https://selected.example/series",
                                "medium":"manhwa_vi_panel","selected_baseline":True})
        data["observations"][0].update(source_edition_id="selected",
                                       source_url="https://selected.example/panel-4.jpg",
                                       selected_baseline_verified=True,edition_match_status="confirmed")
        self.assertProblem(data,"independent visual review")

    def test_primary_with_explicit_review_metadata(self):
        data=sample()
        data["sources"].append({"id":"selected","url":"https://selected.example/series",
                                "medium":"manhwa_vi_panel","selected_baseline":True})
        data["observations"][0].update(source_edition_id="selected",
                                       source_url="https://selected.example/panel-4.jpg",
                                       selected_baseline_verified=True,edition_match_status="confirmed",
                                       visual_review_id="RV-4",visual_reviewed_by="editor")
        self.assertEqual(check(data), [])

    def test_novel_metadata_cannot_certify_primary(self):
        data=sample()
        data["observations"][0].update(source_edition_id="en",medium="novel_english_secondary",
                                       source_url="https://english.example/chapter-1",
                                       selected_baseline_verified=True,edition_match_status="not_applicable")
        self.assertProblem(data,"non-Vietnamese-panel")

    def test_secondary_cannot_claim_edition_match(self):
        data=sample()
        data["observations"][0].update(source_edition_id="en",medium="novel_english_secondary",
                                       source_url="https://english.example/chapter-1",
                                       selected_baseline_verified=False,edition_match_status="confirmed")
        self.assertProblem(data,"cannot claim Vietnamese edition match")

if __name__=="__main__":
    unittest.main()
