import os
import unittest

class TestRepositoryDocs(unittest.TestCase):
    def test_repo_docs_exist(self):
        self.assertTrue(os.path.exists("LICENSE"))
        self.assertTrue(os.path.exists("CONTRIBUTING.md"))
        self.assertTrue(os.path.exists("CONTRIBUTING_ZH.md"))

        with open("CONTRIBUTING.md", "r", encoding="utf-8") as f:
            self.assertIn("CONTRIBUTING_ZH.md", f.read())

        with open("CONTRIBUTING_ZH.md", "r", encoding="utf-8") as f:
            self.assertIn("CONTRIBUTING.md", f.read())

if __name__ == "__main__":
    unittest.main()
