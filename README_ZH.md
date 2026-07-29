# 🧬 Hermes Evolution Log (进化日记)

[![English](https://img.shields.io/badge/README-English-blue)](README.md)

> AI 进化可视化与可观测性仪表盘 — 追踪 Hermes Agent 的 Skills、Memory、Cron Jobs 进化历程

一个漂亮、响应式的可视化 HTML 仪表盘，每日自动采集 Hermes Agent 的能力数据，通过快照增量比对生成履历记录与可视化视图。

## ✨ 核心功能

| 功能 | 说明 |
|------|------|
| 📊 **仪表盘** | Skills / Memory / Cron Jobs 实时数量 + 累计进化次数 + 进化概览 |
| 🛠️ **Skills Tab** | 独立 Tab，自适应网格展示所有已掌握的 Skills，含智能主分类 Chip 与数量标记 |
| 🧠 **记忆 Tab** | 独立 Tab，按类型（`user` 偏好 / `memory` 笔记）分类筛选持久记忆 |
| 📚 **进化档案** | 时间轴浏览每次进化记录，含项目筛选、统计条与折叠详情 |
| 🔍 **Visual Side-by-Side Diff** | 内置纯前端 LCS 文本对比视图，支持 Side-by-Side / Unified 红绿增删高亮 |
| 🌐 **i18n 多语言** | 客户端中/英文实时无缝切换，刷新自动恢复选择 |
| 📦 **前后端解耦 API** | 标准 RESTful JSON API (`output/api/v1/`) + 零依赖静态网页输出 |
| 🚀 **一键脚本** | `./update.sh` 脚本一行命令完成增量更新与编译 |
| 🐳 **Docker 部署** | 开箱即用 Docker Compose 编排，支持每日凌晨 2 点定时增量采集 |

## 🚀 快速开始

### 本地运行

```bash
# 安装 Python 依赖
pip install -r requirements.txt

# 一键增量更新
./update.sh

# 常见 CLI 参数
./update.sh --baseline      # 首次建立基线（不产生 diff）
./update.sh --full-rebuild # 全量重写与 3 个月前记录压缩
./update.sh --project foo  # 指定显式项目名称
```

输出：`output/index.html`，可在任何浏览器中直接打开。

### Docker 容器部署

```bash
# 完整模式：每日凌晨 2 点自动定时更新 + Nginx Web 服务 (端口 57621)
docker compose --profile full up -d
```

部署成功后访问 `http://localhost:57621` 即可查看面板。

## 📁 项目结构

```
hermes-evolution/
├── update.sh                # 英文一键更新 Shell 脚本
├── generate.py              # CLI 命令主入口
├── i18n.py                  # 中英翻译字典
├── src/                     # 核心源码
│   ├── core/                # 采集器、Diff 引擎与导出器
│   └── web/                 # Vanilla JS ES 模块与前端 UI
├── output/                  # 静态输出目录与 JSON API 产物
├── Dockerfile               # Docker 镜像构建配置
└── docker-compose.yml       # Docker Compose 服务编排
```

## 🌐 贡献指南与开源协议

- **贡献指南**：欢迎阅读 [贡献指南](CONTRIBUTING_ZH.md) ([English Guide](CONTRIBUTING.md)) 参与项目建设。
- **开源协议**：本项目基于 [MIT 协议](LICENSE) 开源，Powered by **Nous Hermes Agent**。
