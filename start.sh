#!/bin/bash

echo "🚀 Starting PlaygreSQL Development Environment..."
echo ""

# Build and start containers
echo "📦 Building containers..."
docker compose up --build -d

# Wait for database to be ready
echo ""
echo "⏳ Waiting for database to be ready..."
sleep 5

# Check database health
echo ""
echo "🔍 Checking database health..."
docker compose exec db pg_isready -U postgres

# Show enabled extensions
echo ""
echo "🔌 Enabled PostgreSQL extensions:"
docker compose exec db psql -U postgres -d playgresql -c "SELECT extname, extversion FROM pg_extension WHERE extname IN ('postgis', 'timescaledb', 'vector');"

# Run migrations
echo ""
echo "🔄 Running Django migrations..."
docker compose exec web uv run python manage.py migrate

echo ""
echo "✅ Environment ready!"
echo ""
echo "📍 Services:"
echo "   - Django: http://localhost:8000"
echo "   - PostgreSQL: postgresql://postgres:postgres@localhost:5432/playgresql"
echo ""
echo "💡 Quick commands:"
echo "   - Django shell:  docker compose exec web uv run python manage.py shell"
echo "   - Database shell: docker compose exec db psql -U postgres -d playgresql"
echo "   - View logs: docker compose logs -f"
echo "   - Stop: docker compose down"
echo ""
