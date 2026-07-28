#!/usr/bin/env python3
"""
Hermes Evolution Log — 进化日志生成器

采集 Hermes Agent 的 Skills、Memory、Cron Jobs 数据，
生成可视化 HTML 页面，支持增量快照对比和变更追踪。

用法:
    # 首次基线快照（不产生变更记录）
    python generate.py --baseline

    # 每日增量更新
    python generate.py

    # 指定 Hermes 数据目录
    python generate.py --hermes-home /path/to/hermes

    # 指定输出目录
    python generate.py --output-dir ./public

    # 全量重写（压缩 3 个月前记录）
    python generate.py --full-rebuild
"""

import argparse
import json
import os
import re
import sqlite3
import sys
import time
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from i18n import get as i18n_get, t as i18n_t, resolve_lang, TRANSLATIONS


# ─── 路径工具 ────────────────────────────────────────────────────────────────

def get_hermes_home() -> Path:
    """获取 Hermes 数据目录"""
    env = os.environ.get("HERMES_HOME", "")
    if env:
        return Path(env)
    # Windows: ~/AppData/Local/hermes
    local_appdata = os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))
    return Path(local_appdata) / "hermes"


def get_project_dir() -> Path:
    """获取项目根目录（脚本所在目录的父目录）"""
    return Path(__file__).resolve().parent


# ─── 数据采集 ────────────────────────────────────────────────────────────────

def collect_skills(hermes_home: Path) -> list[dict]:
    """扫描 skills 目录，解析每个 SKILL.md"""
    skills_dir = hermes_home / "skills"
    if not skills_dir.is_dir():
        return []

    skills = []
    for skill_md in skills_dir.rglob("SKILL.md"):
        rel = skill_md.relative_to(skills_dir)
        category = str(rel.parent) if rel.parent != Path(".") else ""

        content = skill_md.read_text(encoding="utf-8", errors="replace")
        meta = parse_skill_frontmatter(content)

        skills.append({
            "name": meta.get("name", skill_md.parent.name),
            "category": category,
            "description": meta.get("description", ""),
            "version": meta.get("version", "1.0.0"),
            "tags": meta.get("metadata", {}).get("hermes", {}).get("tags", []),
            "path": str(rel),
            "content_hash": hash_content(content),
            "mtime": skill_md.stat().st_mtime if skill_md.exists() else 0,
        })

    skills.sort(key=lambda s: s["name"])
    return skills


def parse_skill_frontmatter(content: str) -> dict:
    """解析 YAML frontmatter"""
    m = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not m:
        return {}
    try:
        return yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        return {}


def collect_memory(hermes_home: Path) -> list[dict]:
    """从 memories 目录和 state.db 读取 memory 条目"""
    memories = []
    mem_dir = hermes_home / "memories"

    # 方式1: *.md 纯文本文件（文件名为 target，每行一条）
    if mem_dir.is_dir():
        for mf in sorted(mem_dir.rglob("*.md")):
            try:
                target = mf.stem.lower()  # MEMORY.md → memory, USER.md → user
                text = mf.read_text(encoding="utf-8").strip()
                for line in text.splitlines():
                    line = line.strip()
                    if line:
                        memories.append({
                            "target": target,
                            "content": line[:200] + ("..." if len(line) > 200 else ""),
                            "created_at": "",
                            "updated_at": "",
                            "content_hash": hash_content(line),
                        })
            except Exception:
                pass

    # 方式2: JSON 文件
    if mem_dir.is_dir():
        for mf in sorted(mem_dir.rglob("*.json")):
            try:
                data = json.loads(mf.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    for entry in data:
                        content = str(entry.get("content", entry))
                        memories.append({
                            "target": entry.get("target", "memory"),
                            "content": content[:200] + ("..." if len(content) > 200 else ""),
                            "created_at": entry.get("created_at", ""),
                            "updated_at": entry.get("updated_at", ""),
                            "content_hash": hash_content(content),
                        })
                elif isinstance(data, dict):
                    content = str(data.get("content", json.dumps(data)))
                    memories.append({
                        "target": data.get("target", "memory"),
                        "content": content[:200] + ("..." if len(content) > 200 else ""),
                        "created_at": data.get("created_at", ""),
                        "updated_at": data.get("updated_at", ""),
                        "content_hash": hash_content(content),
                    })
            except Exception:
                continue

    # 方式3: state.db
    db_path = hermes_home / "state.db"
    if db_path.exists():
        try:
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
            if "memory" in tables:
                cur = conn.execute(
                    "SELECT target, content, created_at, updated_at FROM memory ORDER BY target, created_at"
                )
                for r in cur.fetchall():
                    memories.append({
                        "target": r["target"],
                        "content": r["content"][:200] + ("..." if len(r["content"]) > 200 else ""),
                        "created_at": r["created_at"],
                        "updated_at": r["updated_at"],
                        "content_hash": hash_content(r["content"]),
                    })
            conn.close()
        except Exception as e:
            print(f"[WARN] state.db memory 读取失败: {e}", file=sys.stderr)

    return memories


def collect_cron_jobs(hermes_home: Path) -> list[dict]:
    """从 config 或 cron 目录读取 cron jobs"""
    config_path = hermes_home / "config.yaml"
    jobs = []

    # 尝试从 config.yaml 读取
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}
            cron_config = config.get("cron", {}) if isinstance(config, dict) else {}
            for job_id, job in cron_config.get("jobs", {}).items():
                jobs.append({
                    "id": job_id,
                    "name": job.get("name", job_id),
                    "schedule": job.get("schedule", ""),
                    "prompt": str(job.get("prompt", ""))[:100],
                    "enabled": job.get("enabled", True),
                })
        except Exception:
            pass

    # 也扫描 cron/ 目录下的 job 定义文件
    cron_dir = hermes_home / "cron"
    if cron_dir.is_dir():
        for jf in cron_dir.rglob("*.yaml"):
            try:
                data = yaml.safe_load(jf.read_text(encoding="utf-8")) or {}
                jobs.append({
                    "id": jf.stem,
                    "name": data.get("name", jf.stem),
                    "schedule": data.get("schedule", ""),
                    "prompt": str(data.get("prompt", ""))[:100],
                })
            except Exception:
                pass

    return jobs


def collect_snapshot(hermes_home: Path) -> dict:
    """采集当前快照"""
    return {
        "timestamp": datetime.now().isoformat(),
        "hermes_home": str(hermes_home),
        "skills": collect_skills(hermes_home),
        "memories": collect_memory(hermes_home),
        "cron_jobs": collect_cron_jobs(hermes_home),
    }


# ─── 快照管理 ────────────────────────────────────────────────────────────────

def snapshots_dir(output_dir: Path) -> Path:
    d = output_dir / "snapshots"
    d.mkdir(parents=True, exist_ok=True)
    return d


def latest_snapshot(snap_dir: Path) -> dict | None:
    """获取最近一次快照"""
    files = sorted(snap_dir.glob("*.json"), reverse=True)
    for f in files:
        try:
            return json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
    return None


def save_snapshot(snap_dir: Path, data: dict):
    """保存快照（使用时间戳避免同一天多次运行覆盖）"""
    ts = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    path = snap_dir / f"{ts}.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# ─── Diff 引擎 ───────────────────────────────────────────────────────────────

def diff_snapshots(old: dict | None, new: dict) -> dict:
    """对比两个快照，返回变更摘要"""
    if old is None:
        return {"is_baseline": True, "changes": []}

    changes = []

    # Skills 变更
    old_skills = {s["name"]: s for s in old.get("skills", [])}
    new_skills = {s["name"]: s for s in new.get("skills", [])}

    for name, skill in new_skills.items():
        if name not in old_skills:
            changes.append({"type": "skill_added", "name": name, "detail": skill})
        elif skill["content_hash"] != old_skills[name]["content_hash"]:
            changes.append({
                "type": "skill_updated",
                "name": name,
                "detail": skill,
                "old": {"version": old_skills[name].get("version", "")}
            })
    for name in old_skills:
        if name not in new_skills:
            changes.append({"type": "skill_removed", "name": name, "detail": old_skills[name]})

    # Memory 变更
    old_memories = {m["content_hash"]: m for m in old.get("memories", [])}
    new_memories = {m["content_hash"]: m for m in new.get("memories", [])}

    added = set(new_memories) - set(old_memories)
    removed = set(old_memories) - set(new_memories)
    for h in added:
        changes.append({"type": "memory_added", "name": f"memory:{new_memories[h]['target']}", "detail": new_memories[h]})
    for h in removed:
        changes.append({"type": "memory_removed", "name": f"memory:{old_memories[h]['target']}", "detail": old_memories[h]})

    # Cron jobs 变更
    old_cron = {j["id"]: j for j in old.get("cron_jobs", [])}
    new_cron = {j["id"]: j for j in new.get("cron_jobs", [])}

    for jid, job in new_cron.items():
        if jid not in old_cron:
            changes.append({"type": "cron_added", "name": job.get("name", jid), "detail": job})
    for jid in old_cron:
        if jid not in new_cron:
            changes.append({"type": "cron_removed", "name": old_cron[jid].get("name", jid), "detail": old_cron[jid]})

    # 检查快照间隔
    old_time = datetime.fromisoformat(old["timestamp"]) if old.get("timestamp") else None
    new_time = datetime.fromisoformat(new["timestamp"])
    days_gap = (new_time - old_time).days if old_time else 0

    return {
        "is_baseline": False,
        "changes": changes,
        "old_snapshot_date": old.get("timestamp", ""),
        "days_since_last": days_gap,
        "has_gap": days_gap > 1,
    }


# ─── HTML 模板（基于进化档案设计指南） ──────────────────────────────────────

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="{{ 'zh-CN' if lang == 'zh' else 'en' }}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Noto Sans SC', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #0a0a0f 0%, #1a1a2e 50%, #16213e 100%);
            min-height: 100vh; color: #e0e0e0; line-height: 1.6;
        }

        /* 头部 */
        .header { text-align: center; padding: 60px 20px 40px; }
        .avatar {
            width: 120px; height: 120px; border-radius: 50%; margin: 0 auto 24px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: 3px solid rgba(102,126,234,0.5);
            box-shadow: 0 0 60px rgba(102,126,234,0.4);
            animation: pulse 3s ease-in-out infinite;
            display: flex; align-items: center; justify-content: center;
            font-size: 48px;
        }
        @keyframes pulse {
            0%,100% { box-shadow: 0 0 60px rgba(102,126,234,0.4); }
            50% { box-shadow: 0 0 80px rgba(102,126,234,0.6); }
        }
        .header h1 {
            font-size: 2.5rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .header .subtitle { color: #888; font-size: 1rem; margin-top: 8px; }
        .header .update { color: #666; font-size: 0.8rem; margin-top: 4px; }

        /* 统计 */
        .stats-grid {
            display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px;
            max-width: 900px; margin: 0 auto 50px; padding: 0 20px;
        }
        .stat-card {
            background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08);
            border-radius: 16px; padding: 24px; text-align: center;
            backdrop-filter: blur(10px); transition: all 0.3s ease;
        }
        .stat-card:hover {
            transform: translateY(-4px); border-color: rgba(102,126,234,0.5);
        }
        .stat-number {
            font-size: 2.5rem; font-weight: 700;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .stat-label { font-size: 0.85rem; color: #888; margin-top: 4px; }

        /* 区块 */
        .section { max-width: 1000px; margin: 0 auto 60px; padding: 0 20px; }
        .section-title {
            display: flex; align-items: center; gap: 12px;
            font-size: 1.5rem; font-weight: 600; margin-bottom: 24px;
            padding-bottom: 12px; border-bottom: 1px solid rgba(255,255,255,0.1);
        }

        /* 进化概览 */
        .evolution-card {
            background: linear-gradient(135deg, rgba(102,126,234,0.1), rgba(118,75,162,0.1));
            border: 1px solid rgba(102,126,234,0.2); border-radius: 16px;
            padding: 32px; display: grid; grid-template-columns: repeat(3, 1fr);
            gap: 20px; text-align: center;
        }
        .evo-item .evo-icon { font-size: 2rem; margin-bottom: 8px; }
        .evo-item .evo-number {
            font-size: 1.8rem; font-weight: 700;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .evo-item .evo-label { color: #888; font-size: 0.85rem; }

        /* 技能卡片 */
        .skills-grid {
            display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 20px;
        }
        .skill-card {
            background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08);
            border-radius: 16px; padding: 24px; transition: all 0.3s ease;
            position: relative; overflow: hidden;
        }
        .skill-card::before {
            content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
            background: linear-gradient(90deg, #667eea, #764ba2);
            transform: scaleX(0); transform-origin: left;
            transition: transform 0.3s ease;
        }
        .skill-card:hover::before { transform: scaleX(1); }
        .skill-card:hover {
            transform: translateY(-4px);
            border-color: rgba(102,126,234,0.3);
            box-shadow: 0 20px 40px rgba(0,0,0,0.3);
        }
        .skill-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
        .skill-name { font-size: 1.1rem; font-weight: 600; color: #fff; }
        .skill-category {
            font-size: 0.7rem; padding: 4px 8px;
            background: rgba(102,126,234,0.2); border-radius: 20px; color: #a5b4fc;
        }
        .skill-description { font-size: 0.9rem; color: #999; margin-bottom: 16px; }
        .skill-tags { display: flex; flex-wrap: wrap; gap: 6px; }
        .skill-tag {
            font-size: 0.75rem; padding: 4px 10px;
            background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1);
            border-radius: 20px; color: #888;
        }

        /* 记忆卡片 */
        .memories-grid {
            display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 16px;
        }
        .memory-card {
            background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08);
            border-radius: 16px; padding: 24px; transition: all 0.3s ease;
        }
        .memory-card:hover { transform: translateY(-2px); border-color: rgba(255,255,255,0.15); }
        .memory-type {
            display: inline-block; font-size: 0.75rem;
            padding: 4px 12px; border-radius: 20px; margin-bottom: 12px;
        }
        .memory-type.user { background: rgba(236,72,153,0.2); color: #f472b6; }
        .memory-type.memory { background: rgba(16,185,129,0.2); color: #34d399; }
        .memory-content { font-size: 0.9rem; color: #bbb; }

        /* 时间线 */
        .timeline { position: relative; padding-left: 30px; }
        .timeline::before {
            content: ''; position: absolute; left: 8px; top: 0; bottom: 0; width: 2px;
            background: linear-gradient(to bottom, #667eea, #764ba2, transparent);
        }
        .timeline-item { position: relative; padding-bottom: 40px; }
        .timeline-item::before {
            content: ''; position: absolute; left: -26px; top: 4px;
            width: 12px; height: 12px; border-radius: 50%;
            background: linear-gradient(135deg, #667eea, #764ba2);
            box-shadow: 0 0 20px rgba(102,126,234,0.5);
        }
        .timeline-item.future::before {
            background: rgba(255,255,255,0.2); box-shadow: none;
        }
        .timeline-item.gap::before {
            background: linear-gradient(135deg, #f59e0b, #ef4444);
            box-shadow: 0 0 20px rgba(245,158,11,0.5);
        }
        .timeline-date { font-size: 0.8rem; color: #666; margin-bottom: 8px; }
        .timeline-content {
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 12px; padding: 20px;
        }
        .timeline-title { font-size: 1.1rem; font-weight: 600; color: #fff; margin-bottom: 8px; }
        .timeline-title .badge {
            display: inline-block; font-size: 0.7rem; font-weight: 500;
            padding: 2px 8px; border-radius: 10px; margin-left: 8px;
            vertical-align: middle;
        }
        .badge.skill { background: rgba(102,126,234,0.2); color: #a5b4fc; }
        .badge.memory { background: rgba(16,185,129,0.2); color: #34d399; }
        .badge.cron { background: rgba(245,158,11,0.2); color: #fbbf24; }
        .badge.system { background: rgba(236,72,153,0.2); color: #f472b6; }
        .timeline-desc { font-size: 0.9rem; color: #999; }
        .timeline-details {
            margin-top: 12px; padding-top: 12px;
            border-top: 1px solid rgba(255,255,255,0.05);
            font-size: 0.85rem; color: #777;
        }
        .timeline-details summary {
            cursor: pointer; color: #888; user-select: none;
            padding: 4px 0;
        }
        .timeline-details summary:hover { color: #a5b4fc; }
        .gap-warning {
            display: inline-block; background: rgba(245,158,11,0.15);
            color: #fbbf24; font-size: 0.75rem; padding: 2px 8px;
            border-radius: 8px; margin-left: 8px;
        }

        /* 页脚 */
        .footer {
            text-align: center; padding: 40px 20px;
            color: #666; font-size: 0.85rem;
        }
        .footer a { color: #667eea; text-decoration: none; }

        /* 语言切换 */
        .lang-switcher {
            position: absolute; top: 20px; right: 24px;
            display: flex; gap: 4px; z-index: 10;
        }
        .lang-btn {
            background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.12);
            color: #888; font-size: 0.8rem; padding: 6px 14px;
            border-radius: 20px; cursor: pointer; transition: all 0.3s ease;
            font-family: inherit;
        }
        .lang-btn:hover { border-color: rgba(102,126,234,0.4); color: #ccc; }
        .lang-btn.active {
            background: rgba(102,126,234,0.2); border-color: rgba(102,126,234,0.5);
            color: #a5b4fc;
        }
        @media (max-width: 480px) {
            .lang-switcher { top: 12px; right: 12px; }
            .lang-btn { padding: 4px 10px; font-size: 0.75rem; }
        }

        /* 响应式 */
        @media (max-width: 768px) {
            .stats-grid { grid-template-columns: repeat(2, 1fr); }
            .evolution-card { grid-template-columns: 1fr; }
            .header h1 { font-size: 1.8rem; }
        }
        @media (max-width: 480px) {
            .stats-grid { grid-template-columns: 1fr; }
            .skills-grid { grid-template-columns: 1fr; }
            .memories-grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="lang-switcher">
        <button class="lang-btn active" data-lang="zh" onclick="switchLang('zh')" data-i18n-attr="textContent:lang_zh">中</button>
        <button class="lang-btn" data-lang="en" onclick="switchLang('en')" data-i18n-attr="textContent:lang_en">EN</button>
    </div>
    <div class="header">
        <div class="avatar">🧬</div>
        <h1>{{ title }}</h1>
        <p class="subtitle" data-i18n="page_subtitle">{{ i18n.page_subtitle }}</p>
        <p class="update"><span data-i18n="page_updated">{{ i18n.page_updated }}</span>：{{ last_updated }}</p>
    </div>

    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-number">{{ stats.skills }}</div>
            <div class="stat-label" data-i18n="stat_skills">{{ i18n.stat_skills }}</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{{ stats.memories }}</div>
            <div class="stat-label" data-i18n="stat_memories">{{ i18n.stat_memories }}</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{{ stats.cron_jobs }}</div>
            <div class="stat-label" data-i18n="stat_cron">{{ i18n.stat_cron }}</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{{ stats.total_changes }}</div>
            <div class="stat-label" data-i18n="stat_changes">{{ i18n.stat_changes }}</div>
        </div>
    </div>

    <div class="section">
        <h2 class="section-title" data-i18n="section_overview"><span>📈</span> {{ i18n.section_overview }}</h2>
        <div class="evolution-card">
            <div class="evo-item">
                <div class="evo-icon">🆕</div>
                <div class="evo-number">{{ evolution.skills_added }}</div>
                <div class="evo-label" data-i18n="evo_skills_added">{{ i18n.evo_skills_added }}</div>
            </div>
            <div class="evo-item">
                <div class="evo-icon">🔄</div>
                <div class="evo-number">{{ evolution.skills_updated }}</div>
                <div class="evo-label" data-i18n="evo_skills_updated">{{ i18n.evo_skills_updated }}</div>
            </div>
            <div class="evo-item">
                <div class="evo-icon">🧠</div>
                <div class="evo-number">{{ evolution.memories_changed }}</div>
                <div class="evo-label" data-i18n="evo_memories_changed">{{ i18n.evo_memories_changed }}</div>
            </div>
        </div>
    </div>

    <div class="section">
        <h2 class="section-title" data-i18n="section_skills"><span>🛠️</span> {{ i18n.section_skills }}</h2>
        <div class="skills-grid">
            {% for skill in skills %}
            <div class="skill-card">
                <div class="skill-header">
                    <span class="skill-name">{{ skill.name }}</span>
                    {% if skill.category %}
                    <span class="skill-category">{{ skill.category }}</span>
                    {% endif %}
                </div>
                <p class="skill-description">{{ skill.description or i18n.skill_no_desc }}</p>
                <div class="skill-tags">
                    {% for tag in (skill.tags or [])[:5] %}
                    <span class="skill-tag">{{ tag }}</span>
                    {% endfor %}
                    {% if skill.version %}
                    <span class="skill-tag">v{{ skill.version }}</span>
                    {% endif %}
                </div>
            </div>
            {% endfor %}
        </div>
    </div>

    <div class="section">
        <h2 class="section-title" data-i18n="section_memories"><span>🧠</span> {{ i18n.section_memories }}</h2>
        <div class="memories-grid">
            {% for mem in memories %}
            <div class="memory-card">
                <span class="memory-type {{ mem.target }}" data-i18n="{{ 'memory_type_user' if mem.target == 'user' else 'memory_type_memory' }}">{{ i18n.memory_type_user if mem.target == "user" else i18n.memory_type_memory }}</span>
                <p class="memory-content">{{ mem.content }}</p>
            </div>
            {% endfor %}
        </div>
    </div>

    <div class="section">
        <h2 class="section-title" data-i18n="section_timeline"><span>📅</span> {{ i18n.section_timeline }}</h2>
        <div class="timeline">
            {% for entry in timeline %}
            <div class="timeline-item{% if entry.future %} future{% endif %}{% if entry.has_gap %} gap{% endif %}">
                <div class="timeline-date">{{ entry.date }}</div>
                <div class="timeline-content">
                    <div class="timeline-title">
                        {{ entry.title }}
                        {% if entry.has_gap %}
                        <span class="gap-warning" data-i18n="timeline_gap_warning">{{ i18n.timeline_gap_warning }}</span>
                        {% endif %}
                    </div>
                    <p class="timeline-desc">{{ entry.summary }}</p>
                    {% if entry.changes %}
                    <details class="timeline-details">
                        <summary><span data-i18n="timeline_expand">{{ i18n.timeline_expand }}</span> ({{ entry.changes|length }} <span data-i18n="change_count_label">{{ i18n.change_count_label }}</span>)</summary>
                        <ul>
                        {% for c in entry.changes %}
                            <li>
                                <span class="badge {{ c.type.split('_')[0] }}">{{ c.type }}</span>
                                <strong>{{ c.name }}</strong>
                                {{ c.desc }}
                            </li>
                        {% endfor %}
                        </ul>
                    </details>
                    {% endif %}
                </div>
            </div>
            {% endfor %}
        </div>
    </div>

    <div class="footer">
        <p>Powered by <a href="https://github.com/NousResearch/hermes-agent" target="_blank">Hermes Agent</a> · <span data-i18n="footer_powered">{{ i18n.footer_powered }}</span> {{ last_updated }}</p>
    </div>

    <script>
    // ── Client-side i18n engine ──
    const I18N = {{ i18n_all }};

    function getLang() {
        let lang = localStorage.getItem('evolution-lang');
        if (lang && I18N[lang]) return lang;
        return '{{ lang }}';
    }

    function switchLang(lang) {
        localStorage.setItem('evolution-lang', lang);
        document.documentElement.lang = lang === 'zh' ? 'zh-CN' : 'en';
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.dataset.i18n;
            if (I18N[lang] && I18N[lang][key]) {
                const hasKids = el.children.length > 0 && el.querySelector('[data-i18n]');
                if (!hasKids) el.textContent = I18N[lang][key];
            }
        });
        document.querySelectorAll('[data-i18n-attr]').forEach(el => {
            const parts = el.dataset.i18nAttr.split(':');
            const attr = parts[0], key = parts[1];
            if (I18N[lang] && I18N[lang][key]) el[attr] = I18N[lang][key];
        });
        document.querySelectorAll('.lang-btn').forEach(b => {
            b.classList.toggle('active', b.dataset.lang === lang);
        });
        document.title = I18N[lang].page_title || document.title;
    }

    // Init on load
    const savedLang = getLang();
    if (savedLang !== '{{ lang }}') switchLang(savedLang);
    </script>
</body>
</html>"""


# ─── HTML 渲染 ────────────────────────────────────────────────────────────────

def render_html(snapshot: dict, diff_result: dict, timeline_data: list[dict], output_path: Path, lang: str, i18n_dict: dict):
    """渲染最终 HTML"""
    try:
        from jinja2 import Template
    except ImportError:
        print("[ERROR] 需要安装 jinja2: pip install jinja2", file=sys.stderr)
        sys.exit(1)

    template = Template(HTML_TEMPLATE)

    skills = snapshot.get("skills", [])
    memories = snapshot.get("memories", [])
    cron_jobs = snapshot.get("cron_jobs", [])

    # 统计进化数据
    evolution = compute_evolution_stats(timeline_data)

    html = template.render(
        i18n=i18n_dict,
        i18n_all=json.dumps(TRANSLATIONS, ensure_ascii=False),
        lang=lang,
        title=i18n_dict.get("page_title", "Hermes Evolution Log"),
        last_updated=snapshot["timestamp"][:19].replace("T", " "),
        stats={
            "skills": len(skills),
            "memories": len(memories),
            "cron_jobs": len(cron_jobs),
            "total_changes": sum(len(entry.get("changes", [])) for entry in timeline_data),
        },
        evolution=evolution,
        skills=skills,
        memories=memories,
        timeline=timeline_data,
    )

    output_path.write_text(html, encoding="utf-8")
    print(f"[OK] HTML 已生成: {output_path}")


def compute_evolution_stats(timeline_data: list[dict]) -> dict:
    """从时间线数据计算进化统计"""
    skills_added = 0
    skills_updated = 0
    memories_changed = 0
    for entry in timeline_data:
        for c in entry.get("changes", []):
            t = c.get("type", "")
            if t == "skill_added":
                skills_added += 1
            elif t == "skill_updated":
                skills_updated += 1
            elif t.startswith("memory_"):
                memories_changed += 1
    return {
        "skills_added": skills_added,
        "skills_updated": skills_updated,
        "memories_changed": memories_changed,
    }


def load_timeline(output_dir: Path) -> list[dict]:
    """加载已有的时间线数据"""
    timeline_file = output_dir / "timeline.json"
    if timeline_file.exists():
        try:
            return json.loads(timeline_file.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def save_timeline(output_dir: Path, data: list[dict]):
    """保存时间线数据"""
    timeline_file = output_dir / "timeline.json"
    timeline_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def append_timeline_entry(timeline: list[dict], diff_result: dict, snapshot: dict, lang: str):
    """将 diff 结果追加为时间线条目"""
    if diff_result.get("is_baseline"):
        return

    changes = diff_result.get("changes", [])
    if not changes:
        return

    # 生成变更摘要
    summary_parts = []
    change_details = []
    type_counts = {}
    for c in changes:
        t = c["type"]
        type_counts[t] = type_counts.get(t, 0) + 1

    # 构建摘要
    if type_counts.get("skill_added", 0):
        summary_parts.append(i18n_t(lang, "change_skill_added", n=type_counts["skill_added"]))
    if type_counts.get("skill_updated", 0):
        summary_parts.append(i18n_t(lang, "change_skill_updated", n=type_counts["skill_updated"]))
    if type_counts.get("skill_removed", 0):
        summary_parts.append(i18n_t(lang, "change_skill_removed", n=type_counts["skill_removed"]))
    if type_counts.get("memory_added", 0):
        summary_parts.append(i18n_t(lang, "change_memory_added", n=type_counts["memory_added"]))
    if type_counts.get("memory_removed", 0):
        summary_parts.append(i18n_t(lang, "change_memory_removed", n=type_counts["memory_removed"]))
    if type_counts.get("cron_added", 0):
        summary_parts.append(i18n_t(lang, "change_cron_added", n=type_counts["cron_added"]))
    if type_counts.get("cron_removed", 0):
        summary_parts.append(i18n_t(lang, "change_cron_removed", n=type_counts["cron_removed"]))

    for c in changes:
        detail_desc = ""
        if c["type"] == "skill_added":
            detail_desc = c["detail"].get("description", "")[:80]
        elif c["type"] == "skill_updated":
            old_v = c.get("old", {}).get("version", "")
            new_v = c["detail"].get("version", "")
            detail_desc = f"v{old_v} → v{new_v}" if old_v and new_v else i18n_t(lang, "change_skill_updated_detail")
        elif c["type"] == "memory_added":
            detail_desc = c["detail"].get("content", "")[:60]
        elif c["type"] == "memory_removed":
            detail_desc = c["detail"].get("content", "")[:60]
        elif c["type"] in ("cron_added", "cron_removed"):
            detail_desc = c["detail"].get("name", "")

        change_details.append({
            "type": c["type"],
            "name": c["name"],
            "desc": detail_desc,
        })

    date_str = snapshot["timestamp"][:10]
    entry = {
        "date": date_str,
        "title": " · ".join(summary_parts) if summary_parts else i18n_t(lang, "change_title_fallback"),
        "summary": i18n_t(lang, "change_summary", n=len(changes)),
        "changes": change_details,
        "has_gap": diff_result.get("has_gap", False),
        "future": False,
    }

    # 插入到时间线最前面
    timeline.insert(0, entry)

    # 清理 3 个月前的记录
    cutoff = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
    timeline = [e for e in timeline if e["date"] >= cutoff or e.get("future")]


def full_rebuild_timeline(snapshots_dir: Path, timeline: list[dict]) -> list[dict]:
    """全量重写时间线：压缩 3 个月前的记录"""
    # 从快照重建
    return trim_timeline(timeline)


def trim_timeline(timeline: list[dict], days: int = 90) -> list[dict]:
    """裁剪旧记录"""
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    return [e for e in timeline if e["date"] >= cutoff or e.get("future")]


# ─── 工具函数 ────────────────────────────────────────────────────────────────

def hash_content(text: str) -> str:
    import hashlib
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


# ─── 主入口 ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Hermes Evolution Log Generator (生成器)")
    parser.add_argument("--hermes-home", default=str(get_hermes_home()),
                        help="Hermes data directory path (数据目录路径)")
    parser.add_argument("--output-dir", default=str(get_project_dir() / "output"),
                        help="Output directory (输出目录)")
    parser.add_argument("--baseline", action="store_true",
                        help="Create baseline snapshot (no change records)")
    parser.add_argument("--full-rebuild", action="store_true",
                        help="Full rebuild HTML (trim old records)")
    parser.add_argument("--lang", choices=["zh", "en"], default=None,
                        help="Output language: zh or en (default: EVOLUTION_LANG env or zh)")
    args = parser.parse_args()

    lang = resolve_lang(args.lang)
    i18n_dict = i18n_get(lang)

    hermes_home = Path(args.hermes_home)
    output_dir = Path(args.output_dir)
    snap_dir = snapshots_dir(output_dir)

    if not hermes_home.exists():
        print(f"[ERROR] Hermes data dir not found: {hermes_home}", file=sys.stderr)
        print(f"        Use --hermes-home to specify correct path", file=sys.stderr)
        sys.exit(1)

    print(i18n_t(lang, "console_data_dir", path=hermes_home))
    print(i18n_t(lang, "console_output_dir", path=output_dir))

    # 采集快照
    print(i18n_t(lang, "console_collecting"))
    snapshot = collect_snapshot(hermes_home)
    save_snapshot(snap_dir, snapshot)

    # 加载已有时间线
    timeline = load_timeline(output_dir)

    # 对比
    prev = latest_snapshot(snap_dir)
    all_snaps = sorted(snap_dir.glob("*.json"))
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
            append_timeline_entry(timeline, diff_result, snapshot, lang)

    # 保存时间线
    save_timeline(output_dir, timeline)

    # 渲染 HTML
    html_path = output_dir / "index.html"
    render_html(snapshot, diff_result, timeline, html_path, lang, i18n_dict)

    # 汇总
    print(f"\n{'='*50}")
    print(f"   Skills: {len(snapshot['skills'])}")
    print(f"   Memories: {len(snapshot.get('memories', []))}")
    print(f"   Cron Jobs: {len(snapshot.get('cron_jobs', []))}")
    print(f"   时间线条目: {len(timeline)}" if lang == "zh" else f"   Timeline entries: {len(timeline)}")
    print(f"   输出: {html_path}" if lang == "zh" else f"   Output: {html_path}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
