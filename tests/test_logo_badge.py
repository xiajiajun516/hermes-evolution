import os
import unittest

class TestLogoBadge(unittest.TestCase):
    def test_logo_badge_ui(self):
        html_path = "src/web/index.html"
        css_path = "src/web/assets/css/main.css"
        self.assertTrue(os.path.exists(html_path))
        self.assertTrue(os.path.exists(css_path))
        with open(html_path, "r", encoding="utf-8") as f:
            self.assertIn("brand-logo-badge", f.read())
        with open(css_path, "r", encoding="utf-8") as f:
            self.assertIn(".brand-logo-badge", f.read())

if __name__ == "__main__":
    unittest.main()
