import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import role3_qa
import role3_rights

class OfflineQA(unittest.TestCase):
    def test_paragraph_alignment(self):
        self.assertIn('PARAGRAPH_COUNT', role3_qa.inspect('A.\n\nB.', 'A.'))
    def test_pronoun_marker(self):
        self.assertIn('PRONOUN_UNRESOLVED', role3_qa.inspect('A.', '[CẦN_XƯNG_HÔ]'))
    def test_pending_rights(self):
        c = {'works': [{'book_id':'demo','rights_status':'pending','allowed_to_translate':False}]}
        self.assertFalse(role3_rights.permitted(c,'demo'))
        c['works'][0].update(rights_status='cleared', allowed_to_translate=True)
        self.assertTrue(role3_rights.permitted(c,'demo'))

if __name__ == '__main__':
    unittest.main()
