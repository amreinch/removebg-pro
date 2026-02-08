#!/bin/bash
# QuickTools - Local Docker Deployment
set -e

echo "🚀 Deploying QuickTools locally with Docker..."
echo ""

cd "$(dirname "$0")"

# Stop any existing containers
echo "🛑 Stopping existing containers..."
sudo docker compose down 2>/dev/null || true

# Build and start
echo "🔨 Building Docker image..."
sudo docker compose build

echo "🚀 Starting containers..."
sudo docker compose up -d

echo ""
echo "✅ QuickTools is now running!"
echo ""
echo "📍 Access at: http://192.168.0.89:5000"
echo ""
echo "📊 View logs: sudo docker compose logs -f"
echo "🛑 Stop: sudo docker compose down"
echo "🔄 Restart: sudo docker compose restart"
echo ""
