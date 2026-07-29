"""
Tests for src/core/diff_engine.py
"""

import tempfile
import unittest
from pathlib import Path

from src.core.diff_engine import (
    append_timeline_entry,
    compare_snapshots,
    compute_evolution_stats,
    diff_snapshots,
    latest_snapshot,
    load_timeline,
    save_snapshot,
    save_timeline,
    snapshots_dir,
    summarize_snapshot,
    trim_timeline,
)


class TestDiffEngine(unittest.TestCase):

    def test_diff_snapshots_baseline(self):
        new_snap = {
            "timestamp": "2026-07-29T10:00:00",
            "skills": [{"name": "s1", "content_hash": "h1"}],
            "memories": [],
            "cron_jobs": []
        }
        res = diff_snapshots(None, new_snap)
        self.assertTrue(res["is_baseline"])
        self.assertEqual(res["changes"], [])

    def test_diff_snapshots_changes(self):
        old_snap = {
            "timestamp": "2026-07-28T10:00:00",
            "skills": [{"name": "s1", "content_hash": "h1"}],
            "memories": [{"content_hash": "m1", "target": "user", "content": "c1"}],
            "cron_jobs": []
        }
        new_snap = {
            "timestamp": "2026-07-29T10:00:00",
            "skills": [
                {"name": "s1", "content_hash": "h1_updated", "version": "1.1.0"},
                {"name": "s2", "content_hash": "h2", "description": "Skill 2"}
            ],
            "memories": [{"content_hash": "m1", "target": "user", "content": "c1"}],
            "cron_jobs": []
        }
        res = compare_snapshots(old_snap, new_snap)
        self.assertFalse(res["is_baseline"])
        changes = res["changes"]
        self.assertEqual(len(changes), 2)  # s1 updated, s2 added
        types = [c["type"] for c in changes]
        self.assertIn("skill_updated", types)
        self.assertIn("skill_added", types)

    def test_summarize_snapshot(self):
        snap = {
            "timestamp": "2026-07-29T10:00:00",
            "skills": [1, 2],
            "memories": [1],
            "cron_jobs": []
        }
        summary = summarize_snapshot(snap)
        self.assertEqual(summary["skills_count"], 2)
        self.assertEqual(summary["memories_count"], 1)
        self.assertEqual(summary["cron_jobs_count"], 0)

    def test_snapshot_storage(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir)
            s_dir = snapshots_dir(out_dir)
            snap = {"timestamp": "2026-07-29T10:00:00", "skills": []}
            save_snapshot(s_dir, snap)

            loaded = latest_snapshot(s_dir)
            self.assertIsNotNone(loaded)
            self.assertEqual(loaded["timestamp"], "2026-07-29T10:00:00")

    def test_timeline(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir)
            timeline = load_timeline(out_dir)
            self.assertEqual(timeline, [])

            timeline.append({"date": "2026-07-29", "title": "Test"})
            save_timeline(out_dir, timeline)

            loaded = load_timeline(out_dir)
            self.assertEqual(len(loaded), 1)
            self.assertEqual(loaded[0]["title"], "Test")


if __name__ == "__main__":
    unittest.main()
