FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/outputs

# Set environment variables for production
ENV ENVIRONMENT=production \
    HOST=0.0.0.0 \
    PORT=10000 \
    WORKERS=4 \
    TIMEOUT=120 \
    RELOAD=false

# Expose the port the app runs on
EXPOSE 10000

# Command to run the application
CMD ["gunicorn", "main:app", "--workers", "$WORKERS", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:$PORT", "--timeout", "$TIMEOUT"]
