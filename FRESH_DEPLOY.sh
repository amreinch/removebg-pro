#!/bin/bash
set -e

echo "🗑️  Fresh Deployment - Wiping Everything"
echo ""

cd /home/influ/projects/quicktools

echo "1️⃣ Stopping all containers..."
sudo docker compose down -v
echo "   ✅ Containers stopped, volumes deleted"

echo ""
echo "2️⃣ Rebuilding containers..."
sudo docker compose build --no-cache
echo "   ✅ Fresh build complete"

echo ""
echo "3️⃣ Starting fresh deployment..."
sudo docker compose up -d
echo "   ✅ Containers starting..."

echo ""
echo "4️⃣ Waiting for PostgreSQL to initialize..."
sleep 15

echo ""
echo "5️⃣ Checking health..."
curl -s http://192.168.0.89:5000/api/health | python3 -m json.tool

echo ""
echo "6️⃣ Checking database schema (should have credit pack fields)..."
sudo docker exec quicktools-db psql -U quicktools -d quicktools -c "\d users" 2>/dev/null || echo "   Tables will be created on first API call"

echo ""
echo "✅ Fresh deployment complete!"
echo ""
echo "📊 Database Status:"
echo "   - PostgreSQL: Fresh and empty"
echo "   - Schema: Will auto-create on first use"
echo "   - Users: 0 (ready for signups)"
echo ""
echo "🎯 Next Steps:"
echo "   1. Visit: http://192.168.0.89:5000/static/index.html"
echo "   2. Click 'Get Started' to create your first user"
echo "   3. You'll get 10 free credits automatically"
echo ""
echo "🎉 Ready for production!"
