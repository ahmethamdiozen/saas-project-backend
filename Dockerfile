FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Set permissions for Hugging Face (they use user 1000)
RUN chmod +x start.sh && chown -R 1000:1000 /app

# Switch to HF User
USER 1000

ENV PYTHONPATH=/app
ENV PORT=7860

CMD ["./start.sh"]
