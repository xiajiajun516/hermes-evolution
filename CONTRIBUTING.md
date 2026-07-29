# Contributing to Hermes Evolution Log

[![中文](https://img.shields.io/badge/CONTRIBUTING-中文-red)](CONTRIBUTING_ZH.md)

Thank you for your interest in contributing to **Hermes Evolution Log**! We welcome bug reports, feature suggestions, UI enhancements, and code contributions.

---

## 🛠️ Development Setup

1. **Clone Repository & Install Dependencies**:
   ```bash
   git clone https://github.com/xiajiajun516/hermes-evolution.git
   cd hermes-evolution
   pip install -r requirements.txt
   ```

2. **Run Generator Locally**:
   ```bash
   ./update.sh
   # Or directly
   python generate.py
   ```

3. **Run Unit Tests**:
   ```bash
   python -m unittest discover tests
   ```

---

## 📐 Project Architecture

- `generate.py`: Main CLI entry point.
- `src/core/`: Python modules for data collection, diff calculations, and JSON exporter.
- `src/web/`: Vanilla JS ES Modules, CSS Variables dark theme, and component view renderers.
- `tests/`: Automated unit tests covering collectors, exporters, UI, and docs.

---

## 📋 Pull Request Workflow

1. Fork the repository and create a feature branch (`git checkout -b feat/my-awesome-feature`).
2. Implement your changes keeping code clean and modular.
3. Ensure all tests pass (`python -m unittest discover tests`).
4. Commit your changes with clear commit messages (`git commit -m "feat: description"`).
5. Open a Pull Request on GitHub.

---

Thank you for helping build better observability for Hermes Agent! 🧬
