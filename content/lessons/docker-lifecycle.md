## A running process may not be ready
Container started means the runtime launched a process. It does not prove the database is reachable, migrations are compatible or requests can succeed. A liveness check asks whether the process should be restarted. A readiness check asks whether it should receive traffic. Restarting every instance when a shared database is unavailable can worsen recovery.

Use a small, reproducible image with explicit dependencies and a non-root application user. Keep secrets out of image layers and Git. Docker environment variables are configuration, not a secret vault; production credentials require controlled injection and rotation.

```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
USER 10001
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```
The exec-form command makes the application the container's main process and allows shutdown signals to reach it directly. Account for writable directories and ownership when using a non-root user.

## Graceful shutdown is a budget
On termination, stop taking new work, allow in-flight operations to finish within a bounded grace period, and leave unfinished queue jobs recoverable. An orchestrator can still force-kill after the grace period. Transactions and idempotency must remain correct under that abrupt ending. Do not depend on a shutdown hook as the only place essential state is persisted.

## Schema evolution spans versions
During a rolling deployment, old and new application versions may run simultaneously. Use expand-and-contract changes: add a compatible column, deploy code that supports both shapes, backfill and only later remove the old shape. Running destructive migrations concurrently from every replica is unsafe. Give migrations a single controlled deployment step.

## Incident checkpoint
A container responds locally but is unreachable from another service. Verify bind address, container DNS name and container port before changing a host port mapping. A process bound to 127.0.0.1 inside its container is not reachable through the container network. For mastery, explain network boundaries, signal behavior and migration compatibility with a concrete rollback plan.
