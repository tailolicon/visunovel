import unittest
from tools.independent_qa import inspect

class TestQA(unittest.TestCase):
    def test_no_automatic_approval(self):
        canon = {'works':[{'book_id':'demo','rights_status':'cleared'}]}
        r=inspect('Một đoạn.', 'Một đoạn.', canon, 'demo', 1)
        self.assertEqual(r['qa_status'], 'needs_review')
        self.assertFalse(r['publishable'])
