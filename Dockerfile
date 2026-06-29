FROM python:3.11-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY src ./src

RUN pip install --no-cache-dir .

# Default command overridden by docker-compose (API or Celery worker).
CMD ["uvicorn", "vera.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
