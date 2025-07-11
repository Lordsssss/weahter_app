FROM python:3.11-alpine

WORKDIR /app

# Install system dependencies
RUN apk add --no-cache \
    gcc \
    musl-dev \
    && rm -rf /var/cache/apk/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY config/ ./config/
COPY .env.example .env

# Create directories
RUN mkdir -p logs data

# Set Python path
ENV PYTHONPATH=/app/src

# Run the weather monitor
CMD ["python", "-m", "weather_monitor.cli", "start"]