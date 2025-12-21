# Production Dockerfile for Localrun - Alpine-based (lightweight)

# ============================================
# Backend Builder Stage
# ============================================
FROM python:3.11-alpine AS backend-builder

WORKDIR /app

# Install build dependencies
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    openssl-dev \
    cargo \
    postgresql-dev

# Install pipenv
RUN pip install --no-cache-dir pipenv

# Copy backend dependencies
COPY backend/Pipfile backend/Pipfile.lock ./
RUN pipenv install --system --deploy

# ============================================
# Frontend Builder Stage  
# ============================================
FROM node:22-alpine AS frontend-builder

WORKDIR /app/frontend

# Install pnpm
RUN corepack enable && corepack prepare pnpm@latest --activate

# Copy frontend package files
COPY frontend/package.json frontend/pnpm-lock.yaml ./

# Install dependencies
RUN pnpm install --frozen-lockfile

# Copy frontend source
COPY frontend/ ./

# Build frontend for production
RUN pnpm run build

# ============================================
# Production Runtime Stage
# ============================================
FROM python:3.11-alpine

# Install runtime dependencies
RUN apk add --no-cache \
    nodejs \
    npm \
    ca-certificates \
    curl \
    supervisor \
    docker-cli \
    libpq

# Install cloudflared
RUN ARCH=$(uname -m | sed 's/x86_64/amd64/;s/aarch64/arm64/') \
    && wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-${ARCH} -O /usr/bin/cloudflared \
    && chmod +x /usr/bin/cloudflared

# Install ngrok
RUN ARCH=$(uname -m | sed 's/x86_64/amd64/;s/aarch64/arm64/') \
    && wget -q https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-${ARCH}.tgz \
    && tar -xzf ngrok-v3-stable-linux-${ARCH}.tgz -C /usr/bin \
    && chmod +x /usr/bin/ngrok \
    && rm ngrok-v3-stable-linux-${ARCH}.tgz

# Create localrun user
RUN addgroup -S localrun && adduser -S -G localrun localrun

# Set working directory
WORKDIR /app

# Copy Python dependencies from builder
COPY --from=backend-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=backend-builder /usr/local/bin /usr/local/bin

# Copy backend application
COPY backend/ ./backend/

COPY --from=frontend-builder /app/frontend/.output ./frontend/.output

RUN mkdir -p /data/localrun/storage /data/localrun/cloudflared /data/localrun/logs /app/logs \
    && chown -R localrun:localrun /data/localrun /app \
    && find /app/backend -type f -name "*.pyc" -delete \
    && find /app/backend -type d -name "__pycache__" -delete

# Copy build files
COPY build/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY build/entrypoint.sh /entrypoint.sh
COPY build/healthcheck.sh /healthcheck.sh

RUN chmod +x /entrypoint.sh /healthcheck.sh

EXPOSE 8000 3006

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD /healthcheck.sh

ENTRYPOINT ["/entrypoint.sh"]
