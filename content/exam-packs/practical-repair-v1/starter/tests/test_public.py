import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core import repair

class PublicRegressionTests(unittest.TestCase):
    def test_public_cases(self):
        cases = json.loads((Path(__file__).resolve().parents[1] / 'public-cases.json').read_text())
        for case in cases:
            with self.subTest(case=case['name']):
                self.assertEqual(repair(case['args'][0]), case['expected'])

if __name__ == '__main__':
    unittest.main()
