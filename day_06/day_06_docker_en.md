Today I'm venturing back into familiar waters... more or less. 
It's all about Docker. That's the "more" part, FastAPI is the "less".

Docker makes it super easy to isolate services, and projects can be deployed or rebuilt on different operating systems or environments without a hitch.

Today we're starting with a single container. But you can orchestrate many containers too – we'll get to that next week. For now, we're hosting a small FastAPI service.

By the way... You need a so-called docker-compose.yml and a Dockerfile.
In the yml file, you define which container services should be started and managed together, and with which settings.

```yml
version: '3.8'

services:
  agent-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - LLM_BASE_URL=http://host.docker.internal:1234/v1
      - LLM_MODEL=google/gemma-3n-e4b
    volumes:
      - ./data:/app/data
```

In this docker-compose.yml, a service called "agent-api" is defined, which is built from the local Dockerfile, exposes port 8000, sets two environment variables for the LLM, and mounts the local ./data directory into /app/data inside the container.
The two environment variables LLM_BASE_URL and LLM_MODEL tell the container to access the service running on the host machine at port 1234. That's our locally hosted LLM in LM-Studio! And now it's clear what LLM_MODEL is for ;)

In the Dockerfile, you define how a single container image is built – the base, installed software, configurations, and the start command for exactly one container.

```Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code
COPY day_05_fastapi.py .

# Expose port
EXPOSE 8000

# Run agent
CMD ["python", "day_05_fastapi.py"]
```

Our Dockerfile makes sure a Python image (3.11-slim) is used as the base. Then it sets the working directory, installs the packages from requirements.txt, copies the Python script, exposes port 8000, and finally runs that script when the container starts.

Once you've set up the basics – all files exist and work – you can start everything by running docker-compose up in the terminal. Important: Docker must be running beforehand! In the background, the container is built and everything described above is executed.
In this case, a FastAPI app is started, which you can open in your browser. That lets you communicate with the locally hosted LLM.

Now we can call several different URLs.
For example, http://localhost:8000/: But this URL leads nowhere if you haven't defined anything for the root route.
Different story for http://localhost:8000/docs. This URL takes you to FastAPI's automatically generated documentation.
http://localhost:8000/health leads to a health status, as long as the endpoint is defined in the code.
You can also use the documentation to get to the chat area and test communication with LM-Studio. Or you can use the command line.

```bash 
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, how are you?"}'
```

This call gives you an output like:

```Bash
{"response":"Hello! I'm doing well, thank you for asking! 😊\n\nIt's nice to be able to communicate in English. How can I help you today?\n","container_id":"186177f2a75e"}% 
```

And so on and so forth. You can really take your time to play around with it.

## Summary
So now we've got a service running in a Docker container – and we can even chat with it. That brings some real advantages:

- Whether it's Windows, Mac, or Linux – it runs the same everywhere. No more "works on my machine, not on yours" nonsense.
- Everything the app needs is inside the container. No dependency hell, no version conflicts.
- Want to run it somewhere else? Just start the container. Reproducible and stress-free.
- Multiple instances? No problem – scale up as much as you like.
- And: The interfaces are clear – HTTP in, response out. Clean and tidy.

So we've set up the Docker base camp. Next week, we'll get into the real stuff: multiple containers working together. That's going to be exciting!
