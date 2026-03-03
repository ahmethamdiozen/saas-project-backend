FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for PyMuPDF and Psycopg2
RUN apt-get update && apt-get install -y 
    build-essential 
    libpq-dev 
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Environment variables setup (can be overridden by platform)
ENV PYTHONPATH=/app
ENV PORT=8000

# Default command (will be overridden in Railway for the worker)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
