# OAuth Authentication Service
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

# Copy OAuth service code (Docker version)
COPY day_08/day_08_oauth_docker.py ./day_08_oauth.py

# Create data directory
RUN mkdir -p /data

ENV PYTHONUNBUFFERED=1
ENV PORT=8001
ENV DATABASE_PATH=/data/heist_audit.db

EXPOSE 8001

HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
  CMD curl -f http://localhost:8001/health || exit 1

CMD ["python", "day_08_oauth.py"]
