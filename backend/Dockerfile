# ================= BACKEND DOCKERFILE =================
# ========== DEPENDENCIES STAGE ==========
FROM python:3.12-slim AS deps
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create env directory for .env files
RUN mkdir -p /app/env


# ========== BUILDER STAGE ==========
FROM deps AS builder
WORKDIR /app

# Build-time arguments (not stored in final image)
ARG SECRET_KEY=dummy-key-for-build-only
ARG MONGO_URI=mongodb://mongodb:27017

# Set environment for collectstatic
ENV MONGO_URI=$MONGO_URI

# Copy source code
COPY . .

# Create entrypoint script
RUN echo '#!/bin/sh\n\
set -e\n\
\n\
echo "🚀 Running database migrations..."\n\
python manage.py migrate --noinput\n\
\n\
echo "📁 Collecting static files..."\n\
python manage.py collectstatic --noinput\n\
\n\
echo "✅ Starting server..."\n\
exec "$@"\n\
' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Collect static files (requires SECRET_KEY to be set)
RUN SECRET_KEY=${SECRET_KEY} python manage.py collectstatic --noinput --settings=marketplace.settings

# Ensure staticfiles folder exists
RUN mkdir -p /app/staticfiles || true


# ========== DEVELOPMENT STAGE ==========
FROM python:3.12-slim AS dev
WORKDIR /app

# Install system dependencies for development
RUN apt-get update && apt-get install -y \
    curl \
    git \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from deps stage
COPY --from=deps /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

# Copy source code and static files from builder
COPY --from=builder /app/env /app/env
COPY --from=builder /app/entrypoint.sh /app/entrypoint.sh
COPY . .

RUN chmod +x /app/entrypoint.sh

EXPOSE 8000

# Run with Django development server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]


# ========== PRODUCTION STAGE ==========
FROM python:3.12-slim AS prod
WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    libpq5 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder stage
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy the application from builder stage
COPY --from=builder /app .
COPY --from=builder /app/entrypoint.sh /app/entrypoint.sh

RUN chmod +x /app/entrypoint.sh

EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=3s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:8000/ || exit 1

# Use entrypoint script for migrations
ENTRYPOINT ["/app/entrypoint.sh"]

# Run with daphne
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "marketplace.asgi:application"]