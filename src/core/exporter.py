"""
Hermes Evolution Log — API & Web Site Exporter
导出 RESTful 标准 JSON 数据结构至 output/api/v1/
并将 src/web/ 静态站点集成打包至 output/，支持 file:// 零跨域运行。
"""

import json
import shutil
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


def export_site(
    output_dir: Path | str,
    timeline: list[dict[str, Any]],
    current_snapshot: dict[str, Any],
    meta: dict[str, Any] | None = None,
    lang: str = "zh",
    project: str = "",
    web_dir: Path | str | None = None
) -> dict[str, Path]:
    """
    完整自动化构建打包打包流程:
      1. 导出 api/v1/ REST API 数据 (meta.json, timeline.json, latest.json)
      2. 复制 src/web/ 静态资源文件至 output_dir
      3. 内嵌 window.__INITIAL_DATA__ 全量快照至 index.html 头部，保证 file:// 零跨域运行
    """
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # 1. 导出 API 数据
    files = export_data(out_path, timeline, current_snapshot, meta=meta, lang=lang, project=project)

    # 2. 复制 src/web 静态资源
    if web_dir is None:
        web_dir = Path(__file__).resolve().parent.parent / "web"

    web_path = Path(web_dir)
    if web_path.is_dir():
        for item in web_path.rglob("*"):
            if item.is_file():
                rel = item.relative_to(web_path)
                dest = out_path / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, dest)

    # 3. 注入 window.__INITIAL_DATA__ 兜底数据
    index_file = out_path / "index.html"
    if index_file.exists():
        html_content = index_file.read_text(encoding="utf-8")

        meta_data = meta or build_meta(current_snapshot, timeline, lang=lang, project=project)
        initial_data = {
            "meta": meta_data,
            "timeline": timeline,
            "latest": current_snapshot
        }

        script_tag = f'<script id="initial-data">window.__INITIAL_DATA__ = {json.dumps(initial_data, ensure_ascii=False)};</script>\n</head>'
        if "</head>" in html_content:
            html_content = html_content.replace("</head>", script_tag, 1)
        else:
            html_content = script_tag + "\n" + html_content

        index_file.write_text(html_content, encoding="utf-8")

    return files
