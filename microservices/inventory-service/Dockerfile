# Optimized build for Inventory Service
FROM python:3.12-slim

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies (prefer pre-built wheels)
COPY requirements.txt .
RUN pip install --no-cache-dir --only-binary=:all: -r requirements.txt || \
    pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p staticfiles

EXPOSE 8006

ENV PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=inventory_service.settings

CMD python manage.py migrate --no-input && \
    python manage.py collectstatic --no-input && \
    gunicorn inventory_service.wsgi:application --bind 0.0.0.0:8006 --workers 4 --timeout 120
