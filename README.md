# 🧬 Hermes Evolution Log

[![中文](https://img.shields.io/badge/README-中文-red)](README_ZH.md)

> AI Evolution Observability & Dashboard — Track the growth of Hermes Agent's Skills, Memory, and Cron Jobs

A sleek, responsive visual HTML dashboard that automatically captures Hermes Agent capability data daily, performs snapshot diffing, and displays versioned evolution history.

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| 📊 **Dashboard** | Real-time counts of Skills, Memory, Cron Jobs & cumulative evolution metrics |
| 🛠️ **Skills Tab** | Responsive grid of all mastered skills with smart category chips and counts |
| 🧠 **Memory Tab** | Filterable persistent memories categorized by target (`user` / `memory`) |
| 📚 **Evolution Archive** | Interactive timeline with collapsible details and project filtering |
| 🔍 **Visual Side-by-Side Diff** | Built-in LCS Diff viewer to highlight exact text additions & removals |
| 🌐 **i18n Multi-language** | Client-side real-time English/Chinese switching, remembers user choice |
| 📦 **Decoupled REST API** | Standardized JSON API (`output/api/v1/`) + zero-dependency static build |
| 🚀 **One-Click Script** | Single `./update.sh` script to perform incremental updates & rebuilds |
| 🐳 **Docker Ready** | Production-ready Docker Compose setup with scheduled daily cron updates |

## 🚀 Quick Start

### Local Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Run one-click update
./update.sh

# Additional CLI Flags
./update.sh --baseline      # Establish baseline snapshot (no diff output)
./update.sh --full-rebuild # Perform full rebuild & compression
./update.sh --project foo  # Specify explicit project label
```

Output dashboard: `output/index.html` — open directly in any browser.

### Docker Deployment

```bash
# Full Mode: Auto-updates daily at 02:00 + Web Server (Port 57621)
docker compose --profile full up -d
```

Access the dashboard live at `http://localhost:57621`.

## 📁 Repository Structure

```
hermes-evolution/
├── update.sh                # One-click update shell script
├── generate.py              # CLI entry point
├── i18n.py                  # Core translation dictionary
├── src/                     # Core Python & Web modules
│   ├── core/                # Collector, Diff Engine & Exporter
│   └── web/                 # Vanilla JS ES Modules & Theme UI
├── output/                  # Output static dashboard & JSON APIs
├── Dockerfile               # Docker container definition
└── docker-compose.yml       # Docker Compose multi-service setup
```

## 🌐 License & Attribution

Powered by **Nous Hermes Agent**. Released under the MIT License.
