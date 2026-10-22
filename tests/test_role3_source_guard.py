import argparse
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import role3_entry

class LocalSourceGuard(unittest.TestCase):
    def test_demo_fixture_cannot_be_translated_inside_git(self):
        args = argparse.Namespace(dry_run=False, book_id='nhung-la-thu-binh-minh', input=Path(__file__).parent / 'example-source.txt', output=None, chapter=137)
        with patch.object(role3_entry, 'original') as call:
            with self.assertRaises(ValueError):
                role3_entry.guarded(args)
            call.assert_not_called()

if __name__ == '__main__':
    unittest.main()
