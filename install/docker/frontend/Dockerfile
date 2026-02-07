FROM node:14-bullseye-slim

WORKDIR /app

# Install git and ca-certificates (required for GitHub dependencies over HTTPS)
RUN apt-get update && \
    apt-get install -y --no-install-recommends git ca-certificates && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy package.json only (exclude lock file to regenerate with HTTPS URLs)
COPY frontend/package.json ./

# Install dependencies
RUN npm install --legacy-peer-deps

# Copy frontend code
COPY frontend .

# Configure ng serve for Docker
RUN sed -i 's/"start":.*/"start": "ng serve --host 0.0.0.0 --disable-host-check",/' package.json

EXPOSE 4200

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD node -e "require('http').get('http://localhost:4200', (r) => process.exit(r.statusCode === 200 ? 0 : 1))" || exit 1

CMD ["npm", "start"]
