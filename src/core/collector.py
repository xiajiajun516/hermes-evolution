"""
Hermes Evolution Log — 数据采集模块 (Collector)
负责采集 Hermes Agent 的 Skills、Memory、Cron Jobs 数据。
"""

import hashlib
import json
import os
import re
import sqlite3
import sys
import yaml
from datetime import datetime
from pathlib import Path


def hash_content(text: str) -> str:
    """对字符串计算 sha256 短哈希"""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def parse_skill_frontmatter(content: str) -> dict:
    """解析 YAML frontmatter"""
    m = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not m:
        return {}
    try:
        return yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        return {}


def collect_skills(hermes_home: Path) -> list[dict]:
    """扫描 skills 目录，解析每个 SKILL.md"""
    skills_dir = hermes_home / "skills"
    if not skills_dir.is_dir():
        return []

    skills = []
    for skill_md in skills_dir.rglob("SKILL.md"):
        rel = skill_md.relative_to(skills_dir)
        # 提取顶级分类目录名（如 creative/ascii-art/SKILL.md 提取为 creative）
        parts = rel.parts
        if len(parts) > 2:  # 例如 mlops/evaluation/weights-and-biases/SKILL.md 或 creative/ascii-art/SKILL.md
            category = parts[0]
        elif len(parts) == 2:  # 例如 category/SKILL.md
            category = parts[0]
        else:
            category = "general"

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

    # 方式4: scope-recall/memory.sqlite3
    scope_db = hermes_home / "scope-recall" / "memory.sqlite3"
    if scope_db.exists():
        try:
            conn = sqlite3.connect(str(scope_db))
            conn.row_factory = sqlite3.Row
            tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
            if "memories" in tables:
                cur = conn.execute(
                    "SELECT id, scope_id, target, content, source, created_at, updated_at "
                    "FROM memories ORDER BY target, created_at"
                )
                for r in cur.fetchall():
                    memories.append({
                        "id": r["id"],
                        "scope_id": r["scope_id"],
                        "target": r["target"],
                        "content": r["content"][:200] + ("..." if len(r["content"]) > 200 else ""),
                        "source": "scope-recall",
                        "created_at": r["created_at"],
                        "updated_at": r["updated_at"],
                        "content_hash": hash_content(r["content"]),
                    })
            conn.close()
        except Exception as e:
            print(f"[WARN] scope-recall memory 读取失败: {e}", file=sys.stderr)

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


def collect_all(hermes_home: Path) -> dict:
    """采集 Hermes Agent 的所有数据 (skills, memories, cron_jobs, timestamp)"""
    return collect_snapshot(hermes_home)
