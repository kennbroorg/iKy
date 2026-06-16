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

# Ensure backend/factories/apikeys.json exists (prevents Docker creating a directory)
init-apikeys:
    @cp -n backend/factories/apikeys_default.json backend/factories/apikeys.json 2>/dev/null || true

# Build Docker images
build: init-apikeys
    docker compose build

# Start all services (excludes the legacy `frontend`; use `docker compose up frontend` if needed)
up: init-apikeys
    docker compose up -d backend iky-frontend redis

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

# Open a shell in the new-frontend container
shell-new-frontend:
    docker compose exec new-frontend sh

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

# Full rebuild: stop, build, start (excludes the legacy `frontend`)
rebuild: init-apikeys
    docker compose down
    docker compose build
    docker compose up -d backend iky-frontend redis

# Remove containers, volumes, and locally-built images
clean:
    docker compose down -v --rmi local

# Install the host-side browser cookie extraction dependency into the venv
cookies-setup:
    .venv/bin/pip install browser-cookie3==0.20.1

# Import a browser-exported cookie file into the persistent cookie volume.
# Usage: just cookies-import linkedin ~/linkedin_export.json
cookies-import module file:
    @test -f "{{ file }}" || { echo "iKy - source file not found: {{ file }}" >&2; exit 1; }
    @mkdir -p backend/cookies
    @cp "{{ file }}" "backend/cookies/{{ module }}_cookies.json"
    @echo "iKy - imported cookies -> backend/cookies/{{ module }}_cookies.json"

# Grab cookies from local browsers into the persistent cookie volume.
# Tries all browsers unless one is named. Close the target browser first
# (a running browser locks its cookie database).
# Usage: just cookies-grab linkedin linkedin.com [firefox]
cookies-grab module domain browser="": cookies-setup
    #!/usr/bin/env sh
    set -e
    extra=""
    [ -n "{{ browser }}" ] && extra="--browser {{ browser }}"
    .venv/bin/python install/scripts/grab_cookies.py \
        --module {{ module }} --domain {{ domain }} \
        --out "backend/cookies/{{ module }}_cookies.json" $extra
