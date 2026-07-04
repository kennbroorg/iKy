#!/usr/bin/env bash
# scripts/up-native.sh — levanta iKy completo sin Docker.
#
# Qué hace:
#   1. Verifica prerrequisitos del host (redis-server, curl, tar, python3).
#   2. Asegura que el venv de Python tenga las deps críticas (celery,
#      fastapi, uvicorn). Ofrece instalar las que falten.
#   3. Asegura que Caddy standalone esté bajado en .tools/caddy/.
#   4. Descarga y extrae el frontend nuevo desde kennbroorg/iKy releases
#      (mismo URL que usa el Dockerfile de iky-frontend).
#   5. Arranca Redis (si no está corriendo), Celery worker, Uvicorn y
#      Caddy. Cada servicio loguea a .run/logs/<servicio>.log.
#   6. Espera Ctrl-C para detener todo limpio (mata hijos en orden
#      inverso, espera hasta 5s por shutdown graceful).
#
# Variables de entorno (opcional):
#   FRONTEND_VERSION  "latest" (default) o "v1.2.3" para pinear release.
#   IKY_PORT          Puerto del frontend (default 4300, igual al compose).
#   IKY_API_PORT      Puerto del backend (default 5000, igual al compose).
#   IKY_NO_INSTALL    "1" = no instalar deps de Python aunque falten.
#   IKY_NO_PLAYWRIGHT "1" = no correr `playwright install` aunque se pida.
#
# Uso:
#   ./scripts/up-native.sh                 # levanta todo en foreground
#   ./scripts/up-native.sh --install-deps  # también instala deps de Python
#   ./scripts/up-native.sh --with-playwright  # instala browsers de Playwright
#   ./scripts/up-native.sh --help

set -euo pipefail

# --- Constantes y defaults ----------------------------------------------------

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

IKY_PORT="${IKY_PORT:-4300}"
IKY_API_PORT="${IKY_API_PORT:-5000}"
FRONTEND_VERSION="${FRONTEND_VERSION:-latest}"
GITHUB_REPO="kennbroorg/iKy"
GITHUB_TAG="frontend-${FRONTEND_VERSION}"

CADDY_VERSION="${CADDY_VERSION:-2.8.4}"
CADDY_DIR="${REPO_ROOT}/.tools/caddy"
CADDY_BIN="${CADDY_DIR}/caddy"

FRONTEND_DIR="${REPO_ROOT}/frontend/dist-native"
CADDYFILE="${REPO_ROOT}/install/native/Caddyfile"

RUN_DIR="${REPO_ROOT}/.run"
LOG_DIR="${RUN_DIR}/logs"
PID_DIR="${RUN_DIR}/pids"

VENV_BIN="${REPO_ROOT}/.venv/bin"

# Set por las flags CLI; "0" = no hacer esa acción, "1" = hacerla.
FLAG_INSTALL_DEPS=0
FLAG_WITH_PLAYWRIGHT=0

# PIDs de los hijos que nosotros levantamos (NO los que ya estaban
# corriendo). Usado por cleanup() al recibir EXIT/INT/TERM.
declare -a CHILD_PIDS=()
# Marca de quién es nuestro: "1" si lo levantamos nosotros, "0" si reuse.
declare -a CHILD_OWNED=()
declare -a CHILD_NAMES=()

# --- UI helpers --------------------------------------------------------------

if [[ -t 1 ]]; then
    C_RESET=$'\033[0m'
    C_BOLD=$'\033[1m'
    C_DIM=$'\033[2m'
    C_RED=$'\033[31m'
    C_GREEN=$'\033[32m'
    C_YELLOW=$'\033[33m'
    C_BLUE=$'\033[34m'
    C_CYAN=$'\033[36m'
else
    C_RESET=""; C_BOLD=""; C_DIM=""; C_RED=""; C_GREEN=""
    C_YELLOW=""; C_BLUE=""; C_CYAN=""
fi

step()   { printf '\n%s==>%s %s%s\n' "${C_BOLD}${C_CYAN}" "${C_RESET}${C_BOLD}" "$*" "${C_RESET}"; }
ok()     { printf '   %s✓%s %s\n' "${C_GREEN}" "${C_RESET}" "$*"; }
warn()   { printf '   %s!%s %s\n' "${C_YELLOW}" "${C_RESET}" "$*"; }
err()    { printf '   %s✗%s %s\n' "${C_RED}" "${C_RESET}" "$*" >&2; }
info()   { printf '     %s\n' "$*"; }
dim()    { printf '     %s%s%s\n' "${C_DIM}" "$*" "${C_RESET}"; }

die() { err "$*"; exit 1; }

# --- Port helpers ------------------------------------------------------------

# Devuelve 0 si el puerto local está abierto, 1 si no.
# Implementación: bash abre la conexión TCP vía /dev/tcp; si abre OK,
# algo está escuchando. NO leemos del socket (eso era un bug: en
# servicios que aceptan y no mandan data, cat se cuelga hasta el
# timeout y retorna != 0, engañando al if).
port_in_use() {
    local port="$1"
    timeout 1 bash -c "exec 9<>/dev/tcp/127.0.0.1/${port}" 2>/dev/null
}

# Espera hasta N segundos a que el puerto abra. Sale 0 si abrió, 1 si no.
wait_for_port() {
    local port="$1" timeout_s="${2:-15}" name="${3:-${port}}"
    local elapsed=0
    while (( elapsed < timeout_s )); do
        if port_in_use "${port}"; then return 0; fi
        sleep 1
        elapsed=$(( elapsed + 1 ))
    done
    return 1
}

# --- Cleanup (registrado en trap) -------------------------------------------

cleanup() {
    local exit_code=$?
    set +e

    if (( ${#CHILD_PIDS[@]} == 0 )); then
        return ${exit_code}
    fi

    printf '\n'
    step "Deteniendo servicios (Ctrl-C recibido)"

    # Matar en orden inverso al de arranque: caddy, uvicorn, celery, redis
    for (( i=${#CHILD_PIDS[@]}-1; i>=0; i-- )); do
        local pid="${CHILD_PIDS[i]}"
        local owned="${CHILD_OWNED[i]}"
        local name="${CHILD_NAMES[i]}"

        if ! kill -0 "${pid}" 2>/dev/null; then
            dim "${name} (pid ${pid}) ya estaba detenido"
            continue
        fi

        if [[ "${owned}" == "0" ]]; then
            dim "${name} (pid ${pid}) no es nuestro, lo dejo"
            continue
        fi

        printf '   %s↘%s %s (pid %s)... ' "${C_YELLOW}" "${C_RESET}" "${name}" "${pid}"
        kill -TERM "${pid}" 2>/dev/null || true

        # Esperar hasta 5s por shutdown graceful.
        local waited=0
        while (( waited < 5 )) && kill -0 "${pid}" 2>/dev/null; do
            sleep 1
            waited=$(( waited + 1 ))
        done

        if kill -0 "${pid}" 2>/dev/null; then
            kill -KILL "${pid}" 2>/dev/null || true
            printf 'killed\n'
        else
            printf 'stopped\n'
        fi
    done

    # Limpiar PID files (best-effort).
    rm -f "${PID_DIR}"/*.pid 2>/dev/null || true

    printf '\n   %siKy detenido.%s\n' "${C_DIM}" "${C_RESET}"
    return ${exit_code}
}

trap cleanup EXIT INT TERM

# --- Arranque de servicios con tracking --------------------------------------

# Arranca un proceso en background, guarda PID y metadata para cleanup.
# Args: name owned(0|1) pid_file log_file cmd...
start_bg() {
    local name="$1" owned="$2" pid_file="$3" log_file="$4"
    shift 4

    mkdir -p "$(dirname "${pid_file}")" "$(dirname "${log_file}")"

    if [[ -f "${pid_file}" ]] && kill -0 "$(cat "${pid_file}")" 2>/dev/null; then
        local existing_pid
        existing_pid="$(cat "${pid_file}")"
        warn "${name} ya tiene pid file (${existing_pid}); reusando"
        CHILD_PIDS+=("${existing_pid}")
        CHILD_OWNED+=("${owned}")
        CHILD_NAMES+=("${name}")
        return 0
    fi

    "$@" >>"${log_file}" 2>&1 &
    local pid=$!
    echo "${pid}" >"${pid_file}"

    CHILD_PIDS+=("${pid}")
    CHILD_OWNED+=("${owned}")
    CHILD_NAMES+=("${name}")
    return 0
}

# --- Prerrequisitos del host -------------------------------------------------

check_host_prereqs() {
    step "Verificando prerrequisitos del host"

    local missing=()
    command -v redis-server >/dev/null || missing+=("redis-server")
    command -v python3      >/dev/null || missing+=("python3")
    command -v curl         >/dev/null || missing+=("curl")
    command -v tar          >/dev/null || missing+=("tar")

    if (( ${#missing[@]} > 0 )); then
        err "Faltan comandos en el host: ${missing[*]}"
        info "En Debian/Ubuntu: sudo apt install ${missing[*]}"
        die "Instalá los prerrequisitos y volvé a correr el script"
    fi

    ok "redis-server, python3, curl, tar"

    if [[ ! -x "${VENV_BIN}/python" ]]; then
        err "No hay venv en .venv/. Corré: just setup"
        die "Falta el virtualenv"
    fi
    ok "venv encontrado en .venv/"
}

# --- Dependencias de Python --------------------------------------------------

check_python_deps() {
    step "Verificando dependencias de Python en el venv"

    local missing_pkgs=()
    "${VENV_BIN}/python" -c "import celery"  2>/dev/null || missing_pkgs+=("celery")
    "${VENV_BIN}/python" -c "import fastapi" 2>/dev/null || missing_pkgs+=("fastapi")
    "${VENV_BIN}/python" -c "import uvicorn" 2>/dev/null || missing_pkgs+=("uvicorn")

    if (( ${#missing_pkgs[@]} == 0 )); then
        ok "celery, fastapi, uvicorn presentes"
        return 0
    fi

    if [[ "${IKY_NO_INSTALL:-0}" == "1" ]]; then
        die "Faltan: ${missing_pkgs[*]} (IKY_NO_INSTALL=1 evita instalar)"
    fi

    warn "Faltan: ${missing_pkgs[*]}"
    if (( FLAG_INSTALL_DEPS == 0 )); then
        info "Pasá --install-deps o corré: .venv/bin/pip install -r requirements.txt"
        die "Dependencias de Python incompletas"
    fi

    info "Instalando requirements.txt en el venv..."
    "${VENV_BIN}/pip" install -q -r "${REPO_ROOT}/requirements.txt" \
        || die "pip install falló"
    ok "Dependencias instaladas"
}

maybe_install_playwright() {
    if (( FLAG_WITH_PLAYWRIGHT == 0 )); then return 0; fi
    if [[ "${IKY_NO_PLAYWRIGHT:-0}" == "1" ]]; then
        warn "IKY_NO_PLAYWRIGHT=1, salto playwright install"
        return 0
    fi

    step "Instalando browsers de Playwright (chromium)"
    info "Tarda ~150 MB. Solo necesario para TikTokApi."
    "${VENV_BIN}/playwright" install --with-deps chromium \
        || warn "playwright install falló (no bloqueante para el resto)"
    ok "Playwright instalado"
}

# --- Frontend ----------------------------------------------------------------

ensure_frontend() {
    step "Descargando frontend nuevo (${GITHUB_TAG})"

    mkdir -p "${FRONTEND_DIR}"

    if [[ -f "${FRONTEND_DIR}/index.html" ]]; then
        if [[ "${FRONTEND_VERSION}" == "latest" ]]; then
            # Para "latest" siempre re-descargamos (es liviano y queremos
            # la versión más reciente); si querés pinear, usá vX.Y.Z.
            info "Ya hay un frontend extraído, pero 'latest' siempre se re-baja"
        else
            ok "Frontend ${FRONTEND_VERSION} ya extraído, no re-descargo"
            return 0
        fi
    fi

    local asset
    if [[ "${FRONTEND_VERSION}" == "latest" ]]; then
        asset="frontend-dist-latest.tar.gz"
    else
        asset="frontend-dist-${GITHUB_TAG}.tar.gz"
    fi

    local url="https://github.com/${GITHUB_REPO}/releases/download/${GITHUB_TAG}/${asset}"
    info "URL: ${url}"

    local tmp
    tmp="$(mktemp -d)"
    trap 'rm -rf "${tmp}"' RETURN

    if ! curl -fSL --retry 3 --retry-delay 2 -o "${tmp}/${asset}" "${url}"; then
        rm -rf "${tmp}"
        trap - RETURN
        die "No pude bajar ${asset} del release ${GITHUB_TAG} en ${GITHUB_REPO}."
    fi

    rm -rf "${FRONTEND_DIR}"
    mkdir -p "${FRONTEND_DIR}"
    tar -xzf "${tmp}/${asset}" -C "${FRONTEND_DIR}" \
        || die "No pude extraer ${asset}"
    rm -rf "${tmp}"
    trap - RETURN

    [[ -f "${FRONTEND_DIR}/index.html" ]] \
        || die "El tarball se extrajo pero no hay index.html en ${FRONTEND_DIR}"
    ok "Frontend extraído en ${FRONTEND_DIR}"
}

# --- Caddy -------------------------------------------------------------------

ensure_caddy() {
    step "Asegurando Caddy ${CADDY_VERSION} standalone"

    if [[ -x "${CADDY_BIN}" ]]; then
        local current
        current="$("${CADDY_BIN}" version 2>/dev/null | awk '/^v?[0-9]/ {print $1}' | sed 's/^v//')" || current="?"
        if [[ "${current}" == "${CADDY_VERSION}" ]]; then
            ok "Caddy ${CADDY_VERSION} ya en ${CADDY_BIN}"
        else
            warn "Caddy ${current} != ${CADDY_VERSION}, re-bajando"
            rm -f "${CADDY_BIN}"
        fi
    fi

    if [[ ! -x "${CADDY_BIN}" ]]; then
        info "Bajando Caddy ${CADDY_VERSION}..."
        CADDY_VERSION="${CADDY_VERSION}" CADDY_DIR="${CADDY_DIR}" \
            "${REPO_ROOT}/install/native/caddy-download.sh" >/dev/null \
            || die "Falló la descarga de Caddy"
    fi

    ok "Caddy listo"
}

validate_caddyfile() {
    step "Validando Caddyfile"
    # Exporto defaults por si las variables no están en el entorno:
    # los placeholders {$VAR:default} del Caddyfile las usan.
    export IKY_PORT IKY_FRONTEND_DIR IKY_LOG_DIR
    : "${IKY_PORT:=${IKY_PORT:-4300}}"
    IKY_FRONTEND_DIR="${IKY_FRONTEND_DIR:-${FRONTEND_DIR}}"
    IKY_LOG_DIR="${IKY_LOG_DIR:-${LOG_DIR}}"
    export IKY_PORT IKY_FRONTEND_DIR IKY_LOG_DIR

    if ! "${CADDY_BIN}" validate --config "${CADDYFILE}" 2>"${LOG_DIR}/caddy-validate.err"; then
        err "Caddyfile inválido. Detalle:"
        cat "${LOG_DIR}/caddy-validate.err" >&2
        die "Arreglá el Caddyfile antes de continuar"
    fi
    ok "Caddyfile válido"
}

# --- Servicios ---------------------------------------------------------------

start_redis() {
    step "Redis"

    if port_in_use 6379; then
        # Puerto ocupado. Verificamos si es un Redis y mostramos info.
        # Por default REUSAMOS: si Celery después no se conecta, el log
        # va a decir exactamente por qué (auth, protected mode, etc).
        if command -v redis-cli >/dev/null 2>&1; then
            local ping_output version
            # No usar `redis-cli -t 1`: el -t interno es connect timeout
            # de redis-cli y es tan agresivo que a veces mata el comando
            # antes de llegar la respuesta. Usamos `timeout` externo.
            ping_output="$(timeout 3 redis-cli -p 6379 PING 2>&1 || true)"
            if [[ "${ping_output}" == *"PONG"* ]]; then
                version="$(timeout 3 redis-cli -p 6379 INFO server 2>/dev/null \
                    | awk -F: '/^redis_version/ {gsub(/\r/, ""); print $2; exit}')"
                ok "Redis ${version:-?} ya escucha en :6379 — lo reusamos, no lo matamos"
                CHILD_PIDS+=(0); CHILD_OWNED+=(0)
                CHILD_NAMES+=("redis:6379 (reused, v${version:-?})")
                return 0
            fi

            # PING no devolvió PONG. Mostramos QUÉ devolvió para que se
            # sepa qué está pasando. Reusamos igual — Celery va a fallar
            # claro si la auth/version no es compatible.
            info "redis-cli PING devolvió: ${ping_output:-<sin respuesta>}"
            case "${ping_output}" in
                *NOAUTH*|*WRONGPASS*)
                    warn "el Redis requiere autenticación (requirepass)."
                    warn "configura CELERY_BROKER_URL=redis://:PASSWORD@127.0.0.1:6379/0"
                    warn "antes de up-native, o cambiá el requirepass del server." ;;
                *DENIED*|*protected*)
                    warn "Redis en protected mode. Si esto no es intencional,"
                    warn "agregá 'bind 127.0.0.1' o un requirepass en su config." ;;
            esac
            warn "reusando :6379 de todas formas — Celery confirmará si funciona"
            CHILD_PIDS+=(0); CHILD_OWNED+=(0)
            CHILD_NAMES+=("redis:6379 (reused, PING no respondió PONG)")
            return 0
        fi

        # No hay redis-cli: no podemos verificar. Reusamos con warning.
        warn "puerto 6379 ocupado y no hay redis-cli para verificar"
        warn "asumimos que es un Redis — si Celery falla, el log lo va a decir"
        CHILD_PIDS+=(0); CHILD_OWNED+=(0)
        CHILD_NAMES+=("redis:6379 (reused, unverified)")
        return 0
    fi

    info "levantando redis-server en :6379"
    start_bg "redis" 1 "${PID_DIR}/redis.pid" "${LOG_DIR}/redis.log" \
        redis-server --daemonize no --port 6379 --dir "${RUN_DIR}/redis"
    mkdir -p "${RUN_DIR}/redis"

    if wait_for_port 6379 10 "redis"; then
        ok "redis escuchando en :6379 (pid ${CHILD_PIDS[-1]})"
    else
        tail -n 20 "${LOG_DIR}/redis.log" >&2
        die "redis no levantó en 10s"
    fi
}

start_celery() {
    step "Celery worker"

    if ! port_in_use 6379; then
        die "redis no está en :6379, no puedo arrancar celery"
    fi

    # export de env vars que celery_app.py lee por default.
    # Si no las seteo, caen a redis://localhost:6379/0 — que es justo
    # lo que queremos cuando Redis corre local en el host.
    cd "${REPO_ROOT}/backend"
    start_bg "celery" 1 "${PID_DIR}/celery.pid" "${LOG_DIR}/celery.log" \
        "${VENV_BIN}/celery" -A celery_worker.celery worker --loglevel=INFO
    cd "${REPO_ROOT}"
    ok "celery arrancado (logs: .run/logs/celery.log)"
}

start_uvicorn() {
    step "Uvicorn (FastAPI)"

    cd "${REPO_ROOT}/backend"
    start_bg "uvicorn" 1 "${PID_DIR}/uvicorn.pid" "${LOG_DIR}/uvicorn.log" \
        "${VENV_BIN}/uvicorn" main:app --host 127.0.0.1 --port "${IKY_API_PORT}" --log-level info
    cd "${REPO_ROOT}"

    if wait_for_port "${IKY_API_PORT}" 20 "uvicorn"; then
        ok "uvicorn escuchando en :${IKY_API_PORT} (pid ${CHILD_PIDS[-1]})"
    else
        tail -n 30 "${LOG_DIR}/uvicorn.log" >&2
        die "uvicorn no levantó en 20s"
    fi
}

start_caddy() {
    step "Caddy (frontend + reverse proxy)"

    # El Caddyfile usa IKY_PORT, IKY_FRONTEND_DIR y IKY_LOG_DIR.
    export IKY_PORT IKY_FRONTEND_DIR="${FRONTEND_DIR}" IKY_LOG_DIR="${LOG_DIR}"

    start_bg "caddy" 1 "${PID_DIR}/caddy.pid" "${LOG_DIR}/caddy.log" \
        "${CADDY_BIN}" run --config "${CADDYFILE}" --adapter ""

    if wait_for_port "${IKY_PORT}" 15 "caddy"; then
        ok "caddy escuchando en :${IKY_PORT} (pid ${CHILD_PIDS[-1]})"
    else
        tail -n 30 "${LOG_DIR}/caddy.log" >&2
        die "caddy no levantó en 15s"
    fi
}

# --- CLI ---------------------------------------------------------------------

usage() {
    sed -n '2,30p' "${BASH_SOURCE[0]}" | sed 's/^# \?//'
    cat <<EOF

Opciones:
  --install-deps       Instalar requirements.txt en el venv si falta algo.
  --with-playwright    Correr \`playwright install --with-deps chromium\`
                       (necesario solo para TikTokApi, ~150 MB).
  --help               Mostrar esta ayuda.

Variables de entorno (ej. FRONTEND_VERSION=v1.2.3 ./scripts/up-native.sh):
  FRONTEND_VERSION     "latest" o "vX.Y.Z" (default: latest).
  IKY_PORT             Puerto del frontend (default: 4300).
  IKY_API_PORT         Puerto del backend  (default: 5000).
  IKY_NO_INSTALL       "1" para no instalar deps aunque falten.
  IKY_NO_PLAYWRIGHT    "1" para saltarse playwright install.

Logs en .run/logs/{redis,celery,uvicorn,caddy}.log
PIDs  en .run/pids/*.pid
EOF
}

parse_args() {
    while (( $# > 0 )); do
        case "$1" in
            --install-deps)    FLAG_INSTALL_DEPS=1 ;;
            --with-playwright) FLAG_WITH_PLAYWRIGHT=1 ;;
            --help|-h)         usage; exit 0 ;;
            --*)               die "Flag desconocida: $1 (probá --help)" ;;
            *)                 die "Argumento no esperado: $1" ;;
        esac
        shift
    done
}

# --- Main --------------------------------------------------------------------

main() {
    parse_args "$@"

    step "iKy up-native (sin Docker)"
    info "Frontend: ${GITHUB_REPO}@${GITHUB_TAG}"
    info "API:      http://127.0.0.1:${IKY_API_PORT}"
    info "Web:      http://127.0.0.1:${IKY_PORT}"
    info "Logs:     ${LOG_DIR}"

    mkdir -p "${LOG_DIR}" "${PID_DIR}" "${RUN_DIR}/redis"

    check_host_prereqs
    check_python_deps
    maybe_install_playwright
    ensure_frontend
    ensure_caddy
    validate_caddyfile
    start_redis
    start_celery
    start_uvicorn
    start_caddy

    printf '\n'
    step "${C_GREEN}iKy listo${C_RESET}"
    cat <<EOF

   Frontend:  http://127.0.0.1:${IKY_PORT}
   Backend:   http://127.0.0.1:${IKY_API_PORT}
   Health:    http://127.0.0.1:${IKY_PORT}/health

   Logs:      tail -f ${LOG_DIR}/{caddy,uvicorn,celery,redis}.log

   Ctrl-C para detener todo limpio.
EOF

    # Quedarse en foreground hasta que llegue una señal.
    # `wait -n` espera a cualquier hijo; con Ctrl-C, el trap cleanup corre.
    wait
}

main "$@"
