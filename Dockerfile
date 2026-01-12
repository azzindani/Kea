# ============================================================================
# Multi-stage Dockerfile for Kea Research Engine
# ============================================================================

# Base image with Python dependencies
FROM python:3.11-slim as base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

# Install Playwright for browser scraping
RUN pip install playwright && playwright install chromium --with-deps

# Copy source code
COPY . .

# ============================================================================
# Orchestrator Service
# ============================================================================
FROM base as orchestrator

EXPOSE 8000

CMD ["python", "-m", "services.orchestrator.main"]

# ============================================================================
# RAG Service
# ============================================================================
FROM base as rag-service

EXPOSE 8001

CMD ["python", "-m", "services.rag_service.main"]

# ============================================================================
# API Gateway
# ============================================================================
FROM base as api-gateway

EXPOSE 8000

CMD ["python", "-m", "services.api_gateway.main"]

# ============================================================================
# Background Worker
# ============================================================================
FROM base as worker

CMD ["python", "-m", "workers.research_worker"]

# ============================================================================
# Development (all-in-one with hot reload)
# ============================================================================
FROM base as development

# Install dev dependencies
RUN pip install --no-cache-dir -e ".[dev]"

EXPOSE 8000 8001

CMD ["uvicorn", "services.api_gateway.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
