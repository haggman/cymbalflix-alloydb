# CymbalFlix Discover - Cloud Run Dockerfile
# ===========================================
# This Dockerfile builds a container for deploying the CymbalFlix
# Streamlit application to Cloud Run.

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
# (needed for some Python packages and healthier container)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better Docker layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port (Cloud Run uses PORT environment variable)
EXPOSE 8080

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8080/_stcore/health || exit 1

# Run Streamlit
# --server.port uses PORT env var (Cloud Run sets this)
# --server.address 0.0.0.0 allows external connections
# --server.headless true runs without browser opening
CMD ["sh", "-c", "streamlit run Home.py --server.port=${PORT:-8080} --server.address=0.0.0.0 --server.headless=true"]
