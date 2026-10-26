FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 CONTENT_DIR=/content
WORKDIR /app
COPY apps/api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && useradd --uid 10001 --create-home academy
COPY apps/api/app ./app
COPY apps/api/alembic ./alembic
COPY apps/api/alembic.ini .
COPY content /content
USER 10001
EXPOSE 8000
# X-Forwarded-For is honoured only from FORWARDED_ALLOW_IPS (uvicorn's default: 127.0.0.1). The
# server sets it to the web container's fixed address (docker-compose.server.yml).
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
