# Multi-stage Dockerfile for Event Planning Agent v2

# Build stage
FROM python:3.11-slim as builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    gcc \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt pyproject.toml ./
RUN pip install --upgrade pip setuptools wheel \
    && pip install --user -r requirements.txt

# Development stage
FROM python:3.11-slim as development

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    libpq5 \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN useradd --create-home --shell /bin/bash --uid 1000 app

# Copy Python packages from builder
COPY --from=builder /root/.local /home/app/.local
ENV PATH=/home/app/.local/bin:$PATH

# Copy project files
COPY --chown=app:app . .

# Install the package in development mode
RUN pip install -e . \
    && chown -R app:app /app

# Create necessary directories
RUN mkdir -p /app/logs /app/data \
    && chown -R app:app /app/logs /app/data

USER app
EXPOSE 8000

# Development startup script with hot reloading
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
echo "Starting Event Planning Agent v2 (Development Mode)"\n\
\n\
# Wait for database\n\
echo "Waiting for database..."\n\
timeout=60\n\
while [ $timeout -gt 0 ]; do\n\
    if python -c "import psycopg2; psycopg2.connect(\"$DATABASE_URL\")" 2>/dev/null; then\n\
        echo "Database connection established!"\n\
        break\n\
    fi\n\
    sleep 2\n\
    timeout=$((timeout-2))\n\
done\n\
\n\
if [ $timeout -le 0 ]; then\n\
    echo "Database connection timeout!"\n\
    exit 1\n\
fi\n\
\n\
# Run database setup\n\
python -m event_planning_agent_v2.database.setup\n\
\n\
# Start the application with hot reloading\n\
exec uvicorn event_planning_agent_v2.main:app \\\n\
  --host 0.0.0.0 \\\n\
  --port 8000 \\\n\
  --reload \\\n\
  --log-level ${LOG_LEVEL:-debug} \\\n\
  --access-log \\\n\
  --use-colors\n\
' > /app/start-dev.sh && chmod +x /app/start-dev.sh

CMD ["/app/start-dev.sh"]

# Production stage
FROM python:3.11-slim as production

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install only runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN useradd --create-home --shell /bin/bash --uid 1000 app

# Copy Python packages from builder
COPY --from=builder /root/.local /home/app/.local
ENV PATH=/home/app/.local/bin:$PATH

# Copy only necessary project files
COPY --chown=app:app event_planning_agent_v2/ ./event_planning_agent_v2/
COPY --chown=app:app config/ ./config/
COPY --chown=app:app pyproject.toml ./

# Install the package
RUN pip install . \
    && chown -R app:app /app

# Create necessary directories
RUN mkdir -p /app/logs /app/data \
    && chown -R app:app /app/logs /app/data

USER app
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=5 \
    CMD curl -f http://localhost:8000/health || exit 1

# Production startup script
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
echo "Starting Event Planning Agent v2 (Production Mode)"\n\
\n\
# Wait for database with timeout\n\
echo "Waiting for database..."\n\
timeout=120\n\
while [ $timeout -gt 0 ]; do\n\
    if python -c "import psycopg2; psycopg2.connect(\"$DATABASE_URL\")" 2>/dev/null; then\n\
        echo "Database connection established!"\n\
        break\n\
    fi\n\
    sleep 2\n\
    timeout=$((timeout-2))\n\
done\n\
\n\
if [ $timeout -le 0 ]; then\n\
    echo "Database connection timeout!"\n\
    exit 1\n\
fi\n\
\n\
# Run database setup\n\
python -m event_planning_agent_v2.database.setup\n\
\n\
# Start the application with multiple workers\n\
exec uvicorn event_planning_agent_v2.main:app \\\n\
  --host 0.0.0.0 \\\n\
  --port 8000 \\\n\
  --workers ${API_WORKERS:-4} \\\n\
  --worker-class uvicorn.workers.UvicornWorker \\\n\
  --log-level ${LOG_LEVEL:-info} \\\n\
  --access-log \\\n\
  --no-use-colors\n\
' > /app/start-prod.sh && chmod +x /app/start-prod.sh

CMD ["/app/start-prod.sh"]