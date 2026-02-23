# Docker Build Troubleshooting Guide

## Issue: Timeout During Package Installation

If you encounter timeout errors during `docker build`, this is usually due to large packages like PyTorch.

## Solutions

### Option 1: Use the Optimized Dockerfile (Recommended)
The current Dockerfile is optimized with:
- **Increased timeout**: 300 seconds (5 minutes)
- **Retry logic**: 5 retries on failure
- **CPU-only PyTorch**: ~200MB instead of ~800MB
- **Separate PyTorch installation**: Installed before other packages

### Option 2: Build Without Cache
If the build fails partway through, try building without cache:
```bash
docker-compose build --no-cache
```

### Option 3: Increase Docker Build Timeout
Add to your `docker-compose.yml`:
```yaml
services:
  app:
    build:
      context: .
      args:
        BUILDKIT_INLINE_CACHE: 1
    environment:
      - PIP_DEFAULT_TIMEOUT=600
```

### Option 4: Use Pre-built Base Image
Create a base image with dependencies pre-installed, then build your app on top.

### Option 5: Install Locally First
If Docker keeps timing out, install locally and test:
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install PyTorch CPU
pip install torch==2.2.0 --index-url https://download.pytorch.org/whl/cpu

# Install other requirements
pip install -r requirements.txt

# Run locally
uvicorn app.main:app --reload
```

### Option 6: Use Different PyTorch Source
If the PyTorch CDN is slow in your region, you can modify the Dockerfile to use a mirror or different version.

## Current Optimizations Applied

✅ **CPU-only PyTorch**: Reduced from ~800MB to ~200MB  
✅ **Increased timeout**: 300 seconds per package  
✅ **Retry logic**: 5 automatic retries  
✅ **Separate installation**: PyTorch installed first to isolate issues  
✅ **Upgraded pip**: Latest pip with better dependency resolution  

## Testing the Build

```bash
# Try building again
docker-compose build

# If it still fails, try without cache
docker-compose build --no-cache

# Monitor the build progress
docker-compose build --progress=plain
```
