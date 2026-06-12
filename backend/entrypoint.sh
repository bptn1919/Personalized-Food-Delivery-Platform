#!/bin/sh
set -e  # Dừng nếu có lỗi

echo "🚀 Running migrations..."
python manage.py migrate --noinput

echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

echo "✅ Starting server..."
exec "$@"