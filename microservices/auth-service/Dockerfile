# Optimized build for Auth Service
FROM python:3.12-slim

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies (prefer pre-built wheels)
COPY requirements.txt .
RUN pip install --no-cache-dir --only-binary=:all: -r requirements.txt || \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directory for static files
RUN mkdir -p staticfiles

# Expose port
EXPOSE 8001

# Environment variable for Django
ENV PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=auth_service.settings

# Run migrations and start Gunicorn
CMD python manage.py migrate --no-input && \
    python manage.py collectstatic --no-input && \
    gunicorn auth_service.wsgi:application --bind 0.0.0.0:8001 --workers 4 --timeout 120
