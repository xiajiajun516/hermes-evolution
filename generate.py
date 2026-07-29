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
from src.core.collector import (
    collect_all,
    collect_cron_jobs,
    collect_memory,
    collect_skills,
    collect_snapshot,
    hash_content,
    parse_skill_frontmatter,
)
from src.core.diff_engine import (
    append_timeline_entry,
    compare_snapshots,
    compute_evolution_stats,
    diff_snapshots,
    full_rebuild_timeline,
    latest_snapshot,
    load_timeline,
    save_snapshot,
    save_timeline,
    snapshots_dir,
    summarize_snapshot,
    trim_timeline,
)


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


def detect_project(project_dir: Path | None = None) -> str:
    """自动检测项目名：优先 git remote origin 的 repo 名，否则用目录名"""
    import subprocess as sp
    d = project_dir or get_project_dir()
    try:
        r = sp.run(["git", "remote", "get-url", "origin"],
                   cwd=str(d), capture_output=True, text=True, timeout=5)
        if r.returncode == 0:
            url = r.stdout.strip()
            # Extract repo name from git URL
            name = url.rstrip("/").split("/")[-1].removesuffix(".git")
            if name:
                return name
    except Exception:
        pass
    return d.name





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

        /* Tab 导航 */
        .tab-nav {
            max-width: 1000px; margin: 0 auto; padding: 0 20px;
            display: flex; gap: 0; border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        .tab-btn {
            background: none; border: none; color: #888;
            font-size: 0.95rem; padding: 12px 24px; cursor: pointer;
            border-bottom: 2px solid transparent; transition: all 0.3s ease;
            font-family: inherit;
        }
        .tab-btn:hover { color: #ccc; }
        .tab-btn.active { color: #a5b4fc; border-bottom-color: #667eea; }
        .tab-panel { display: none; }
        .tab-panel.active { display: block; margin-top: 30px; }

        /* 档案卡片 */
        .archive-grid {
            display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 20px;
        }
        .archive-card {
            background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08);
            border-radius: 16px; padding: 24px; transition: all 0.3s ease;
        }
        .archive-card:hover {
            transform: translateY(-2px); border-color: rgba(102,126,234,0.3);
            box-shadow: 0 8px 32px rgba(0,0,0,0.2);
        }
        .archive-project {
            color: #f093fb; font-weight: 500;
        }
        .archive-filter {
            margin-bottom: 20px;
        }
        .archive-date { font-size: 0.8rem; color: #667eea; margin-bottom: 8px; }

        /* 搜索框 */
        .search-bar {
            max-width: 400px; margin: 16px auto 0; padding: 0 20px;
            position: relative;
        }
        .search-bar input {
            width: 100%; padding: 10px 16px 10px 40px;
            background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.12);
            border-radius: 24px; color: #e0e0e0; font-size: 0.9rem;
            font-family: inherit; outline: none; transition: all 0.3s ease;
        }
        .search-bar input:focus { border-color: rgba(102,126,234,0.5); background: rgba(255,255,255,0.08); }
        .search-bar input::placeholder { color: #666; }
        .search-icon { position: absolute; left: 32px; top: 50%; transform: translateY(-50%); font-size: 0.9rem; opacity: 0.5; }
        .search-hidden { display: none !important; }
        .archive-title { font-size: 1.1rem; font-weight: 600; color: #fff; margin-bottom: 8px; }
        .archive-summary { font-size: 0.9rem; color: #999; margin-bottom: 16px; }
        .archive-stats {
            display: flex; flex-wrap: wrap; gap: 12px; margin-bottom: 12px;
            font-size: 0.8rem; color: #888;
        }
        .archive-stat { white-space: nowrap; }
        .archive-tags { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 12px; }
        .archive-tag {
            font-size: 0.7rem; padding: 3px 10px;
            background: rgba(102,126,234,0.12); border-radius: 12px; color: #a5b4fc;
        }
        .archive-details {
            margin-top: 8px; padding-top: 8px;
            border-top: 1px solid rgba(255,255,255,0.05);
            font-size: 0.85rem; color: #777;
        }
        .archive-details summary { cursor: pointer; color: #888; }
        .archive-details summary:hover { color: #a5b4fc; }
        .archive-details ul { margin-top: 8px; padding-left: 16px; }
        .archive-details li { margin-bottom: 4px; }

        /* 空状态 */
        .archive-empty { text-align: center; padding: 80px 20px; }
        .empty-illustration { margin-bottom: 24px; opacity: 0.3; }
        .archive-empty h3 { font-size: 1.3rem; color: #aaa; margin-bottom: 8px; }
        .archive-empty p { font-size: 0.9rem; color: #666; max-width: 400px; margin: 0 auto; }

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
        <p class="update"><span data-i18n="page_updated">{{ i18n.page_updated }}</span>{{ i18n.page_updated_sep }}{{ last_updated }}</p>
    </div>

    <div class="search-bar">
        <span class="search-icon">🔍</span>
        <input type="text" id="search-input" data-i18n-attr="placeholder:search_placeholder"
               placeholder="{{ i18n.search_placeholder }}" oninput="doSearch(this.value)" autocomplete="off">
    </div>

    <div class="tab-nav">
        <button class="tab-btn active" data-tab="dashboard" onclick="switchTab('dashboard')" data-i18n="tab_dashboard">{{ i18n.tab_dashboard }}</button>
        <button class="tab-btn" data-tab="skills" onclick="switchTab('skills')" data-i18n="section_skills">{{ i18n.section_skills }}</button>
        <button class="tab-btn" data-tab="memory" onclick="switchTab('memory')" data-i18n="section_memories">{{ i18n.section_memories }}</button>
        <button class="tab-btn" data-tab="archive" onclick="switchTab('archive')" data-i18n="tab_archive">{{ i18n.tab_archive }}</button>
    </div>

    <div id="tab-dashboard" class="tab-panel active">
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
    </div><!-- /tab-dashboard -->

    <div id="tab-skills" class="tab-panel">
    <div class="section">
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
    </div><!-- /tab-skills -->

    <div id="tab-memory" class="tab-panel">
    <div class="section">
        <div class="memories-grid">
            {% for mem in memories %}
            <div class="memory-card">
                <span class="memory-type {{ mem.target }}" data-i18n="{{ 'memory_type_user' if mem.target == 'user' else 'memory_type_memory' }}">{{ i18n.memory_type_user if mem.target == "user" else i18n.memory_type_memory }}</span>
                <p class="memory-content">{{ mem.content }}</p>
            </div>
            {% endfor %}
        </div>
    </div>
    </div><!-- /tab-memory -->

    <div id="tab-archive" class="tab-panel">
    <div class="section">
        {% if timeline %}
        {% if projects|length > 1 %}
        <div class="archive-filter">
            <select onchange="filterArchive(this.value)" style="background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.12);color:#ccc;padding:6px 12px;border-radius:8px;font-family:inherit;">
                <option value="all">All Projects</option>
                {% for p in projects %}
                <option value="{{ p }}">{{ p }}</option>
                {% endfor %}
            </select>
        </div>
        {% endif %}
        <div class="archive-grid">
            {% for entry in timeline %}
            <div class="archive-card" data-project="{{ entry.project }}">
                <div class="archive-date">{{ entry.date }}{% if entry.project %} · <span class="archive-project">{{ entry.project }}</span>{% endif %}</div>
                <h3 class="archive-title">{{ entry.title }}</h3>
                <p class="archive-summary">{{ entry.summary }}</p>
                <div class="archive-stats">
                    {% set skill_n = entry.changes | selectattr('type', 'in', ['skill_added','skill_updated','skill_removed']) | list | length %}
                    {% set mem_n = entry.changes | selectattr('type', 'in', ['memory_added','memory_removed']) | list | length %}
                    {% set cron_n = entry.changes | selectattr('type', 'in', ['cron_added','cron_removed']) | list | length %}
                    <span class="archive-stat">● <span data-i18n="archive_stats_skills">{{ i18n.archive_stats_skills }}</span>: {{ skill_n }}</span>
                    <span class="archive-stat">● <span data-i18n="archive_stats_memories">{{ i18n.archive_stats_memories }}</span>: {{ mem_n }}</span>
                    <span class="archive-stat">● <span data-i18n="archive_stats_cron">{{ i18n.archive_stats_cron }}</span>: {{ cron_n }}</span>
                    <span class="archive-stat">⚡ <span data-i18n="archive_evo_points">{{ i18n.archive_evo_points }}</span>: {{ entry.changes|length }}</span>
                </div>
                <div class="archive-tags" data-tags-source="{{ entry.title }} {{ entry.changes | map(attribute='name') | join(' ') }}"></div>
                {% if entry.changes %}
                <details class="archive-details">
                    <summary><span data-i18n="archive_expand">{{ i18n.archive_expand }}</span> ({{ entry.changes|length }})</summary>
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
            {% endfor %}
        </div>
        {% else %}
        <div class="archive-empty">
            <div class="empty-illustration">
                <svg width="120" height="120" viewBox="0 0 120 120" fill="none">
                    <rect x="20" y="30" width="80" height="60" rx="8" stroke="#667eea" stroke-width="1.5" stroke-dasharray="4 4" opacity="0.5"/>
                    <circle cx="45" cy="55" r="6" stroke="#667eea" stroke-width="1.5" opacity="0.4"/>
                    <line x1="55" y1="55" x2="85" y2="55" stroke="#667eea" stroke-width="1.5" opacity="0.3"/>
                    <line x1="55" y1="65" x2="75" y2="65" stroke="#667eea" stroke-width="1.5" opacity="0.2"/>
                    <circle cx="60" cy="60" r="30" stroke="#764ba2" stroke-width="1" opacity="0.15"/>
                </svg>
            </div>
            <h3 data-i18n="archive_empty_title">{{ i18n.archive_empty_title }}</h3>
            <p data-i18n="archive_empty_desc">{{ i18n.archive_empty_desc }}</p>
        </div>
        {% endif %}
    </div>
    </div><!-- /tab-archive -->

    <div class="footer">
        <p>Powered by <a href="https://github.com/NousResearch/hermes-agent" target="_blank">Hermes Agent</a> · <span data-i18n="footer_powered">{{ i18n.footer_powered }}</span> {{ last_updated }}</p>
    </div>

    <script>
    // ── Client-side i18n engine ──
    const I18N = {{ i18n_all }};
    const DEFAULT_LANG = '{{ lang }}';

    function getLang() {
        try {
            let lang = localStorage.getItem('evolution-lang');
            if (lang && I18N[lang]) return lang;
        } catch(e) {}
        return DEFAULT_LANG;
    }

    function switchLang(lang) {
        try {
            localStorage.setItem('evolution-lang', lang);
        } catch(e) {}
        document.documentElement.lang = lang === 'zh' ? 'zh-CN' : 'en';

        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.dataset.i18n;
            if (I18N[lang] && I18N[lang][key]) {
                const hasKids = el.children.length > 0 && el.querySelector('[data-i18n]');
                if (!hasKids) el.textContent = I18N[lang][key];
            }
        });
        document.querySelectorAll('[data-i18n-attr]').forEach(el => {
            const spec = el.dataset.i18nAttr;
            if (!spec) return;
            const idx = spec.indexOf(':');
            if (idx === -1) return;
            const attr = spec.slice(0, idx), key = spec.slice(idx + 1);
            if (I18N[lang] && I18N[lang][key]) el[attr] = I18N[lang][key];
        });
        document.querySelectorAll('.lang-btn').forEach(b => {
            b.classList.toggle('active', b.dataset.lang === lang);
        });
        if (I18N[lang]) document.title = I18N[lang].page_title || document.title;
    }

    // Init on load
    (function() {
        const savedLang = getLang();
        if (savedLang !== DEFAULT_LANG) switchLang(savedLang);
        // Always ensure correct button state (defensive)
        document.querySelectorAll('.lang-btn').forEach(b => {
            b.classList.toggle('active', b.dataset.lang === savedLang);
        });
    })();

    // ── Tab switching ──
    function switchTab(name) {
        document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.toggle('active', b.dataset.tab === name));
        const panel = document.getElementById('tab-' + name);
        if (panel) panel.classList.add('active');
        try { localStorage.setItem('evolution-tab', name); } catch(e) {}
    }
    // Init tab from localStorage
    (function() {
        let tab = 'dashboard';
        try { tab = localStorage.getItem('evolution-tab') || 'dashboard'; } catch(e) {}
        if (tab !== 'dashboard') switchTab(tab);
    })();

    // ── Tag generation for archive cards ──
    (function() {
        const TAG_MAP = {
            'skill': 'skill', '技能': 'skill', 'memory': 'memory', '记忆': 'memory',
            'cron': 'cron', '定时任务': 'cron', '新增': 'added', 'added': 'added',
            '更新': 'updated', 'updated': 'updated', '移除': 'removed', 'removed': 'removed',
        };
        document.querySelectorAll('.archive-tags').forEach(el => {
            const source = (el.dataset.tagsSource || '').toLowerCase();
            const tags = new Set();
            for (const [kw, tag] of Object.entries(TAG_MAP)) {
                if (source.includes(kw)) tags.add(tag);
            }
            tags.forEach(t => {
                const span = document.createElement('span');
                span.className = 'archive-tag';
                span.textContent = t;
                el.appendChild(span);
            });
        });
    })();

    // ── Search ──
    function doSearch(query) {
        const q = query.toLowerCase().trim();
        // Skills
        document.querySelectorAll('#tab-skills .skill-card').forEach(card => {
            const text = (card.textContent || '').toLowerCase();
            card.classList.toggle('search-hidden', q !== '' && !text.includes(q));
        });
        // Memory
        document.querySelectorAll('#tab-memory .memory-card').forEach(card => {
            const text = (card.textContent || '').toLowerCase();
            card.classList.toggle('search-hidden', q !== '' && !text.includes(q));
        });
        // Archive
        document.querySelectorAll('#tab-archive .archive-card').forEach(card => {
            const text = (card.textContent || '').toLowerCase();
            const projectMatch = q === '' || (card.dataset.project || '').toLowerCase().includes(q);
            card.classList.toggle('search-hidden', q !== '' && !text.includes(q) && !projectMatch);
        });
    }

    // ── Archive project filter ──
    function filterArchive(project) {
        document.querySelectorAll('.archive-card').forEach(card => {
            card.style.display = (project === 'all' || card.dataset.project === project) ? '' : 'none';
        });
        try { localStorage.setItem('evolution-project-filter', project); } catch(e) {}
    }
    // Restore filter on load
    (function() {
        try {
            const f = localStorage.getItem('evolution-project-filter');
            if (f && f !== 'all') { const sel = document.querySelector('.archive-filter select'); if (sel) { sel.value = f; filterArchive(f); } }
        } catch(e) {}
    })();
    </script>
</body>
</html>"""


# ─── HTML 渲染 ────────────────────────────────────────────────────────────────

def render_html(snapshot: dict, diff_result: dict, timeline_data: list[dict], output_path: Path, lang: str, i18n_dict: dict, project: str = ""):
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

    # 提取所有项目列表
    projects = sorted(set(entry.get("project", "") for entry in timeline_data if entry.get("project")))

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
        projects=projects,
        project=project,
    )

    output_path.write_text(html, encoding="utf-8")
    print(f"[OK] HTML 已生成: {output_path}")



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
    parser.add_argument("--project", default=None,
                        help="Project name for archive grouping (auto-detected from git remote)")
    args = parser.parse_args()

    lang = resolve_lang(args.lang)
    i18n_dict = i18n_get(lang)
    project = args.project or detect_project()

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
            append_timeline_entry(timeline, diff_result, snapshot, lang, project)

    # 保存时间线
    save_timeline(output_dir, timeline)

    # 渲染 HTML
    html_path = output_dir / "index.html"
    render_html(snapshot, diff_result, timeline, html_path, lang, i18n_dict, project)

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
