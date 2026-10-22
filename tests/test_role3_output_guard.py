import argparse
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import role3_entry

class PrivateOutputGuard(unittest.TestCase):
    def test_output_outside_private_home_rejected(self):
        with TemporaryDirectory() as folder:
            src = Path(folder) / 'original.txt'
            src.write_text('Authored demo only.', encoding='utf-8')
            args = argparse.Namespace(dry_run=False, book_id='nhung-la-thu-binh-minh', input=src, output=Path(folder) / 'public.txt', chapter=137)
            with patch.object(role3_entry, 'original') as call:
                with self.assertRaises(ValueError):
                    role3_entry.guarded(args)
                call.assert_not_called()

if __name__ == '__main__':
    unittest.main()
