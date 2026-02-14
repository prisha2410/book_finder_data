FROM python:3.12-slim

WORKDIR /app

# Install system deps (important for lxml, torch)
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 7860

# FIXED: Changed from "app:app" to "api.app:app"
CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "7860"]