# 🧬 Hermes Evolution Log

[![EN](https://img.shields.io/badge/README-EN-blue)](README_EN.md)

> AI 进化可视化 — 追踪 Hermes Agent 的 Skills、Memory、Cron Jobs 进化历程

一个漂亮的可视化 HTML 仪表盘，每日自动采集 Hermes Agent 的能力数据，通过快照对比生成进化记录。

## ✨ 功能

| 功能 | 说明 |
|------|------|
| 📊 **仪表盘** | Skills / Memory / Cron Jobs 数量 + 累计进化次数 + 进化概览 |
| 🛠️ **Skills Tab** | 独立 Tab，自适应网格展示所有已掌握的 Skills，含分类标签和描述 |
| 🧠 **记忆 Tab** | 独立 Tab，按类型（user/memory）分类展示持久记忆 |
| 📚 **进化档案** | 卡片式浏览每次进化记录，含统计条、自动标签、项目归属、折叠详情 |
| 🔍 **全局搜索** | 实时筛选 Skills / Memory / Archive，按名称、描述、内容、项目名搜索 |
| 🌐 **客户端语言切换** | 页面按钮实时中/英切换，刷新后记住选择 |
| 📦 **项目归属** | `--project` 自动检测 git remote，档案支持按项目筛选 |
| 🔄 **基线策略** | 首次快照不产生变更记录，避免全量误报 |
| 🗜️ **定期压缩** | 3 个月前的记录自动只保留摘要，控制页面体积 |
| ⚠️ **容错补偿** | 快照间隔超过 1 天时标注"合并变更"警告 |

## 🚀 快速开始

### 本地运行

```bash
# 安装依赖
pip install -r requirements.txt

# 首次运行（创建基线快照，不产生变更记录）
python generate.py --baseline

# 每日增量更新（自动检测项目名）
python generate.py

# 指定项目名
python generate.py --project my-project

# 全量重写（压缩 3 个月前记录）
python generate.py --full-rebuild

# 英文输出
python generate.py --lang en
```

输出：`output/index.html`，直接用浏览器打开即可。

### Docker

```bash
# 完整模式：定时更新 + Web 服务
docker compose --profile full up -d
# 每天凌晨 2 点自动更新，周日凌晨 3 点全量重写
# 默认端口 57621，通过 PORT 环境变量修改
```

## 📁 项目结构

```
hermes-evolution/
├── generate.py              # 核心脚本：采集 + diff + 渲染
├── i18n.py                  # 中英翻译字典
├── Dockerfile               # Docker 镜像
├── docker-compose.yml       # 多服务编排
├── requirements.txt         # Python 依赖
├── output/                  # 输出目录
│   ├── index.html           # 生成的进化日志页面
│   ├── timeline.json        # 时间线数据（持久化）
│   └── snapshots/           # 每日快照（JSON 时间戳命名）
└── README.md
```

## 🎨 设计

- **暗色主题** — 深色渐变背景，紫蓝色调
- **4 Tab 布局** — 仪表盘 / Skills / 记忆 / 档案
- **响应式** — 桌面 4 列统计 → 平板 2 列 → 手机 1 列
- **动画效果** — 头像脉冲光晕、卡片悬停上浮
- **档案卡片** — 项目标签、统计条、自动关键词标签、折叠详情

## 🌐 多语言 (i18n)

支持中文 (zh) 和英语 (en)：

```bash
python generate.py --lang en           # CLI 参数
EVOLUTION_LANG=en python generate.py   # 环境变量
```

页面内置语言切换按钮，刷新后自动恢复选择。

## 🔧 配置

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--hermes-home` | `~/AppData/Local/hermes` | Hermes 数据目录 |
| `--lang` | `zh` | 输出语言 (zh / en) |
| `--project` | 自动检测 git remote | 项目名，用于档案分组 |
| `EVOLUTION_LANG` | `zh` | 环境变量方式设置语言 |
| `PORT` | `57621` | Docker Web 服务端口 |

## 📄 License

MIT
