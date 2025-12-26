---
title: "Day 23: Docker Consolidation - Everything in One System"
date: 2025-12-23
tags:
  - python
  - aoc
  - adventofcode
  - docker
  - microservices
  - production
toc: true
---

All documents for this post can be found in my [repository](https://github.com/gvtsch/aoc_2025_heist/tree/main/day_23).

We've been developing for 22 days now, exploring various concepts and programming in Python. Well... someone else programmed the dashboard for us.
And today it's about making the system production-ready with Docker and starting it with just a single command.

## Goal

Instead of manually starting 6 different services (OAuth, Calculator, File Reader, Database Query, Memory, and Dashboard), I want to make this whole thing "production-ready." I just want to run `docker-compose up`.

That sounds like "just deployment" at first, but it's much more. I found and fixed a whole bunch of bugs, synchronized the services, and made the system really stable. That took a lot longer than I expected.

But the effort was worth it. Now I have a system that's something like "production-ready." Let's take a look at how it's all built.

## Docker Setup

I chose Docker Compose because it's perfect for multi-container setups. Each service runs isolated in its own container, but they can all communicate with each other. We already had this on Day 6.

### The Structure

Each service has its own Dockerfile and runs isolated. They communicate with each other over a Docker network.

```
docker-compose.yml          # Orchestrates all 6 Services
├── oauth (Port 8001)       # JWT Token Service
├── calculator (8002)       # Math Operations
├── file-reader (8003)      # Document Access
├── database-query (8004)   # Security DB
├── memory (8005)           # Context Compression
└── dashboard (8008)        # Main Application + AI Detection
```

### `docker-compose.yml`

This file is the heart of the system. Here's an excerpt:

```yaml
version: '3.8'

services:
  oauth:
    build:
      context: .
      dockerfile: day_08/Dockerfile
    container_name: heist-oauth
    ports:
      - "8001:8001"
    networks:
      - heist-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 10s
      timeout: 5s
      retries: 3

  dashboard:
    build:
      context: .
      dockerfile: day_22/Dockerfile
    container_name: heist-dashboard
    ports:
      - "8008:8008"
    environment:
      - DATABASE_PATH=/data/heist_analytics.db
      - LM_STUDIO_URL=http://host.docker.internal:1234/v1
    volumes:
      - heist-data:/data
    depends_on:
      oauth:
        condition: service_healthy
      calculator:
        condition: service_healthy
      # ... all other services
    networks:
      - heist-network

volumes:
  heist-data:
    driver: local

networks:
  heist-network:
    driver: bridge
```

I stumbled over one obstacle or another...

The `depends_on` with `condition: service_healthy` helped me the most. Without it, the dashboard container starts immediately, even if the other services aren't ready yet. With the health check, Docker really waits until all tools are running and reachable. That saved me a lot of problems with race conditions.

With `host.docker.internal` I was confused at first. LM Studio doesn't run in a container, but directly on my machine (port 1234). But containers can't just access `localhost` of the host. With `host.docker.internal` it works - Docker automatically resolves it to the correct host IP. But we already know that from Day 6.

I need the `volumes` for persistence. The SQLite database with all session data is located at `/data/heist_analytics.db` in the container. Without a volume, the data would be gone every time the container restarts. With the volume `heist-data:/data`, all heist statistics are preserved - even across restarts and rebuilds.

## The Dockerfiles

Each service needs its own Dockerfile. Here's an example for the Calculator:

```dockerfile
# day_13/Dockerfile.calculator
FROM python:3.11-slim

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY day_13/tool_service.py .

ENV PYTHONUNBUFFERED=1
ENV PORT=8002

EXPOSE 8002

HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
  CMD curl -f http://localhost:8002/health || exit 1

CMD ["python", "tool_service.py"]
```

The health check is crucial. Without it, the dashboard container would start too early and get connection errors. And I got quite a few errors over time ;)

## Bugs During Dockerization

During the assembly, I noticed quite a few bugs that didn't show up locally. Docker forces you to be very precise, which is good! Here's a summary of the most important problems:

* **Endpoint Paths:** Config and services had different paths (`/tools/read_file` vs. `/tools/file_reader`). Result: 404 errors.
* **Duplicate Messages:** Every message was written to the DB twice - by the agent and by the dashboard. The message counter therefore always counted double.
* **Session Completion:** Sessions were never marked as 'completed'. The completion rate stayed at 0%, no matter how many heists I ran through.
* **Tool Usage Detection:** The original logic "error = suspicious" was unfair. Random 404s made innocent agents suspicious. I reversed it: Perfect success rates (95%+) are now suspicious because the mole is too careful. But there's still plenty of room for improvement here.
* **Database Schema:** Column names didn't match (`num_turns` vs. `total_turns`), JWT secrets were different, token fields inconsistent. Typical integration problems.

You can find the complete fixes in the repository. Every bug was a good lesson in service integration and made the system significantly more robust.

## Starting & Using

And how do you start the whole thing?

Actually quite simple: First open LM Studio, load a model (ideally the model specified in the config) and start the server on port 1234. Then run `docker-compose up --build` in the terminal. The first time, Docker builds all containers, which takes a few minutes. Then open a browser to `http://localhost:8008` and you're good to go.

Click "Start New Heist" in the dashboard, and the 6 agents start planning. You see in real-time how they communicate, which tools they use, and the AI analyzes every message in the background. At the end, you can guess who the mole is.

The AI gives me hints. Too perfect tool usage (95%+ success rate) is suspicious, contradictory timing statements, or hesitant language. But the final decision lies with the user. But there's still a lot to improve here too. The logic isn't quite mature yet.

If something doesn't work: Usually it's because LM Studio isn't running or the containers aren't fully booted yet. With `docker-compose logs dashboard` I can see what's going on.

## What I Learned

The Docker integration was more educational than expected. Sure, technically it's "just" writing a few Dockerfiles and putting together a Compose file. But in reality, Docker forced me to think about things that just worked in local development.

* **Health checks are not optional.** I initially thought `depends_on` would be enough. Service A starts after Service B, done. Well... "Started" doesn't mean "ready". The dashboard container immediately tried to reach the calculator while it was still booting. With `condition: service_healthy`, Docker really waits until the service responds.
* **Service discovery was confusing.** In my local setup, everything was `localhost:800X`. In Docker, each container is its own little system. `localhost` points into the container itself, not to the other services. The solution is simple: use service names (`http://calculator:8002`). Docker resolves it internally. But it took a while to understand that.
* **Volumes are mandatory for persistent data.** The SQLite database was initially directly in the container. If the container is restarted, all heist data is gone. With the volume `heist-data:/data`, the data is preserved. Sounds trivial, but I forgot it on the first try and wondered why my test sessions were disappearing.
* **Docker shows integration problems mercilessly.** Locally, I started the services manually, in any order. If something didn't work, I restarted. In Docker, everything must be cleanly orchestrated. Order, dependencies, and configs. That showed me some bugs: For example, endpoint mismatch, duplicate message storage, and missing session completion. All things that somehow worked in my chaotic local setup but were actually broken.
* **Debugging is different.** No simple print statement that I see in the terminal anymore. I had to learn to work with `docker-compose logs -f`, jump into containers (`docker exec -it`), check the database directly in the container. Frustrating at first, but actually much more systematic than my local chaos.
* **Centralized auth is genius.** Every tool service uses the same OAuth service. No service does auth itself. That means: change the JWT secret in only one place, manage scopes centrally, and implement token logic correctly once.

## Conclusion

Day 23 turned a development setup into a "production-ready" system. As far as you can even say that for our constructed project.

* **One command**: `docker-compose up` and everything runs
* **6 Microservices**: All isolated and healthy
* **OAuth Security**: Token-based authentication
* **Persistence**: Database survives restarts
* **6 Agents**: More complex heist scenarios
* **AI Detection**: RAG-based mole detection
* **Observability**: Logs, health checks, metrics

I found and fixed quite a few bugs during dockerization that were hidden before. That, and everything else I learned along the way, was almost more valuable than the Docker setup itself!
