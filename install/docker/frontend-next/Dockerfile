FROM node:22-bookworm-slim AS build

WORKDIR /app

# Install git (may be needed for some npm packages)
RUN apt-get update && \
    apt-get install -y --no-install-recommends git ca-certificates && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY frontend-next/package*.json ./
RUN npm ci
COPY frontend-next/ .

ARG VITE_API_URL=http://localhost:5000
ARG VITE_WS_URL=ws://localhost:5000
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY install/docker/frontend-next/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 5173

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget -q --spider http://localhost:5173/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
