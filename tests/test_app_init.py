import os
import unittest

class TestAppInit(unittest.TestCase):
    def test_app_init_fallback(self):
        app_js_path = "src/web/assets/js/app.js"
        self.assertTrue(os.path.exists(app_js_path))
        with open(app_js_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("readyState", content)
        self.assertIn("initApp", content)

if __name__ == "__main__":
    unittest.main()
