##############################################################################
# Dockerfile — iKy-frontend (nginx:alpine, release-asset distribution)
#
# Instead of building the Angular app inside Docker, this image downloads
# a pre-built release asset from the public kennbroorg/iKy GitHub repo,
# extracts it into the nginx html root, and serves it.
#
# Build args:
#   FRONTEND_VERSION  — "latest" (default) or a semver tag without prefix,
#                       e.g. "v1.2.3".  Maps to GitHub Release tags:
#                         latest  → tag: frontend-latest
#                                   asset: frontend-dist-latest.tar.gz
#                         v1.2.3  → tag: frontend-v1.2.3
#                                   asset: frontend-dist-frontend-v1.2.3.tar.gz
#
# Usage:
#   docker build .                                       # pulls latest
#   docker build --build-arg FRONTEND_VERSION=v1.2.3 .  # pins version
##############################################################################

FROM nginx:alpine

ARG FRONTEND_VERSION=latest
ARG GITHUB_REPO=kennbroorg/iKy

# --------------------------------------------------------------------------
# Download and extract the pre-built frontend release asset.
#
# Two URL patterns:
#   latest  → /releases/download/frontend-latest/frontend-dist-latest.tar.gz
#   vX.Y.Z  → /releases/download/frontend-vX.Y.Z/frontend-dist-frontend-vX.Y.Z.tar.gz
#
# curl is used instead of BusyBox wget: supports --show-progress is not
# available in BusyBox wget, and curl handles GitHub redirect chains better.
# set -e ensures the build fails immediately if the download fails.
# --------------------------------------------------------------------------
RUN apk add --no-cache curl

RUN set -e; \
    if [ "$FRONTEND_VERSION" = "latest" ]; then \
        TAG="frontend-latest"; \
        ASSET="frontend-dist-latest.tar.gz"; \
    else \
        TAG="frontend-${FRONTEND_VERSION}"; \
        ASSET="frontend-dist-${TAG}.tar.gz"; \
    fi; \
    DOWNLOAD_URL="https://github.com/${GITHUB_REPO}/releases/download/${TAG}/${ASSET}"; \
    echo ">>> Downloading frontend from: ${DOWNLOAD_URL}"; \
    curl -fSL -o /tmp/frontend.tar.gz "${DOWNLOAD_URL}" || { \
        echo "ERROR: Failed to download ${DOWNLOAD_URL}"; \
        echo "       Check that release '${TAG}' exists on ${GITHUB_REPO}"; \
        echo "       and that FRONTEND_VERSION is correct."; \
        exit 1; \
    }; \
    echo ">>> Extracting to /usr/share/nginx/html/"; \
    tar -xzf /tmp/frontend.tar.gz -C /usr/share/nginx/html/; \
    rm -f /tmp/frontend.tar.gz; \
    echo ">>> Done. Contents:"; \
    ls /usr/share/nginx/html/

# --------------------------------------------------------------------------
# Copy the custom nginx config (SPA routing + API proxy + security headers).
# Replaces the default nginx:alpine conf.d/default.conf.
# --------------------------------------------------------------------------
COPY install/docker/iKy-frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

# --------------------------------------------------------------------------
# Health check using curl (installed above).
# Uses the dedicated /health endpoint defined in nginx.conf.
# --------------------------------------------------------------------------
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost/health || exit 1
