FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install wheel for faster builds
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Install PyTorch CPU-only first (smaller download, faster build)
RUN pip install --no-cache-dir \
    --default-timeout=300 \
    --retries 5 \
    torch==2.2.0 \
    --index-url https://download.pytorch.org/whl/cpu

# Install remaining Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir \
    --default-timeout=300 \
    --retries 5 \
    -r requirements.txt

# Copy application code
COPY ./app ./app
COPY ./database ./database

# Expose port
EXPOSE 8000

# Run FastAPI app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
