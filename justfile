# iKy task runner
# Install just: https://github.com/casey/just#installation

# List available recipes
default:
    @just --list

# Create venv and install dev tooling (pre-commit, ruff)
setup:
    python3 -m venv .venv
    .venv/bin/pip install --upgrade pip
    .venv/bin/pip install pre-commit ruff==0.9.7
    .venv/bin/pre-commit install
    @echo "Done. Activate with: source .venv/bin/activate"

# Build Docker images
build:
    docker compose build

# Start all services (auto-detects host Redis)
up:
    #!/usr/bin/env bash
    if command -v redis-cli &>/dev/null && redis-cli -h 127.0.0.1 -p 6379 ping 2>/dev/null | grep -q PONG; then
        echo "▶ Host Redis detected on 127.0.0.1:6379 — skipping Redis container"
        export CELERY_BROKER_URL=redis://host.docker.internal:6379/0
        export CELERY_RESULT_BACKEND=redis://host.docker.internal:6379/0
        export REDIS_HOST=host.docker.internal
        docker compose up -d frontend backend
    else
        echo "▶ No host Redis found — starting all services including Redis container"
        docker compose up -d
    fi

# Stop all services
down:
    docker compose down

# Follow logs for a service (default: backend)
logs service="backend":
    docker compose logs -f {{ service }}

# Show running containers
ps:
    docker compose ps

# Open a shell in the backend container
shell-backend:
    docker compose exec backend bash

# Open a shell in the frontend container
shell-frontend:
    docker compose exec frontend sh

# Run linter checks (no auto-fix)
lint:
    .venv/bin/ruff check .
    .venv/bin/ruff format --check .

# Auto-format Python code
fmt:
    .venv/bin/ruff format .
    .venv/bin/ruff check --fix .

# Run backend tests inside the container
test *args:
    docker compose exec backend pytest -v {{ args }}

# Restart a service
restart service:
    docker compose restart {{ service }}

# Full rebuild: stop, build, start (auto-detects host Redis)
rebuild:
    #!/usr/bin/env bash
    docker compose down
    docker compose build
    if command -v redis-cli &>/dev/null && redis-cli -h 127.0.0.1 -p 6379 ping 2>/dev/null | grep -q PONG; then
        echo "▶ Host Redis detected — skipping Redis container"
        export CELERY_BROKER_URL=redis://host.docker.internal:6379/0
        export CELERY_RESULT_BACKEND=redis://host.docker.internal:6379/0
        export REDIS_HOST=host.docker.internal
        docker compose up -d frontend backend
    else
        echo "▶ No host Redis — starting all services"
        docker compose up -d
    fi

# Remove containers, volumes, and locally-built images
clean:
    docker compose down -v --rmi local
