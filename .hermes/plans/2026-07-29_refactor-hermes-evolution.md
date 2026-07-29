# 🧬 Hermes Evolution Log 前后端解耦与工程化重构 Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** 重构 `hermes-evolution` 架构，实现数据采集与前端渲染彻底解耦。后端 Python 专注于数据采集、Diff 算法与 JSON API 输出；前端采用轻量 Vanilla JS + ES Modules 动态渲染组件，支持 Visual Side-by-Side Diff 增删对比与图表呈现，零 Node 构建依赖。

**Architecture:** 
1. **后端数据层 (`src/core/`)**：拆分 `generate.py` 为模块化的 Python 包。包含 `collector.py`（技能/记忆/任务采集）、`diff_engine.py`（快照比对算法）、`exporter.py`（生成 API 数据 JSON 及数据压缩）。
2. **前端渲染层 (`src/web/`)**：采用原生 HTML5 + CSS Variables + Vanilla JS ES Modules 前后端分离模式。包含 `index.html`（宿主）、`app.js`（入口与状态路由）、`store.js`（数据中心）、`i18n.js`（多语言）以及 View 组件库（`dashboard.js`, `skills.js`, `memory.js`, `archive.js`, `diff_modal.js`）。
3. **兼容性与 CLI 接口**：保留根目录 `generate.py` 命令行入口，保证 Docker 部署与现有 CLI 指令 (`--baseline`, `--full-rebuild`, `--project`) 100% 兼容。

**Tech Stack:** Python 3.11, Standard Libraries, PyYAML, Vanilla JS (ES6 Modules), CSS3 Variables, Diff2Html / Light Diff Engine.

---

### Task 1: 后端代码结构化拆分 (Python Core)

**Objective:** 将单文件 `generate.py` 的数据采集与 Diff 比对逻辑解耦，提取为干净的核心模块。

**Files:**
- Create: `src/core/__init__.py`
- Create: `src/core/collector.py`
- Create: `src/core/diff_engine.py`
- Modify: `generate.py:1-120`

**Step 1: 编写测试/验证脚本确认采集逻辑**

在 `tests/test_collector.py` 中验证 `collector.py` 能成功从 Hermes Home 采集 Skills, Memory, Cron 数据。

```python
# tests/test_collector.py
from pathlib import Path
from src.core.collector import collect_all

def test_collect_all():
    data = collect_all(Path.home() / "AppData/Local/hermes")
    assert "skills" in data
    assert "memories" in data
    assert "cron_jobs" in data
```

**Step 2: 拆分 `collector.py` 与 `diff_engine.py`**

从 `generate.py` 中抽取 `collect_skills`, `collect_memory`, `collect_cron` 至 `src/core/collector.py`，抽取 `compare_snapshots`, `summarize_snapshot` 至 `src/core/diff_engine.py`。

**Step 3: 验证后端测试通过**

Run: `python -m pytest tests/` 或 `python tests/test_collector.py`
Expected: PASS

**Step 4: Commit**

```bash
git add src/core/ tests/ generate.py
git commit -m "refactor(core): 拆分后端采集器与 Diff 引擎模块"
```

---

### Task 2: 设计 RESTful 标准 JSON 数据架构 (`data.json` & `timeline.json`)

**Objective:** 统一后端导出的数据 Schema，使前端可以独立消费 JSON API 数据。

**Files:**
- Create: `src/core/exporter.py`
- Create: `output/api/v1/meta.json` (自动生成)
- Create: `output/api/v1/timeline.json` (自动生成)

**Step 1: 实现 `src/core/exporter.py`**

实现将采集到的 `snapshot` 和计算后的 `timeline` 序列化为规范 JSON 的导出工具函数。

```python
# src/core/exporter.py
import json
from pathlib import Path

def export_data(output_dir: Path, timeline: list, current_snapshot: dict, meta: dict):
    api_dir = output_dir / "api" / "v1"
    api_dir.mkdir(parents=True, exist_ok=True)
    
    (api_dir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    (api_dir / "timeline.json").write_text(json.dumps(timeline, ensure_ascii=False, indent=2), encoding="utf-8")
    (api_dir / "latest.json").write_text(json.dumps(current_snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
```

**Step 2: 运行 CLI 验证 JSON 导出**

Run: `python generate.py --output-dir ./output`
Expected: `output/api/v1/` 目录下成功生成 `meta.json`, `timeline.json`, `latest.json`。

**Step 3: Commit**

```bash
git add src/core/exporter.py generate.py
git commit -m "feat(exporter): 实现前后端分离的标准 JSON 导出机制"
```

---

### Task 3: 构建前端 HTML 宿主与 ES Modules 核心架构

**Objective:** 创建干净的前端应用结构，包含通用 CSS 变量、响应式布局及核心 Data Store。

**Files:**
- Create: `src/web/index.html`
- Create: `src/web/assets/css/main.css`
- Create: `src/web/assets/js/store.js`
- Create: `src/web/assets/js/app.js`

**Step 1: 创建 `src/web/index.html` 容器页面**

只保留干净的 DOM 结构挂载点 (Header, Tab Buttons, `#app-view` 挂载点, Modal 弹窗等)。

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <title>Hermes Evolution Log</title>
  <link rel="stylesheet" href="assets/css/main.css">
</head>
<body class="dark-theme">
  <header id="app-header"></header>
  <nav id="app-tabs"></nav>
  <main id="app-content"></main>
  <div id="modal-container"></div>
  <script type="module" src="assets/js/app.js"></script>
</body>
</html>
```

**Step 2: 实现 `store.js` 响应式状态中心**

提供异步拉取 `/api/v1/timeline.json` 和 `/api/v1/latest.json` 的能力，并管理当前选中的 Tab、搜索关键词、项目筛选器状态。

```js
// src/web/assets/js/store.js
export const store = {
  state: {
    meta: null,
    timeline: [],
    latest: null,
    currentTab: 'dashboard',
    searchQuery: '',
    selectedProject: 'all',
    lang: localStorage.getItem('hermes_lang') || 'zh'
  },
  async loadData() {
    const [metaRes, timelineRes, latestRes] = await Promise.all([
      fetch('api/v1/meta.json').then(r => r.json()),
      fetch('api/v1/timeline.json').then(r => r.json()),
      fetch('api/v1/latest.json').then(r => r.json())
    ]);
    this.state.meta = metaRes;
    this.state.timeline = timelineRes;
    this.state.latest = latestRes;
  }
};
```

**Step 3: 验证前端静态服务加载**

使用浏览器查看本地生成的静态主页，确认成功动态异步拉取 API 数据。

**Step 4: Commit**

```bash
git add src/web/
git commit -m "feat(web): 初始化前端静态宿主与 ES Modules Store 架构"
```

---

### Task 4: 实现前端视图组件模块化 (`Dashboard`, `Skills`, `Memory`, `Archive`)

**Objective:** 将原本在 Python 中拼接的 4 个独立 Tab 页面改写为可维护的前端组件。

**Files:**
- Create: `src/web/assets/js/components/dashboard.js`
- Create: `src/web/assets/js/components/skills.js`
- Create: `src/web/assets/js/components/memory.js`
- Create: `src/web/assets/js/components/archive.js`

**Step 1: 开发 `dashboard.js` 组件**

渲染 Skills/Memory/Cron 计数卡片、总进化次数及近期的进化摘要演变。

**Step 2: 开发 `skills.js` 与 `memory.js` 组件**

渲染 Skill 卡片网格、分类标签，以及 Memory 列表分组（User / Memory）。

**Step 3: 开发 `archive.js` 进化档案组件**

支持时间轴列表呈现，含变更指标条、关键词标签与卡片收起/展开。

**Step 4: Commit**

```bash
git add src/web/assets/js/components/
git commit -m "feat(web): 完成 Dashboard, Skills, Memory, Archive 四大 Tab 组件重构"
```

---

### Task 5: 开发 Side-by-Side Visual Diff 增删对比组件 (P0 核心增强)

**Objective:** 解决用户在进化记录中看纯文本修改不直观的问题，引入轻量文本 Diff 渲染卡片。

**Files:**
- Create: `src/web/assets/js/components/diff_view.js`
- Modify: `src/web/assets/js/components/archive.js`

**Step 1: 实现轻量 Diff 算法与高亮渲染 (`diff_view.js`)**

支持 Unified / Side-by-Side 模式，对新增行标注背景绿高亮，删除行标注背景红高亮，修改处逐字对比。

```js
// src/web/assets/js/components/diff_view.js
export function renderDiff(oldText, newText) {
  // 生成标准 HTML 格式的 Diff 对比块
  return `<div class="diff-viewer">...</div>`;
}
```

**Step 2: 在 Archive 档案卡片展开中集成 Diff 视图**

点击“查看变更详情”时，自动调用 `diff_view.js` 渲染红绿高亮视图。

**Step 3: Commit**

```bash
git add src/web/assets/js/components/diff_view.js
git commit -m "feat(ui): 新增 Side-by-Side Visual Diff 文本变更对比高亮组件"
```

---

### Task 6: 自动构建构建整合与一键生成打包

**Objective:** 更新 `generate.py` 主程序，使其在执行 `python generate.py` 时自动完成数据采集导出与静态 Web 资源的组合打包。

**Files:**
- Modify: `generate.py`
- Modify: `Dockerfile`

**Step 1: 组装 `generate.py` 主逻辑**

```python
# generate.py
from src.core.collector import collect_all
from src.core.diff_engine import generate_timeline
from src.core.exporter import export_site

def main():
    # 1. 采集数据
    # 2. 计算 Diff
    # 3. 复制 src/web 到 output/ 并写入 api/ 静态数据
    export_site(output_dir, timeline, latest_snapshot)
    print("✨ Successfully updated evolution dashboard at output/index.html")

if __name__ == "__main__":
    main()
```

**Step 2: 端到端功能测试**

Run: `python generate.py --full-rebuild`
Expected: 顺利生成 `output/index.html` 并且可在浏览器无缝访问完整功能。

**Step 3: Commit**

```bash
git add generate.py Dockerfile
git commit -m "refactor: 完成前后端分离重构联调与 CLI 主程序组装"
```

---

## Risk & Tradeoffs

1. **同源策略 (CORS) 限制**：
   - *风险*：如果用户直接使用 `file:///.../output/index.html` 打开页面，浏览器可能因 ES Modules / `fetch()` 限制拦截 API 请求。
   - *应对*：在数据打包步骤中，支持将初始 API 数据集中内嵌在 `output/index.html` 头的 `<script id="initial-data">` 变量中；当无法通过 `fetch()` 读取外部 JSON 时，平滑降级使用内嵌静态数据。这样依然保持直接本地打开 HTML 的零部署优势。

2. **Docker 与依赖**：
   - 完全不需要安装 node/npm 依赖，镜像体积保持小巧。

---
