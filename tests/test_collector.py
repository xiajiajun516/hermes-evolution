"""
Tests for src/core/collector.py
"""

import tempfile
import unittest
from pathlib import Path

from src.core.collector import (
    collect_all,
    collect_cron_jobs,
    collect_memory,
    collect_skills,
    collect_snapshot,
    hash_content,
    parse_skill_frontmatter,
)


class TestCollector(unittest.TestCase):

    def test_hash_content(self):
        h1 = hash_content("hello")
        h2 = hash_content("hello")
        h3 = hash_content("world")
        self.assertEqual(len(h1), 16)
        self.assertEqual(h1, h2)
        self.assertNotEqual(h1, h3)

    def test_parse_skill_frontmatter(self):
        content = "---\nname: test-skill\ndescription: A test skill\nversion: 1.0.0\n---\n# Body"
        meta = parse_skill_frontmatter(content)
        self.assertEqual(meta.get("name"), "test-skill")
        self.assertEqual(meta.get("description"), "A test skill")
        self.assertEqual(meta.get("version"), "1.0.0")

        self.assertEqual(parse_skill_frontmatter("No frontmatter"), {})

    def test_collect_skills_mock(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            hermes_home = Path(tmpdir)
            skill_dir = hermes_home / "skills" / "demo_category" / "my_skill"
            skill_dir.mkdir(parents=True)
            skill_file = skill_dir / "SKILL.md"
            skill_file.write_text(
                "---\nname: my_skill\ndescription: Demo skill\nversion: 1.2.0\n---\nContent",
                encoding="utf-8"
            )

            skills = collect_skills(hermes_home)
            self.assertEqual(len(skills), 1)
            self.assertEqual(skills[0]["name"], "my_skill")
            self.assertEqual(skills[0]["category"], str(Path("demo_category") / "my_skill"))
            self.assertEqual(skills[0]["version"], "1.2.0")

    def test_collect_memory_mock(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            hermes_home = Path(tmpdir)
            mem_dir = hermes_home / "memories"
            mem_dir.mkdir(parents=True)
            (mem_dir / "USER.md").write_text("Prefers Python\nLikes dark mode", encoding="utf-8")

            memories = collect_memory(hermes_home)
            self.assertEqual(len(memories), 2)
            self.assertEqual(memories[0]["target"], "user")

    def test_collect_cron_mock(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            hermes_home = Path(tmpdir)
            config_file = hermes_home / "config.yaml"
            config_file.write_text("cron:\n  jobs:\n    daily_sync:\n      name: Daily Sync\n      schedule: '0 0 * * *'\n", encoding="utf-8")

            jobs = collect_cron_jobs(hermes_home)
            self.assertEqual(len(jobs), 1)
            self.assertEqual(jobs[0]["id"], "daily_sync")
            self.assertEqual(jobs[0]["name"], "Daily Sync")

    def test_collect_all(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            hermes_home = Path(tmpdir)
            data = collect_all(hermes_home)
            self.assertIn("skills", data)
            self.assertIn("memories", data)
            self.assertIn("cron_jobs", data)
            self.assertIn("timestamp", data)


def test_collect_all():
    """Pytest style standalone test function"""
    with tempfile.TemporaryDirectory() as tmpdir:
        data = collect_all(Path(tmpdir))
        assert "skills" in data
        assert "memories" in data
        assert "cron_jobs" in data


if __name__ == "__main__":
    unittest.main()
