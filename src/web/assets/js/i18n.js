// src/web/assets/js/i18n.js

export const TRANSLATIONS = {
  zh: {
    page_title: "Hermes 进化记录",
    page_subtitle: "AI 能力成长追踪",
    page_updated: "最近更新",
    page_updated_sep: "：",
    stat_skills: "Skills 技能",
    stat_memories: "持久记忆",
    stat_cron: "定时任务",
    stat_changes: "累计进化",

    tab_dashboard: "仪表盘",
    tab_skills: "Skills 技能",
    tab_memory: "持久记忆",
    tab_archive: "进化档案",

    section_overview: "📈 进化概览",
    section_skills: "🛠️ 已掌握的 Skills",
    section_memories: "🧠 持久记忆",
    section_timeline: "📅 进化时间线",
    section_recent_activity: "⚡ 最近进化动态",

    evo_skills_added: "新增技能",
    evo_skills_updated: "技能更新",
    evo_memories_changed: "记忆变更",

    skill_no_desc: "暂无描述",
    skill_category_all: "全部分类",
    skill_version: "版本",
    skill_path: "路径",
    skill_hash: "哈希",

    memory_type_all: "全部",
    memory_type_user: "用户",
    memory_type_memory: "记忆",
    memory_empty: "暂无相关记忆记录",

    archive_empty_title: "暂无进化记录",
    archive_empty_desc: "当 Skills、Memory 或 Cron Jobs 发生变化时，记录将自动出现在这里。",
    archive_stats_skills: "Skills",
    archive_stats_memories: "记忆",
    archive_stats_cron: "定时任务",
    archive_evo_points: "进化点",
    archive_expand: "展开变更详情",
    archive_collapse: "收起变更详情",
    archive_view_diff: "查看 Visual Diff 对比",
    timeline_gap_warning: "⚠️ 期间包含合并变更",

    search_placeholder: "搜索 Skills / 记忆 / 档案...",
    search_empty: "未搜索到匹配的内容",
    loading: "加载数据中...",
    error_loading: "数据加载失败，请刷新页面重试",

    change_skill_added: "新增 {n} 个技能",
    change_skill_updated: "更新 {n} 个技能",
    change_skill_removed: "移除 {n} 个技能",
    change_memory_added: "新增 {n} 条记忆",
    change_memory_removed: "移除 {n} 条记忆",
    change_cron_added: "新增 {n} 个定时任务",
    change_cron_removed: "移除 {n} 个定时任务",
    change_skill_updated_detail: "内容更新",
    change_title_fallback: "进化更新",
    change_summary: "本次共检测到 {n} 项变更",
    change_count_label: "{n} 项变更"
  },
  en: {
    page_title: "Hermes Evolution Log",
    page_subtitle: "AI Capability Growth Tracker",
    page_updated: "Last updated",
    page_updated_sep: ": ",
    stat_skills: "Skills Mastered",
    stat_memories: "Persistent Memories",
    stat_cron: "Cron Jobs",
    stat_changes: "Total Evolutions",

    tab_dashboard: "Dashboard",
    tab_skills: "Skills",
    tab_memory: "Memory",
    tab_archive: "Evolution Archive",

    section_overview: "📈 Evolution Overview",
    section_skills: "🛠️ Mastered Skills",
    section_memories: "🧠 Persistent Memory",
    section_timeline: "📅 Evolution Timeline",
    section_recent_activity: "⚡ Recent Evolutions",

    evo_skills_added: "Skills Added",
    evo_skills_updated: "Skills Updated",
    evo_memories_changed: "Memory Changes",

    skill_no_desc: "No description provided",
    skill_category_all: "All Categories",
    skill_version: "Version",
    skill_path: "Path",
    skill_hash: "Hash",

    memory_type_all: "All",
    memory_type_user: "User",
    memory_type_memory: "Memory",
    memory_empty: "No matching memory records",

    archive_empty_title: "No Evolution Log Yet",
    archive_empty_desc: "Records will automatically appear here when Skills, Memory, or Cron Jobs change.",
    archive_stats_skills: "Skills",
    archive_stats_memories: "Memories",
    archive_stats_cron: "Cron Jobs",
    archive_evo_points: "Evolutions",
    archive_expand: "Expand details",
    archive_collapse: "Collapse details",
    archive_view_diff: "View Visual Diff",
    timeline_gap_warning: "⚠️ Merged changes in this period",

    search_placeholder: "Search Skills / Memories / Archives...",
    search_empty: "No matching items found",
    loading: "Loading data...",
    error_loading: "Failed to load data, please refresh and retry",

    change_skill_added: "{n} skill(s) added",
    change_skill_updated: "{n} skill(s) updated",
    change_skill_removed: "{n} skill(s) removed",
    change_memory_added: "{n} memor(ies) added",
    change_memory_removed: "{n} memor(ies) removed",
    change_cron_added: "{n} cron job(s) added",
    change_cron_removed: "{n} cron job(s) removed",
    change_skill_updated_detail: "content updated",
    change_title_fallback: "Evolution Update",
    change_summary: "{n} change(s) detected",
    change_count_label: "{n} change(s)"
  }
};

export function t(key, params = {}, lang = 'zh') {
  const dict = TRANSLATIONS[lang] || TRANSLATIONS['zh'];
  let text = dict[key] || TRANSLATIONS['zh'][key] || key;

  Object.keys(params).forEach(pKey => {
    text = text.replace(new RegExp(`\\{${pKey}\\}`, 'g'), params[pKey]);
  });

  return text;
}
