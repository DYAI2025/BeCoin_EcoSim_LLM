# Multi-stage build for BeCoin EcoSim Dashboard
FROM python:3.11-slim AS base

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies
COPY dashboard/requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY becoin_economy/ /app/becoin_economy/
COPY dashboard/ /app/dashboard/

# Create directory for discovery sessions (will be mounted as volume in production)
RUN mkdir -p /app/.claude-flow/discovery-sessions

# Expose port for FastAPI
EXPOSE 3000

# Environment variables with defaults
ENV PYTHONUNBUFFERED=1 \
    PORT=3000 \
    HOST=0.0.0.0 \
    AUTH_USERNAME="" \
    AUTH_PASSWORD=""

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:3000/api/status')" || exit 1

# Run the FastAPI server
CMD ["python", "-m", "uvicorn", "dashboard.server:app", "--host", "0.0.0.0", "--port", "3000"]
