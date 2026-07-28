FROM python:3.11-slim

LABEL org.opencontainers.image.title="Hermes Evolution Log"
LABEL org.opencontainers.image.description="AI 进化可视化 — 追踪 Hermes Agent 的 Skills、Memory、Cron Jobs 进化历程"
LABEL org.opencontainers.image.source="https://github.com/xiajiajun516/hermes-evolution"

WORKDIR /app

# 安装依赖和 cron
RUN apt-get update && apt-get install -y --no-install-recommends cron && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制脚本
COPY generate.py .
COPY i18n.py .

# 输出目录（挂载点）
RUN mkdir -p /app/output/snapshots

# 默认命令：每天运行一次
# 用法：
#   docker run --rm -v ~/AppData/Local/hermes:/hermes:ro -v ./output:/app/output hermes-evolution
CMD ["sh", "-c", "python generate.py --hermes-home /hermes --output-dir /app/output"]
