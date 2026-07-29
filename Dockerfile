FROM python:3.11-slim

LABEL org.opencontainers.image.title="Hermes Evolution Log"
LABEL org.opencontainers.image.description="AI 进化可视化 — 追踪 Hermes Agent 的 Skills、Memory、Cron Jobs 进化历程"
LABEL org.opencontainers.image.source="https://github.com/xiajiajun516/hermes-evolution"

WORKDIR /app

# 安装依赖和 cron
RUN apt-get update && apt-get install -y --no-install-recommends cron && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制核心脚本与源码目录
# 包含 src/web/ 目录下的静态网页资源（HTML/CSS/JS），供 Web 托管模式使用
COPY generate.py i18n.py ./
COPY src/ ./src/

# 输出目录（挂载点）
RUN mkdir -p /app/output/snapshots

# 默认命令：从容器生成进化快照
CMD ["python", "generate.py", "--hermes-home", "/hermes", "--output-dir", "/app/output"]
