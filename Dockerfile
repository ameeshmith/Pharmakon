# Pharmakon Backend Dockerfile (Python 3.12 + FastAPI + FastMCP Streamable HTTP)
# Compatible with Hugging Face Spaces (Docker port 7860) and Render / standard Docker (port 8000)

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=7860 \
    HOST=0.0.0.0 \
    DATABASE_URL=sqlite:////tmp/pharmakon.db

WORKDIR /app

# Install system essentials and uv
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir uv

# Copy project dependency definitions first for layer caching
COPY pyproject.toml uv.lock ./

# Install production dependencies into system Python
RUN uv pip install --system --no-cache -r pyproject.toml

# Copy application source
COPY server ./server
COPY evals ./evals
COPY docs ./docs
COPY .licenses ./.licenses

# Create non-root user (required by Hugging Face Spaces UID 1000)
RUN useradd -m -u 1000 pharmakon && chown -R pharmakon:pharmakon /app
USER pharmakon

EXPOSE 7860 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT:-7860}/health || exit 1

CMD ["sh", "-c", "uvicorn server.main:app --host ${HOST:-0.0.0.0} --port ${PORT:-7860}"]
