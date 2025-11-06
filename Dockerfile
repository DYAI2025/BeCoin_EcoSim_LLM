# Multi-stage build for BeCoin EcoSim Dashboard
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies
COPY dashboard/requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY becoin_economy/ /app/becoin_economy/
COPY dashboard/ /app/dashboard/

# Create directory for discovery sessions (optional, can be overridden by volume mount)
RUN mkdir -p /app/.claude-flow/discovery-sessions

# Set Python path to include /app
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PORT=3000 \
    HOST=0.0.0.0 \
    AUTH_USERNAME="" \
    AUTH_PASSWORD=""

# Expose port for FastAPI
EXPOSE 3000

# Health check with longer startup period
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:3000/api/status || exit 1

# Run the FastAPI server
CMD ["uvicorn", "dashboard.server:app", "--host", "0.0.0.0", "--port", "3000"]
