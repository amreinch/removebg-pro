#!/bin/bash
# Restart QuickTools with code reload

echo "🔄 Stopping containers..."
docker compose down

echo "🔨 Rebuilding with latest code..."
docker compose build --no-cache

echo "🚀 Starting containers..."
docker compose up -d

echo "⏳ Waiting for health check..."
sleep 3

echo "✅ Testing API..."
curl -s http://192.168.0.89:5000/api/health | python3 -m json.tool

echo ""
echo "Done! Try logging in now."
