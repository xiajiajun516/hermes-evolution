# 贡献指南 (Contributing to Hermes Evolution Log)

[![English](https://img.shields.io/badge/CONTRIBUTING-English-blue)](CONTRIBUTING.md)

感谢你对 **Hermes Evolution Log** 项目的关注与贡献！我们非常欢迎 Issue 报告、功能建议、UI/UX 改进以及 代码 Pull Request。

---

## 🛠️ 本地开发环境准备

1. **克隆仓库与安装依赖**：
   ```bash
   git clone https://github.com/xiajiajun516/hermes-evolution.git
   cd hermes-evolution
   pip install -r requirements.txt
   ```

2. **本地生成与测试运行**：
   ```bash
   ./update.sh
   # 或直接运行 Python 入口
   python generate.py
   ```

3. **运行单元测试套件**：
   ```bash
   python -m unittest discover tests
   ```

---

## 📐 代码架构说明

- `generate.py`：CLI 入口控制。
- `src/core/`：Python 模块（数据采集器、Diff 引擎、JSON 导出器）。
- `src/web/`：前端模块（原生 Vanilla JS ES 模块、CSS3 变量主题、视图渲染组件）。
- `tests/`：自动化测试覆盖集。

---

## 📋 Pull Request 提交规范

1. Fork 仓库并基于开发分支新建分支 (`git checkout -b feat/my-awesome-feature`)。
2. 保持代码模块化与符合现有风格习惯。
3. 确保本地单元测试全部通过 (`python -m unittest discover tests`)。
4. 提交规范的 Commit 消息 (`git commit -m "feat: 描述变更"`).
5. 发起 GitHub Pull Request。

---

再次感谢你为 Hermes Agent 进化可视化生态做出的贡献！🧬
