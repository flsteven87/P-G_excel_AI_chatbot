# Backend Dockerfile for Excel AI Chatbot
# Python FastAPI application with vanna.ai and Excel processing

FROM python:3.11-slim AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies for Excel processing and database
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    ca-certificates \
    # Excel processing dependencies (openpyxl, xlrd)
    libxml2 \
    libxslt1.1 \
    zlib1g \
    # Pandas/PyArrow compilation
    gcc \
    g++ \
    libc-dev \
    # PostgreSQL client libraries
    libpq5 \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install UV package manager
RUN pip install uv

# Set working directory
WORKDIR /app

# Copy UV configuration files
COPY pyproject.toml uv.lock ./

# Install Python dependencies using UV (production only)
RUN uv sync --frozen --no-dev

# Copy application source code
COPY app/ ./app/

# Create ChromaDB persist directory with proper permissions
RUN mkdir -p /data/vanna_db && \
    chmod 755 /data/vanna_db

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app /data
USER app

# Expose port (Zeabur will inject PORT env var)
EXPOSE 8080

# Set PORT environment variable for Zeabur
ENV PORT=8080

# ChromaDB persistent storage path
ENV CHROMADB_PERSIST_PATH=/data/vanna_db

# Health check with extended start period for vanna.ai initialization
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Run the application using uvicorn directly
CMD ["sh", "-c", "uv run uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --workers 1"]