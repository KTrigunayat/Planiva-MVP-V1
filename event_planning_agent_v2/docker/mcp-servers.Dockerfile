FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    DEBIAN_FRONTEND=noninteractive

# Set work directory
WORKDIR /app

# Install system dependencies including uv
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    libpq-dev \
    gcc \
    && curl -LsSf https://astral.sh/uv/install.sh | sh \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN useradd --create-home --shell /bin/bash --uid 1001 mcp

# Add uv to PATH for all users
ENV PATH="/root/.cargo/bin:/home/mcp/.cargo/bin:$PATH"

# Install uvx as root, then switch to mcp user
RUN /root/.cargo/bin/uv tool install uvx

# Copy MCP server configurations and source code
COPY --chown=mcp:mcp mcp_servers/ /app/mcp_servers/
COPY --chown=mcp:mcp config/mcp_config.json /app/config/mcp_config.json

# Create startup script with better error handling and logging
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
echo "Starting MCP Servers..."\n\
\n\
# Function to handle cleanup\n\
cleanup() {\n\
    echo "Shutting down MCP servers..."\n\
    kill $VENDOR_PID $CALC_PID $MONITOR_PID 2>/dev/null || true\n\
    wait\n\
    exit 0\n\
}\n\
\n\
# Set up signal handlers\n\
trap cleanup SIGTERM SIGINT\n\
\n\
# Wait for database to be ready\n\
echo "Waiting for database connection..."\n\
while ! python -c "import psycopg2; psycopg2.connect(\"$DATABASE_URL\")" 2>/dev/null; do\n\
    sleep 2\n\
done\n\
echo "Database connection established!"\n\
\n\
# Start vendor data server\n\
echo "Starting vendor data server..."\n\
python /app/mcp_servers/vendor_server.py &\n\
VENDOR_PID=$!\n\
\n\
# Start calculation server\n\
echo "Starting calculation server..."\n\
python /app/mcp_servers/calculation_server.py &\n\
CALC_PID=$!\n\
\n\
# Start monitoring server\n\
echo "Starting monitoring server..."\n\
python /app/mcp_servers/monitoring_server.py &\n\
MONITOR_PID=$!\n\
\n\
echo "All MCP servers started successfully!"\n\
echo "Vendor Server PID: $VENDOR_PID"\n\
echo "Calculation Server PID: $CALC_PID"\n\
echo "Monitoring Server PID: $MONITOR_PID"\n\
\n\
# Wait for any process to exit\n\
wait -n\n\
\n\
# If we get here, one of the processes exited\n\
echo "One of the MCP servers exited, shutting down..."\n\
cleanup\n\
' > /app/start-mcp-servers.sh && chmod +x /app/start-mcp-servers.sh

# Switch to non-root user
USER mcp

# Create necessary directories
RUN mkdir -p /app/logs /app/data

# Expose MCP server ports
EXPOSE 8001 8002 8003

# Health check for MCP servers
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import socket; [socket.create_connection((\"localhost\", port), timeout=5).close() for port in [8001, 8002, 8003]]" || exit 1

# Run MCP servers
CMD ["/app/start-mcp-servers.sh"]