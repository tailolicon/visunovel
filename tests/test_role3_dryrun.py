import argparse
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import role3_entry

class DryRunGuard(unittest.TestCase):
    def test_dry_run_delegates_without_network(self):
        args = argparse.Namespace(dry_run=True, book_id='the-demon-king-overrun')
        with patch.object(role3_entry, 'original') as call:
            role3_entry.guarded(args)
            call.assert_called_once_with(args)

if __name__ == '__main__':
    unittest.main()
