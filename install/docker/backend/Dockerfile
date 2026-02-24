FROM python:3.9-slim-bookworm

WORKDIR /app

# Install system dependencies in a single layer
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        supervisor \
        git && \
    mkdir -p /var/log/supervisor /etc/supervisor/conf.d && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY ./backend .

# Configure Redis URLs for Docker
RUN sed -i "s/CELERY_BROKER_URL.*/CELERY_BROKER_URL = 'redis:\/\/redis:6379\/0'/g" /app/factories/configuration.py && \
    sed -i "s/CELERY_RESULT_BACKEND.*/CELERY_RESULT_BACKEND = 'redis:\/\/redis:6379\/0'/g" /app/factories/configuration.py && \
    sed -i "s/redis:\/\/localhost/redis:\/\/redis/g" /app/factories/celery_config.py

# Supervisor configuration
COPY install/docker/backend/supervisor.conf /etc/supervisor.conf

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/tasklist')" || exit 1

CMD ["supervisord", "-c", "/etc/supervisor.conf"]
