#!/usr/bin/env bash
# Caddy standalone downloader — baja el binario oficial de Caddy y lo
# guarda en .tools/caddy/. Idempotente: si ya está la versión pedida,
# no vuelve a bajar.
#
# Variables:
#   CADDY_VERSION  — version a bajar (default: 2.8.4)
#   CADDY_DIR      — directorio destino (default: .tools/caddy)
#
# Salida:
#   Path al binario de Caddy en stdout (última línea).

set -euo pipefail

CADDY_VERSION="${CADDY_VERSION:-2.8.4}"
CADDY_DIR="${CADDY_DIR:-.tools/caddy}"
CADDY_BIN="${CADDY_DIR}/caddy"
GITHUB_API="https://api.github.com/repos/caddyserver/caddy/releases/tags"

log() { printf '\033[1;36m[caddy-download]\033[0m %s\n' "$*"; }
die() { printf '\033[1;31m[caddy-download]\033[0m %s\n' "$*" >&2; exit 1; }

arch="$(uname -m)"
case "${arch}" in
    x86_64)        asset_arch="amd64" ;;
    aarch64|arm64) asset_arch="arm64" ;;
    *)             die "Arquitectura no soportada: ${arch}" ;;
esac

asset="caddy_${CADDY_VERSION}_linux_${asset_arch}.tar.gz"
url="https://github.com/caddyserver/caddy/releases/download/v${CADDY_VERSION}/${asset}"

# Si el binario ya está y reporta la versión correcta, no hacemos nada.
if [[ -x "${CADDY_BIN}" ]]; then
    current_version="$("${CADDY_BIN}" version 2>/dev/null | awk '/^v?[0-9]/ {print $1}' | sed 's/^v//')" || true
    if [[ "${current_version}" == "${CADDY_VERSION}" ]]; then
        log "Caddy ${CADDY_VERSION} ya está en ${CADDY_BIN}"
        printf '%s\n' "${CADDY_BIN}"
        exit 0
    fi
    log "Caddy encontrado pero versión ${current_version:-?}, reemplazando por ${CADDY_VERSION}"
fi

command -v curl >/dev/null || die "curl es requerido para bajar Caddy"
command -v tar  >/dev/null || die "tar es requerido para extraer Caddy"

mkdir -p "${CADDY_DIR}"
tmp="$(mktemp -d)"
trap 'rm -rf "${tmp}"' EXIT

log "Descargando Caddy ${CADDY_VERSION} (${asset_arch})..."
curl -fSL --retry 3 --retry-delay 2 -o "${tmp}/${asset}" "${url}" \
    || die "Fallo la descarga de ${url}"

log "Extrayendo..."
tar -xzf "${tmp}/${asset}" -C "${tmp}"

# El tarball contiene un binario "caddy" en la raíz.
[[ -f "${tmp}/caddy" ]] || die "No se encontró el binario 'caddy' en el tarball"
mv "${tmp}/caddy" "${CADDY_BIN}"
chmod +x "${CADDY_BIN}"

log "Caddy ${CADDY_VERSION} instalado en ${CADDY_BIN}"
"${CADDY_BIN}" version | head -1 | sed 's/^/  /'
printf '%s\n' "${CADDY_BIN}"
