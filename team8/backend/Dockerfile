# team8/backend/Dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# System deps (psycopg binary still needs build tools for some platforms)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip \
 && pip install -r /app/requirements.txt

COPY . /app

EXPOSE 8002

# Run migrations and collectstatic before starting gunicorn
CMD ["/bin/sh", "-c", "set -e; python manage.py migrate --noinput; python manage.py collectstatic --noinput || true; exec gunicorn config.wsgi:application --bind 0.0.0.0:8002 --workers 3 --timeout 120"]
