
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code
COPY day_06_docker.py .

# Expose port
EXPOSE 8000

# Run agent
CMD ["python", "day_06_docker.py"]
