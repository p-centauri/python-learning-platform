FROM python:3.13-slim
WORKDIR /app
COPY . .
# Deliberate release faults: root user and loopback server inside container.
CMD ["python", "server.py"]
