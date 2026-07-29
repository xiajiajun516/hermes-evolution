"""i18n translations for hermes-evolution — zh / en."""

TRANSLATIONS = {
    "zh": {
        # ── HTML page ──
        "page_title": "Hermes 进化记录",
        "page_subtitle": "AI 能力成长追踪",
        "page_updated": "最近更新",
        "page_updated_sep": "：",
        "stat_skills": "Skills 技能",
        "stat_memories": "持久记忆",
        "stat_cron": "定时任务",
        "stat_changes": "累计进化",
        "section_overview": "📈 进化概览",
        "section_skills": "🛠️ 已掌握的 Skills",
        "section_memories": "🧠 持久记忆",
        "section_timeline": "📅 进化时间线",
        "evo_skills_added": "新增技能",
        "evo_skills_updated": "技能更新",
        "evo_memories_changed": "记忆变更",
        "skill_no_desc": "暂无描述",
        "timeline_expand": "展开详情",
        "timeline_gap_warning": "⚠️ 期间包含合并变更",
        "footer_powered": "自动生成于",
        "memory_type_user": "用户",
        "memory_type_memory": "记忆",

        # ── Timeline change summary ──
        "change_skill_added": "新增 {n} 个技能",
        "change_skill_updated": "更新 {n} 个技能",
        "change_skill_removed": "移除 {n} 个技能",
        "change_memory_added": "新增 {n} 条记忆",
        "change_memory_removed": "移除 {n} 条记忆",
        "change_cron_added": "新增 {n} 个定时任务",
        "change_cron_removed": "移除 {n} 个定时任务",
        "change_skill_updated_detail": "内容更新",
        "change_title_fallback": "进化更新",
        "change_summary": "本次共检测到 {n} 项变更",
        "change_count_label": "{n} 项变更",

        # ── Console ──
        "console_baseline": "[INFO] 基线快照模式 — 不产生变更记录",
        "console_rebuild": "[INFO] 全量重写模式",
        "console_no_changes": "[INFO] 无变更，跳过时间线更新",
        "console_first_snap": "[INFO] 这是首次快照（无历史数据），视为基线",
        "console_changes": "[INFO] 检测到 {n} 项变更",
        "console_collecting": "[INFO] 采集当前快照...",
        "console_html_done": "[OK] HTML 已生成: {path}",
        "console_data_dir": "[INFO] Hermes 数据目录: {path}",
        "console_output_dir": "[INFO] 输出目录: {path}",

        # ── Archive tab ──
        "tab_dashboard": "📊 仪表盘",
        "tab_archive": "📚 进化档案",
        "archive_empty_title": "暂无进化记录",
        "archive_empty_desc": "当 Skills、Memory 或 Cron Jobs 发生变化时，记录将自动出现在这里。",
        "archive_stats_skills": "Skills",
        "archive_stats_memories": "记忆",
        "archive_stats_cron": "定时任务",
        "archive_evo_points": "进化点",
        "archive_expand": "展开变更详情",
    },
    "en": {
        # ── HTML page ──
        "page_title": "Hermes Evolution Log",
        "page_subtitle": "AI Capability Growth Tracker",
        "page_updated": "Last updated",
        "page_updated_sep": ": ",
        "stat_skills": "Skills",
        "stat_memories": "Memories",
        "stat_cron": "Cron Jobs",
        "stat_changes": "Total Evolutions",
        "section_overview": "📈 Evolution Overview",
        "section_skills": "🛠️ Skills Mastered",
        "section_memories": "🧠 Persistent Memory",
        "section_timeline": "📅 Evolution Timeline",
        "evo_skills_added": "Skills Added",
        "evo_skills_updated": "Skills Updated",
        "evo_memories_changed": "Memory Changes",
        "skill_no_desc": "No description",
        "timeline_expand": "Show details",
        "timeline_gap_warning": "⚠️ Merged changes in this period",
        "footer_powered": "Auto-generated at",
        "memory_type_user": "User",
        "memory_type_memory": "Memory",

        # ── Timeline change summary ──
        "change_skill_added": "{n} skill(s) added",
        "change_skill_updated": "{n} skill(s) updated",
        "change_skill_removed": "{n} skill(s) removed",
        "change_memory_added": "{n} memor(ies) added",
        "change_memory_removed": "{n} memor(ies) removed",
        "change_cron_added": "{n} cron job(s) added",
        "change_cron_removed": "{n} cron job(s) removed",
        "change_skill_updated_detail": "content updated",
        "change_title_fallback": "Evolution Update",
        "change_summary": "{n} change(s) detected",
        "change_count_label": "{n} change(s)",

        # ── Console ──
        "console_baseline": "[INFO] Baseline mode — no change records",
        "console_rebuild": "[INFO] Full rebuild mode",
        "console_no_changes": "[INFO] No changes, timeline skipped",
        "console_first_snap": "[INFO] First snapshot (no history), treated as baseline",
        "console_changes": "[INFO] {n} change(s) detected",
        "console_collecting": "[INFO] Collecting snapshot...",
        "console_html_done": "[OK] HTML generated: {path}",
        "console_data_dir": "[INFO] Hermes data dir: {path}",
        "console_output_dir": "[INFO] Output dir: {path}",

        # ── Archive tab ──
        "tab_dashboard": "📊 Dashboard",
        "tab_archive": "📚 Archive",
        "archive_empty_title": "No Evolution Records",
        "archive_empty_desc": "Records appear here automatically when Skills, Memory, or Cron Jobs change.",
        "archive_stats_skills": "Skills",
        "archive_stats_memories": "Memories",
        "archive_stats_cron": "Cron Jobs",
        "archive_evo_points": "Evolution Pts",
        "archive_expand": "Show changes",
    },
}


def get(lang: str) -> dict:
    """Return translation dict for given language, falling back to zh."""
    return TRANSLATIONS.get(lang, TRANSLATIONS["zh"])


def t(lang: str, key: str, **kwargs) -> str:
    """Get a single translated string with optional formatting."""
    d = get(lang)
    s = d.get(key, key)
    if kwargs:
        s = s.format(**kwargs)
    return s


def resolve_lang(args_lang: str | None = None) -> str:
    """Resolve language: CLI arg > env var > default 'zh'.
    Only 'zh' and 'en' are valid; everything else falls back to 'zh'."""
    import os
    if args_lang and args_lang in ("zh", "en"):
        return args_lang
    env = os.environ.get("EVOLUTION_LANG", "").lower()
    if env in ("zh", "en"):
        return env
    return "zh"
