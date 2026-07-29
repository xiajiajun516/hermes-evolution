# 🧬 Hermes Evolution Log

> AI Evolution Visualization — Track the growth of Hermes Agent's Skills, Memory, and Cron Jobs

A beautiful visual HTML dashboard that automatically collects Hermes Agent capability data daily and generates evolution records through snapshot diffing.

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📊 **Dashboard** | Skills / Memory / Cron Jobs counts + cumulative evolution stats |
| 🛠️ **Skills Tab** | Standalone tab with responsive grid of all mastered Skills, categories & tags |
| 🧠 **Memory Tab** | Standalone tab showing persistent memories by type (user/memory) |
| 📚 **Evolution Archive** | Card-based evolution records with stats bar, auto-tags, project labels, expandable details |
| 🔍 **Global Search** | Real-time filtering across Skills / Memory / Archive by name, description, content, project |
| 🌐 **Client-side Lang Switch** | Instant zh/en toggle button, persists across refreshes |
| 📦 **Project Tracking** | `--project` auto-detects git remote, archive filterable by project |
| 🔄 **Baseline Strategy** | First snapshot creates no change records, avoiding false positives |
| 🗜️ **Periodic Pruning** | Records older than 3 months keep only summaries to control page size |
| ⚠️ **Gap Compensation** | Interval > 1 day between snapshots triggers "merged changes" warning |

## 🚀 Quick Start

### Local

```bash
# Install dependencies
pip install -r requirements.txt

# First run (create baseline, no change records)
python generate.py --baseline

# Daily incremental update (auto-detects project name)
python generate.py

# Specify project name
python generate.py --project my-project

# English output
python generate.py --lang en

# Full rebuild (prune old records)
python generate.py --full-rebuild
```

Output: `output/index.html` — open directly in any browser.

### Docker

```bash
# Full mode: scheduled updates + web server
docker compose --profile full up -d
# Auto-updates daily at 02:00, full rebuild Sundays at 03:00
# Default port 57621, configurable via PORT env var
```

## 📁 Project Structure

```
hermes-evolution/
├── generate.py              # Core script: collection + diff + rendering
├── i18n.py                  # zh/en translation dictionary
├── Dockerfile               # Docker image
├── docker-compose.yml       # Multi-service orchestration
├── requirements.txt         # Python dependencies
├── output/                  # Output directory
│   ├── index.html           # Generated evolution log page
│   ├── timeline.json        # Timeline data (persistent)
│   └── snapshots/           # Daily snapshots (timestamped JSON)
└── README.md
```

## 🎨 Design

- **Dark theme** — Deep gradient background, purple-blue palette
- **4-Tab layout** — Dashboard / Skills / Memory / Archive
- **Responsive** — 4-column stats → 2 on tablet → 1 on mobile
- **Animations** — Pulsing avatar glow, card hover lift
- **Archive cards** — Project badge, stats bar, auto keyword tags, expandable details

## 🌐 i18n

Chinese (zh) and English (en) supported:

```bash
python generate.py --lang en           # CLI flag
EVOLUTION_LANG=en python generate.py   # Environment variable
```

Page includes an in-app language toggle button that persists across refreshes.

## 🔧 Configuration

| Option | Default | Description |
|--------|---------|-------------|
| `--hermes-home` | `~/AppData/Local/hermes` | Hermes data directory |
| `--lang` | `zh` | Output language (zh / en) |
| `--project` | auto-detect from git remote | Project name for archive grouping |
| `EVOLUTION_LANG` | `zh` | Language via environment variable |
| `PORT` | `57621` | Docker web server port |

## 📄 License

MIT
