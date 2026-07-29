#!/usr/bin/env python3
"""
Hermes Evolution Log — 进化日志生成器 CLI

采集 Hermes Agent 的 Skills、Memory、Cron Jobs 数据，
生成可视化 Web 页面与 REST API，支持增量快照对比与 Side-by-Side Visual Diff。

用法:
    # 首次基线快照
    python generate.py --baseline

    # 增量更新
    python generate.py

    # 指定 Hermes 数据目录
    python generate.py --hermes-home /path/to/hermes

    # 指定输出目录
    python generate.py --output-dir ./output

    # 全量重构成构建 (裁剪 3 个月前记录)
    python generate.py --full-rebuild
"""

import argparse
import json
import os
import sys
from pathlib import Path

from i18n import get as i18n_get, t as i18n_t, resolve_lang
from src.core.collector import collect_snapshot
from src.core.diff_engine import (
    append_timeline_entry,
    diff_snapshots,
    latest_snapshot,
    load_timeline,
    save_snapshot,
    save_timeline,
    snapshots_dir,
    trim_timeline,
)
from src.core.exporter import build_meta, export_site


# ─── 路径工具 ────────────────────────────────────────────────────────────────

def get_hermes_home() -> Path:
    """获取 Hermes 数据目录"""
    env = os.environ.get("HERMES_HOME", "")
    if env:
        return Path(env)
    local_appdata = os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))
    return Path(local_appdata) / "hermes"


def get_project_dir() -> Path:
    """获取项目根目录"""
    return Path(__file__).resolve().parent


def detect_project(project_dir: Path | None = None) -> str:
    """自动检测项目名：优先 git remote origin 的 repo 名，否则用目录名"""
    import subprocess as sp
    d = project_dir or get_project_dir()
    try:
        r = sp.run(
            ["git", "remote", "get-url", "origin"],
            cwd=str(d),
            capture_output=True,
            text=True,
            timeout=5
        )
        if r.returncode == 0:
            url = r.stdout.strip()
            name = url.rstrip("/").split("/")[-1].removesuffix(".git")
            if name:
                return name
    except Exception:
        pass
    return d.name


# ─── 主入口 ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Hermes Evolution Log Generator")
    parser.add_argument(
        "--hermes-home",
        default=str(get_hermes_home()),
        help="Hermes data directory path"
    )
    parser.add_argument(
        "--output-dir",
        default=str(get_project_dir() / "output"),
        help="Output directory for generated Web app and API"
    )
    parser.add_argument(
        "--baseline",
        action="store_true",
        help="Create baseline snapshot (no change records)"
    )
    parser.add_argument(
        "--full-rebuild",
        action="store_true",
        help="Full rebuild timeline (trim old records)"
    )
    parser.add_argument(
        "--lang",
        choices=["zh", "en"],
        default=None,
        help="Output language: zh or en"
    )
    parser.add_argument(
        "--project",
        default=None,
        help="Project name for archive grouping (auto-detected if omitted)"
    )
    args = parser.parse_args()

    lang = resolve_lang(args.lang)
    project = args.project or detect_project()

    hermes_home = Path(args.hermes_home)
    output_dir = Path(args.output_dir)
    snap_dir = snapshots_dir(output_dir)

    if not hermes_home.exists():
        print(f"[ERROR] Hermes data dir not found: {hermes_home}", file=sys.stderr)
        print("        Use --hermes-home to specify correct path", file=sys.stderr)
        sys.exit(1)

    print(i18n_t(lang, "console_data_dir", path=hermes_home))
    print(i18n_t(lang, "console_output_dir", path=output_dir))

    # 1. 采集快照
    print(i18n_t(lang, "console_collecting"))
    snapshot = collect_snapshot(hermes_home)
    save_snapshot(snap_dir, snapshot)

    # 2. 加载已有时间线
    timeline = load_timeline(output_dir)

    # 3. 对比快照
    all_snaps = sorted(snap_dir.glob("*.json"))
    prev = None
    if len(all_snaps) >= 2:
        prev_path = all_snaps[-2]
        try:
            prev = json.loads(prev_path.read_text(encoding="utf-8"))
        except Exception:
            prev = None

    diff_result = diff_snapshots(prev, snapshot)

    if args.baseline:
        print(i18n_t(lang, "console_baseline"))
    elif args.full_rebuild:
        print(i18n_t(lang, "console_rebuild"))
        timeline = trim_timeline(timeline)
    else:
        if diff_result.get("is_baseline"):
            print(i18n_t(lang, "console_first_snap"))
        elif not diff_result.get("changes"):
            print(i18n_t(lang, "console_no_changes"))
        else:
            print(i18n_t(lang, "console_changes", n=len(diff_result["changes"])))
            append_timeline_entry(timeline, diff_result, snapshot, lang, project)

    # 4. 保存更新后的时间线
    save_timeline(output_dir, timeline)

    # 5. 打包集成 web 静态资源与 API 数据
    meta = build_meta(snapshot, timeline, lang=lang, project=project)
    export_site(output_dir, timeline, snapshot, meta=meta, lang=lang, project=project)

    # 6. 打印总结
    print(f"\n{'='*50}")
    print(f"   Skills: {len(snapshot['skills'])}")
    print(f"   Memories: {len(snapshot.get('memories', []))}")
    print(f"   Cron Jobs: {len(snapshot.get('cron_jobs', []))}")
    print(f"   Timeline entries: {len(timeline)}")
    print(f"   Output: {output_dir / 'index.html'}")
    print(f"{'='*50}")
    print("✨ Successfully updated evolution dashboard at output/index.html")


if __name__ == "__main__":
    main()
