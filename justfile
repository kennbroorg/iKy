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

# Start all services in background
up:
    docker compose up -d

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

# Full rebuild: stop, build, start
rebuild:
    docker compose down
    docker compose build
    docker compose up -d

# Remove containers, volumes, and locally-built images
clean:
    docker compose down -v --rmi local
