import os
import unittest

class TestReadmeDocs(unittest.TestCase):
    def test_readme_bilingual_links(self):
        readme_en = "README.md"
        readme_zh = "README_ZH.md"
        self.assertTrue(os.path.exists(readme_en))
        self.assertTrue(os.path.exists(readme_zh))

        with open(readme_en, "r", encoding="utf-8") as f:
            en_content = f.read()
        self.assertIn("README_ZH.md", en_content)

        with open(readme_zh, "r", encoding="utf-8") as f:
            zh_content = f.read()
        self.assertIn("README.md", zh_content)

if __name__ == "__main__":
    unittest.main()
