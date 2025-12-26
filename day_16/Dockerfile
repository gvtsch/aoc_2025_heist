# Memory Service
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy memory service code
COPY day_16/memory_service.py .

ENV PYTHONUNBUFFERED=1
ENV PORT=8005

EXPOSE 8005

HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
  CMD curl -f http://localhost:8005/health || exit 1

CMD ["python", "memory_service.py"]
