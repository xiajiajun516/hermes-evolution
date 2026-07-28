# 🧬 Hermes Evolution Log

> AI 进化可视化 — 追踪 Hermes Agent 的 Skills、Memory、Cron Jobs 进化历程

一个漂亮的可视化 HTML 仪表盘，每日自动采集 Hermes Agent 的能力数据，通过快照对比生成进化时间线。

## ✨ 功能

| 功能 | 说明 |
|------|------|
| 📊 **统计面板** | 实时展示 Skills / Memory / Cron Jobs 数量 + 累计进化次数 |
| 🛠️ **技能卡片** | 自适应网格展示所有已掌握的 Skills，含分类标签和描述 |
| 🧠 **记忆卡片** | 按类型（user/memory）分类展示持久记忆 |
| 📅 **进化时间线** | 每日增量追加变更记录，支持折叠展开详情 |
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

# 每日增量更新
python generate.py

# 全量重写（压缩 3 个月前记录）
python generate.py --full-rebuild

# 指定 Hermes 数据目录
python generate.py --hermes-home ~/AppData/Local/hermes --output-dir ./public
```

输出：`output/index.html`，直接用浏览器打开即可。

### Docker

```bash
# 构建镜像
docker compose build

# 首次：创建基线快照
docker compose run --rm evolution python generate.py --baseline

# 手动更新
docker compose run --rm evolution python generate.py

# 托管 HTML（带 nginx）
docker compose --profile serve up -d web
# 访问 http://localhost:8080

# 完整模式：定时更新 + Web 服务
docker compose --profile full up -d
# 每天凌晨 2 点自动更新
# 每周日凌晨 3 点全量重写
# 访问 http://localhost:8080
```

### 定时自动更新（Cron）

在 Docker 中已内置 cron（`--profile full`）。也可以手动设置：

```bash
# 每天凌晨 2 点运行
crontab -e
# 添加：
0 2 * * * cd /path/to/hermes-evolution && python generate.py
# 每周日凌晨 3 点全量重写
0 3 * * 0 cd /path/to/hermes-evolution && python generate.py --full-rebuild
```

## 📁 项目结构

```
hermes-evolution/
├── generate.py              # 核心脚本：采集 + diff + 渲染
├── Dockerfile               # Docker 镜像
├── docker-compose.yml       # 多服务编排
├── requirements.txt         # Python 依赖
├── output/                  # 输出目录
│   ├── index.html           # 生成的进化日志页面
│   ├── timeline.json        # 时间线数据（持久化）
│   └── snapshots/           # 每日快照（JSON）
│       └── YYYY-MM-DD.json
└── README.md
```

## 🎨 设计

- **暗色主题** — 深色渐变背景，紫蓝色调
- **响应式** — 桌面 4 列统计 → 平板 2 列 → 手机 1 列
- **动画效果** — 头像脉冲光晕、卡片悬停上浮、顶部渐变线展开
- **折叠详情** — 时间线条目支持展开查看具体变更项

## 🔧 配置

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| `HERMES_HOME` | `~/AppData/Local/hermes` | Hermes 数据目录 |

## 📄 License

MIT
