FROM python:3.12-slim-bookworm

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

# Install Playwright browsers (required by TikTokApi)
RUN playwright install --with-deps chromium

# Copy backend code
COPY ./backend .

# Configure Redis URLs for Docker (read by celery_app.py at runtime)
ENV CELERY_BROKER_URL="redis://redis:6379/0"
ENV CELERY_RESULT_BACKEND="redis://redis:6379/0"

# Initialize apikeys.json if it doesn't exist
RUN cp -n factories/apikeys_default.json factories/apikeys.json 2>/dev/null || true

# Supervisor configuration
COPY install/docker/backend/supervisor.conf /etc/supervisor.conf

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/tasklist')" || exit 1

CMD ["supervisord", "-c", "/etc/supervisor.conf"]
