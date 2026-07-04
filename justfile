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

# Import a browser-exported cookie file into the persistent cookie volume
# AND mirror it into apikeys.json so the frontend reflects it.
# Usage: just cookies-import linkedin ~/linkedin_export.json
cookies-import module file:
    @test -f "{{ file }}" || { echo "iKy - source file not found: {{ file }}" >&2; exit 1; }
    @mkdir -p backend/cookies
    .venv/bin/python install/scripts/grab_cookies.py \
        --module {{ module }} --import-file "{{ file }}" \
        --out "backend/cookies/{{ module }}_cookies.json"

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

# --------------------------------------------------------------------------
# Native (non-Docker) lifecycle.
#
# Levanta iKy en el host con Caddy + Redis + Celery + Uvicorn, sin Docker.
# El frontend nuevo se descarga del release de kennbroorg/iKy (mismo URL
# que usa el Dockerfile de iky-frontend). Ver scripts/up-native.sh.
# --------------------------------------------------------------------------

# Start iKy natively (no Docker). Ctrl-C in the terminal stops everything.
# Passes --install-deps on first run; skip it on subsequent runs with:
#   just up-native-no-install
up-native:
    ./scripts/up-native.sh --install-deps

# Same as up-native but assumes the venv is already provisioned.
up-native-no-install:
    ./scripts/up-native.sh

# Stop everything started by up-native. Reads PID files from .run/pids/.
# Does NOT kill a Redis that was already running before up-native.
down-native:
    #!/usr/bin/env sh
    set -e
    pids_dir=".run/pids"
    if [ ! -d "${pids_dir}" ]; then
        echo "Nothing to stop: ${pids_dir} does not exist."
        exit 0
    fi
    stopped=0
    for f in "${pids_dir}"/*.pid; do
        [ -f "${f}" ] || continue
        pid=$(cat "${f}")
        name=$(basename "${f}" .pid)
        if ! kill -0 "${pid}" 2>/dev/null; then
            echo "  ${name} (pid ${pid}) already gone"
            rm -f "${f}"
            continue
        fi
        printf '  stopping %s (pid %s)... ' "${name}" "${pid}"
        kill -TERM "${pid}" 2>/dev/null || true
        waited=0
        while [ ${waited} -lt 5 ] && kill -0 "${pid}" 2>/dev/null; do
            sleep 1
            waited=$((waited + 1))
        done
        if kill -0 "${pid}" 2>/dev/null; then
            kill -KILL "${pid}" 2>/dev/null || true
            echo "killed"
        else
            echo "stopped"
        fi
        rm -f "${f}"
        stopped=$((stopped + 1))
    done
    echo "Stopped ${stopped} service(s)."

# Wipe the native setup caches (Caddy binary, frontend tarball, logs, pids).
# Keeps the venv intact.
up-native-clean:
    rm -rf .tools .run frontend/dist-native
    echo "Native caches wiped (venv kept)."
