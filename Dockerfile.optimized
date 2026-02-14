FROM python:3.12-slim

WORKDIR /app

# Install minimal system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy optimized requirements (CPU-only PyTorch!)
COPY requirements_optimized.txt .

# Install with pip (CPU-only torch saves ~150MB)
RUN pip install --no-cache-dir -r requirements_optimized.txt

# Copy application
COPY . .

# Set environment variables for memory optimization
ENV PYTHONUNBUFFERED=1
ENV MALLOC_TRIM_THRESHOLD_=100000
ENV MALLOC_MMAP_THRESHOLD_=100000

EXPOSE 7860

# Use OPTIMIZED version with memory-efficient search
CMD ["uvicorn", "api.app_optimized:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]