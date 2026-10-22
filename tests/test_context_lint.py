"""Deterministic synthetic cases; never use unlicensed source novel text."""
import copy
import unittest

from translation.context_lint import validate


def fixture():
    book = 'demo'
    canon = {
        'works': [{'book_id': book}],
        'characters': [
            {'id': 'a', 'book_id': book, 'canonical_name': 'An', 'aliases': ['A']},
            {'id': 'b', 'book_id': book, 'canonical_name': 'Bình', 'aliases': []},
        ],
        'relationships': [
            {'id': 'a-b-early', 'book_id': book, 'speaker': 'a', 'addressee': 'b', 'phase': 'early', 'valid_from_chapter': 1, 'valid_to_chapter': None, 'self_pronoun': 'em', 'address_pronoun': 'chị', 'locked': True, 'evidence': 'Demo author voice in ch1', 'reviewed_by': 'demo-editor'},
            {'id': 'b-a-early', 'book_id': book, 'speaker': 'b', 'addressee': 'a', 'phase': 'early', 'valid_from_chapter': 1, 'valid_to_chapter': None, 'self_pronoun': 'chị', 'address_pronoun': 'em', 'locked': True, 'evidence': 'Demo author voice in ch1', 'reviewed_by': 'demo-editor'},
        ],
        'relationship_transitions': [], 'terms': [], 'term_review_queue': [], 'relationship_review_queue': [],
    }
    chapters = [
        {'bookId': book, 'chapter': 1, 'scene': 'post-office', 'paragraphs': ['“Chị đợi em sao?” An hỏi.', '“Chị đã chờ em.” Bình đáp.'],
         'dialogues': [
             {'paragraph': 0, 'speaker': 'a', 'addressee': 'b', 'phase': 'early', 'self_pronoun': 'em', 'address_pronoun': 'chị', 'review_status': 'approved', 'evidence': 'ch1 p0'},
             {'paragraph': 1, 'speaker': 'b', 'addressee': 'a', 'phase': 'early', 'self_pronoun': 'chị', 'address_pronoun': 'em', 'review_status': 'approved', 'evidence': 'ch1 p1'},
         ]},
        {'bookId': book, 'chapter': 2, 'scene': 'tower', 'paragraphs': ['“Em biết rồi, chị ạ.”', '“Chị cũng biết, em à.”'],
         'dialogues': [
             {'paragraph': 0, 'speaker': 'a', 'addressee': 'b', 'phase': 'early', 'self_pronoun': 'em', 'address_pronoun': 'chị', 'review_status': 'approved', 'evidence': 'ch2 p0'},
             {'paragraph': 1, 'speaker': 'b', 'addressee': 'a', 'phase': 'early', 'self_pronoun': 'chị', 'address_pronoun': 'em', 'review_status': 'approved', 'evidence': 'ch2 p1'},
         ]},
    ]
    return canon, chapters


def transition_fixture():
    canon, chapters = fixture()
    canon['relationships'][0]['valid_to_chapter'] = 1
    canon['relationships'].append({'id': 'a-b-late', 'book_id': 'demo', 'speaker': 'a', 'addressee': 'b', 'phase': 'allies', 'valid_from_chapter': 2, 'valid_to_chapter': None, 'self_pronoun': 'tôi', 'address_pronoun': 'cô', 'locked': True, 'evidence': 'Demo scene of explicit address change', 'reviewed_by': 'demo-editor'})
    chapters[1]['paragraphs'][0] = '“Tôi hiểu rồi, cô ạ.”'
    chapters[1]['dialogues'][0].update(phase='allies', self_pronoun='tôi', address_pronoun='cô')
    return canon, chapters


class ContextIntegrityTests(unittest.TestCase):
    def assertIssue(self, errors, needle):
        self.assertTrue(any(needle in x for x in errors), errors)

    def test_baseline_passes(self):
        canon, chapters = fixture()
        self.assertEqual(validate(canon, chapters), [])

    def test_duplicate_character_id(self):
        canon, chapters = fixture()
        canon['characters'].append(copy.deepcopy(canon['characters'][0]))
        self.assertIssue(validate(canon, chapters), 'duplicate character id')

    def test_alias_collision_is_per_work(self):
        canon, chapters = fixture()
        canon['characters'][1]['aliases'] = ['  a  ']
        self.assertIssue(validate(canon, chapters), 'identity alias collision')

    def test_same_alias_in_different_work_is_allowed(self):
        canon, chapters = fixture()
        canon['works'].append({'book_id': 'other'})
        canon['characters'].append({'id': 'c', 'book_id': 'other', 'canonical_name': 'An', 'aliases': []})
        self.assertEqual(validate(canon, chapters), [])

    def test_duplicate_relation_id(self):
        canon, chapters = fixture()
        canon['relationships'][1]['id'] = canon['relationships'][0]['id']
        self.assertIssue(validate(canon, chapters), 'duplicate relationship id')

    def test_overlapping_relation_same_phase(self):
        canon, chapters = fixture()
        new = copy.deepcopy(canon['relationships'][0]); new['id'] = 'duplicate-interval'
        canon['relationships'].append(new)
        self.assertIssue(validate(canon, chapters), 'ambiguous overlapping locked edges')

    def test_overlapping_phases_without_scoped_scenes(self):
        canon, chapters = fixture()
        new = copy.deepcopy(canon['relationships'][0]); new.update(id='another-phase', phase='secret')
        canon['relationships'].append(new)
        self.assertIssue(validate(canon, chapters), 'overlapping phases')

    def test_no_reverse_edge_inference(self):
        canon, chapters = fixture()
        canon['relationships'].pop(1)
        self.assertIssue(validate(canon, chapters), 'no unique directed relation b->a')

    def test_unknown_speaker(self):
        canon, chapters = fixture()
        chapters[0]['dialogues'][0]['speaker'] = 'unknown'
        self.assertIssue(validate(canon, chapters), 'unknown speaker')

    def test_pronoun_drift(self):
        canon, chapters = fixture()
        chapters[1]['dialogues'][0]['self_pronoun'] = 'tôi'
        self.assertIssue(validate(canon, chapters), 'PRONOUN DRIFT')

    def test_narration_cannot_supply_missing_pronoun(self):
        canon, chapters = fixture()
        chapters[0]['paragraphs'][0] = '“Tôi đang đợi.” An nghĩ đến chị và em.'
        self.assertIssue(validate(canon, chapters), 'lacks evidence inside spoken quote')

    def test_unapproved_phase_change(self):
        canon, chapters = transition_fixture()
        self.assertIssue(validate(canon, chapters), 'unapproved phase change')

    def test_approved_phase_change(self):
        canon, chapters = transition_fixture()
        canon['relationship_transitions'].append({'book_id': 'demo', 'speaker': 'a', 'addressee': 'b', 'from_phase': 'early', 'to_phase': 'allies', 'chapter': 2, 'paragraph': 0, 'scene': 'tower', 'trigger': 'explicit change of address', 'evidence': 'Demo author ch2 p0', 'reviewed_by': 'demo-editor', 'review_id': 'REV-1'})
        self.assertEqual(validate(canon, chapters), [])

    def test_transition_without_review_is_rejected(self):
        canon, chapters = transition_fixture()
        canon['relationship_transitions'].append({'book_id': 'demo', 'speaker': 'a', 'addressee': 'b', 'from_phase': 'early', 'to_phase': 'allies', 'chapter': 2, 'paragraph': 0, 'scene': 'tower', 'trigger': 'change', 'evidence': 'demo', 'reviewed_by': '', 'review_id': ''})
        self.assertIssue(validate(canon, chapters), 'transition needs reviewer')
        self.assertIssue(validate(canon, chapters), 'unapproved phase change')

    def test_transition_not_backdated(self):
        canon, chapters = transition_fixture()
        canon['relationship_transitions'].append({'book_id': 'demo', 'speaker': 'a', 'addressee': 'b', 'from_phase': 'early', 'to_phase': 'allies', 'chapter': 1, 'paragraph': 0, 'scene': 'tower', 'trigger': 'change', 'evidence': 'demo', 'reviewed_by': 'demo-editor', 'review_id': 'REV-2'})
        self.assertIssue(validate(canon, chapters), 'unapproved phase change')

    def test_review_queue_cannot_autolock(self):
        canon, chapters = fixture()
        canon['term_review_queue'].append({'id': 'candidate', 'locked': True})
        self.assertIssue(validate(canon, chapters), 'cannot be auto-promoted')

    def test_world_bible_requires_evidence(self):
        canon, chapters = fixture()
        bible = {'facts': [{'id': 'f1', 'book_id': 'demo', 'status': 'confirmed', 'kind': 'setting', 'statement': 'There is a tower.'}]}
        self.assertIssue(validate(canon, chapters, bible), 'confirmed fact requires')

    def test_knowledge_cannot_leak_into_earlier_chapter(self):
        canon, chapters = fixture()
        bible = {'facts': [{'id': 'secret', 'book_id': 'demo', 'status': 'confirmed', 'kind': 'character_knowledge', 'character_id': 'a', 'known_from_chapter': 2, 'statement': 'An learned a fact.', 'source_reference': 'demo ch2 p0', 'reviewed_by': 'editor'}]}
        chapters[0]['dialogues'][0]['knowledge_refs'] = ['secret']
        self.assertIssue(validate(canon, chapters, bible), 'spoiler/knowledge timeline violation')

    def test_missing_dialogue_annotation(self):
        canon, chapters = fixture()
        chapters[0]['dialogues'].pop(0)
        self.assertIssue(validate(canon, chapters), 'direct speech paragraph 0 missing annotation')


if __name__ == '__main__':
    unittest.main()
