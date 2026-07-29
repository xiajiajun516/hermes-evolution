import os
import unittest
from pathlib import Path

class TestUpdateScript(unittest.TestCase):
    def test_update_sh_exists(self):
        script_path = Path(__file__).parent.parent / "update.sh"
        self.assertTrue(script_path.exists(), "update.sh should exist in repo root")
        
        content = script_path.read_text(encoding="utf-8")
        self.assertIn("#!/usr/bin/env bash", content)
        self.assertIn("generate.py", content)
        self.assertIn("Update complete", content)

if __name__ == "__main__":
    unittest.main()
