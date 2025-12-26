# Detection Dashboard Service
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy necessary code files (Docker versions)
COPY day_22/detection_dashboard_server_docker.py ./detection_dashboard_server.py
COPY day_22/detection_dashboard_docker.html ./detection_dashboard_docker.html
COPY day_22/sabotage_detector_docker.py ./day_22/sabotage_detector_docker.py
COPY day_20/session_analytics.py ./day_20/
COPY day_20/heist_controller.py ./day_20/
COPY day_20/integrated_agent_with_controller.py ./day_20/
COPY day_20/agents_config.docker.yaml ./day_20/agents_config.yaml
COPY day_16/integrated_system.py ./day_16/integrated_system.py
COPY init_database.py .

# Create necessary directories
RUN mkdir -p /data day_20 day_22 day_16

ENV PYTHONUNBUFFERED=1
ENV PORT=8008
ENV DATABASE_PATH=/data/heist_analytics.db
ENV ANALYTICS_DB_PATH=/data/heist_analytics.db

EXPOSE 8008

HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
  CMD curl -f http://localhost:8008/health || exit 1

# Initialize database and start server
CMD python init_database.py && python detection_dashboard_server.py
