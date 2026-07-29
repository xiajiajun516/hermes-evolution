import os
import unittest

class TestFavicon(unittest.TestCase):
    def test_favicon_present(self):
        index_path = "src/web/index.html"
        self.assertTrue(os.path.exists(index_path))
        with open(index_path, "r", encoding="utf-8") as f:
            html = f.read()
        self.assertIn('rel="icon"', html)
        self.assertIn("data:image/svg+xml;base64", html)

if __name__ == "__main__":
    unittest.main()
