import os
import unittest

class TestTimelineI18n(unittest.TestCase):
    def test_archive_timeline_i18n(self):
        arc_path = "src/web/assets/js/components/archive.js"
        dash_path = "src/web/assets/js/components/dashboard.js"
        self.assertTrue(os.path.exists(arc_path))
        self.assertTrue(os.path.exists(dash_path))
        with open(arc_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("formatEntryTitle", content)
        self.assertIn("formatChangeType", content)

if __name__ == "__main__":
    unittest.main()
