FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir=/wheels -r requirements.txt

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY --from=builder /wheels /wheels
RUN pip install --no-cache /wheels/*

COPY . .

ENV DJANGO_SETTINGS_MODULE=settings \
    PORT=8000

EXPOSE 8000

# Run DB migrations, then start Gunicorn. Use $PORT if provided (Render), else 8000 locally.
CMD ["sh","-c","python manage.py migrate --noinput && gunicorn wsgi:application --bind 0.0.0.0:${PORT:-8000}"]
