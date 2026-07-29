"""
Tests for src/core/exporter.py
"""

import json
import tempfile
import unittest
from pathlib import Path

from src.core.exporter import build_meta, export_data, export_site


class TestExporter(unittest.TestCase):
    def setUp(self):
        self.snapshot = {
            "timestamp": "2026-07-29T12:00:00",
            "skills": [
                {"name": "skill-1", "category": "dev", "version": "1.0.0"}
            ],
            "memories": [
                {"target": "user", "content": "Likes Python"}
            ],
            "cron_jobs": [
                {"id": "cron-1", "name": "Daily Backup"}
            ]
        }
        self.timeline = [
            {
                "date": "2026-07-29",
                "time": "12:00",
                "title": "Initial Baseline",
                "project": "hermes-evolution",
                "changes": [
                    {"type": "skill_added", "name": "skill-1"}
                ]
            }
        ]

    def test_build_meta(self):
        meta = build_meta(self.snapshot, self.timeline, lang="zh", project="hermes-evolution")
        self.assertEqual(meta["generated_at"], "2026-07-29T12:00:00")
        self.assertEqual(meta["lang"], "zh")
        self.assertEqual(meta["project"], "hermes-evolution")
        self.assertEqual(meta["stats"]["skills"], 1)
        self.assertEqual(meta["stats"]["memories"], 1)
        self.assertEqual(meta["stats"]["cron_jobs"], 1)
        self.assertEqual(meta["stats"]["total_changes"], 1)
        self.assertIn("hermes-evolution", meta["projects"])

    def test_export_data(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir)
            files = export_data(out_dir, self.timeline, self.snapshot, lang="en", project="test-project")

            meta_file = out_dir / "api" / "v1" / "meta.json"
            timeline_file = out_dir / "api" / "v1" / "timeline.json"
            latest_file = out_dir / "api" / "v1" / "latest.json"

            self.assertTrue(meta_file.exists())
            self.assertTrue(timeline_file.exists())
            self.assertTrue(latest_file.exists())

            self.assertEqual(files["meta"], meta_file)
            self.assertEqual(files["timeline"], timeline_file)
            self.assertEqual(files["latest"], latest_file)

            meta_content = json.loads(meta_file.read_text(encoding="utf-8"))
            timeline_content = json.loads(timeline_file.read_text(encoding="utf-8"))
            latest_content = json.loads(latest_file.read_text(encoding="utf-8"))

            self.assertEqual(meta_content["lang"], "en")
            self.assertEqual(meta_content["project"], "test-project")
            self.assertEqual(len(timeline_content), 1)
            self.assertEqual(latest_content["timestamp"], "2026-07-29T12:00:00")

    def test_export_site(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir)
            files = export_site(out_dir, self.timeline, self.snapshot, lang="zh", project="test-site")

            index_file = out_dir / "index.html"
            self.assertTrue(index_file.exists())
            content = index_file.read_text(encoding="utf-8")
            self.assertIn("window.__INITIAL_DATA__ =", content)
            self.assertIn("test-site", content)


if __name__ == "__main__":
    unittest.main()
