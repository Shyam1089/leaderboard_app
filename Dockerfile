FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    redis-server \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBUG=True
ENV ALLOWED_HOSTS=*
ENV CELERY_BROKER_URL=redis://localhost:6379/0
ENV CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Configure Supervisor
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Create staticfiles directory and collect static files
RUN mkdir -p staticfiles
RUN python manage.py collectstatic --noinput
RUN chmod -R 755 staticfiles

# Run migrations and create initial users
RUN python manage.py makemigrations api && \
    python manage.py migrate && \
    python manage.py populate_db --count 10

# Expose port
EXPOSE 8080

# Start Supervisor (which will start Redis, Django, and Celery)
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"] 