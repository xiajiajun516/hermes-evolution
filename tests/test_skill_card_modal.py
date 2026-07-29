import os
import unittest

class TestSkillCardModal(unittest.TestCase):
    def test_css_rules(self):
        css_path = os.path.join("src", "web", "assets", "css", "main.css")
        self.assertTrue(os.path.exists(css_path))
        with open(css_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn(".grid-container, .memory-list, .timeline", content)
        self.assertIn("min-height: 540px;", content)
        self.assertIn(".skill-card", content)
        self.assertIn("cursor: pointer;", content)
        self.assertIn("height: 220px;", content)
        self.assertIn("-webkit-line-clamp: 2;", content)

        # Modal-specific styles
        self.assertIn(".skill-modal-card", content)
        self.assertIn("max-width: 600px;", content)
        self.assertIn("max-height: 80vh;", content)
        self.assertIn("overflow-y: auto;", content)

        # Tags override in modal context
        self.assertIn(".skill-modal-card .tags-list", content)
        self.assertIn("max-height: none;", content)
        self.assertIn("overflow: visible;", content)

        # Modal section title and divider
        self.assertIn(".modal-section-title", content)
        self.assertIn(".modal-divider", content)

    def test_skills_js(self):
        js_path = os.path.join("src", "web", "assets", "js", "components", "skills.js")
        self.assertTrue(os.path.exists(js_path))
        with open(js_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("skillMap", content)
        self.assertIn("data-skill-id", content)
        self.assertIn("openSkillModal", content)
        self.assertIn("skill-modal-backdrop", content)
        self.assertIn("skill-modal-card", content)

        # Modal section structure
        self.assertIn("skill_modal_description", content)
        self.assertIn("skill_modal_tags", content)
        self.assertIn("skill_modal_details", content)
        self.assertIn("modal-section-title", content)
        self.assertIn("modal-divider", content)

    def test_i18n_keys(self):
        i18n_path = os.path.join("src", "web", "assets", "js", "i18n.js")
        self.assertTrue(os.path.exists(i18n_path))
        with open(i18n_path, "r", encoding="utf-8") as f:
            content = f.read()

        # New i18n keys for modal
        self.assertIn("skill_modal_description", content)
        self.assertIn("skill_modal_tags", content)
        self.assertIn("skill_modal_details", content)

        # Verify Chinese translations
        self.assertIn('"描述"', content)
        self.assertIn('"标签"', content)
        self.assertIn('"详细信息"', content)

        # Verify English translations
        self.assertIn('"Description"', content)
        self.assertIn('"Tags"', content)
        self.assertIn('"Details"', content)

if __name__ == "__main__":
    unittest.main()
