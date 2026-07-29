"""
Hermes Evolution Log — API Data Exporter

导出 RESTful 标准 JSON 数据结构至 output/api/v1/
包括 meta.json, timeline.json, latest.json
"""

import json
from pathlib import Path
from typing import Any

from src.core.diff_engine import compute_evolution_stats


def build_meta(
    current_snapshot: dict[str, Any],
    timeline: list[dict[str, Any]],
    lang: str = "zh",
    project: str = ""
) -> dict[str, Any]:
    """
    构建元数据 (meta.json)
    """
    skills = current_snapshot.get("skills", [])
    memories = current_snapshot.get("memories", [])
    cron_jobs = current_snapshot.get("cron_jobs", [])

    evolution = compute_evolution_stats(timeline)
    projects = sorted(
        set(entry.get("project", "") for entry in timeline if entry.get("project"))
    )

    total_changes = sum(len(entry.get("changes", [])) for entry in timeline)

    return {
        "generated_at": current_snapshot.get("timestamp", ""),
        "lang": lang,
        "project": project,
        "stats": {
            "skills": len(skills),
            "memories": len(memories),
            "cron_jobs": len(cron_jobs),
            "total_changes": total_changes,
        },
        "evolution": evolution,
        "projects": projects,
    }


def export_data(
    output_dir: Path | str,
    timeline: list[dict[str, Any]],
    current_snapshot: dict[str, Any],
    meta: dict[str, Any] | None = None,
    lang: str = "zh",
    project: str = ""
) -> dict[str, Path]:
    """
    导出 REST API 数据文件结构:
      - output/api/v1/meta.json
      - output/api/v1/timeline.json
      - output/api/v1/latest.json
    """
    out_path = Path(output_dir)
    api_dir = out_path / "api" / "v1"
    api_dir.mkdir(parents=True, exist_ok=True)

    if meta is None:
        meta = build_meta(current_snapshot, timeline, lang=lang, project=project)

    meta_file = api_dir / "meta.json"
    timeline_file = api_dir / "timeline.json"
    latest_file = api_dir / "latest.json"

    meta_file.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    timeline_file.write_text(json.dumps(timeline, ensure_ascii=False, indent=2), encoding="utf-8")
    latest_file.write_text(json.dumps(current_snapshot, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "meta": meta_file,
        "timeline": timeline_file,
        "latest": latest_file,
    }
