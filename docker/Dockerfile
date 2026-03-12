# Multi-stage build for MCP Code Review Server

FROM node:20-alpine as ui-builder

WORKDIR /app/ui

# Install UI dependencies and build artifacts
COPY ui/package*.json ./
RUN npm ci
COPY ui/ ./
RUN npm run build


FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt


FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY . .
COPY --from=ui-builder /app/ui/dist ./ui/dist

# Make sure scripts are in PATH
ENV PATH=/root/.local/bin:$PATH

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/')" || exit 1

# Run server
CMD ["python", "server.py"]
