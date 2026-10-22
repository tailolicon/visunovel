import argparse
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import role3_entry

class GuardTests(unittest.TestCase):
    def test_pending_work_rejected(self):
        args = argparse.Namespace(dry_run=False, book_id='the-demon-king-overrun')
        with patch.object(role3_entry, 'original') as call:
            with self.assertRaises(ValueError):
                role3_entry.guarded(args)
            call.assert_not_called()

if __name__ == '__main__':
    unittest.main()
