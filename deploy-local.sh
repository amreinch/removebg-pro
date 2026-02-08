#!/bin/bash
# QuickTools - Local Docker Deployment with PostgreSQL
set -e

echo "🚀 Deploying QuickTools locally with Docker + PostgreSQL..."
echo ""

cd "$(dirname "$0")"

# Stop any existing containers
echo "🛑 Stopping existing containers..."
docker compose down 2>/dev/null || true

# Build and start
echo "🔨 Building Docker image..."
docker compose build

echo "🐘 Starting PostgreSQL..."
docker compose up -d db

echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 5

# Check if migration is needed
if [ -f "quicktools.db" ]; then
    echo "📦 SQLite database found. Migrating to PostgreSQL..."
    python3 migrate_sqlite_to_postgres.py
    if [ $? -eq 0 ]; then
        echo "✅ Migration successful!"
        echo "📦 Backing up SQLite database..."
        mv quicktools.db quicktools.db.backup
        echo "✅ SQLite backed up to quicktools.db.backup"
    else
        echo "❌ Migration failed!"
        exit 1
    fi
fi

echo "🚀 Starting QuickTools app..."
docker compose up -d web

echo ""
echo "✅ QuickTools is now running with PostgreSQL!"
echo ""
echo "📍 Access at: http://192.168.0.89:5000"
echo "🐘 PostgreSQL: localhost:5432"
echo ""
echo "📊 View logs: docker compose logs -f"
echo "🛑 Stop: docker compose down"
echo "🔄 Restart: docker compose restart"
echo "💾 Backup DB: docker exec quicktools-db pg_dump -U quicktools quicktools > backup.sql"
echo ""
