"""
Hermes Evolution Log — Diff 引擎模块 (Diff Engine)
负责快照管理、快照对比、变更摘要计算及时间线维护。
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

try:
    from i18n import t as i18n_t
except ImportError:
    def i18n_t(lang: str, key: str, **kwargs) -> str:
        return key


# ─── 快照管理 ────────────────────────────────────────────────────────────────

def snapshots_dir(output_dir: Path) -> Path:
    """获取并确保快照存储目录存在"""
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


# ─── Diff 引擎与对比 ─────────────────────────────────────────────────────────

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


def compare_snapshots(old: dict | None, new: dict) -> dict:
    """对比两个快照 (diff_snapshots 的别名)"""
    return diff_snapshots(old, new)


def summarize_snapshot(snapshot: dict) -> dict:
    """对单个快照提取统计摘要"""
    return {
        "timestamp": snapshot.get("timestamp", ""),
        "skills_count": len(snapshot.get("skills", [])),
        "memories_count": len(snapshot.get("memories", [])),
        "cron_jobs_count": len(snapshot.get("cron_jobs", [])),
    }


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


# ─── 时间线数据处理 ───────────────────────────────────────────────────────────

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


def append_timeline_entry(timeline: list[dict], diff_result: dict, snapshot: dict, lang: str, project: str = ""):
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
        "project": project,
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
    timeline[:] = [e for e in timeline if e["date"] >= cutoff or e.get("future")]


def trim_timeline(timeline: list[dict], days: int = 90) -> list[dict]:
    """裁剪旧记录"""
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    return [e for e in timeline if e["date"] >= cutoff or e.get("future")]


def full_rebuild_timeline(snapshots_dir: Path, timeline: list[dict]) -> list[dict]:
    """全量重写时间线：压缩 3 个月前的记录"""
    return trim_timeline(timeline)
