FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    fonts-noto-color-emoji \
    fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

# Copy pyproject.toml first for dependency caching
COPY pyproject.toml .

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Install Playwright browser for server-side PDF rendering
RUN python -m playwright install --with-deps chromium

# Copy application code
COPY apps/api /app/apps/api
COPY packages /app/packages

# Set Python path
ENV PYTHONPATH=/app/apps/api:/app/packages:$PYTHONPATH

WORKDIR /app/apps/api

# Default command (can be overridden in docker-compose)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
