#!/bin/bash
echo "🔧 Fixing login issue..."
echo ""
echo "Issue: Docker was using PostgreSQL, we migrated SQLite"
echo "Fix: Switching Docker to use SQLite (quicktools.db)"
echo ""

echo "1️⃣ Stopping containers..."
cd /home/influ/projects/quicktools
sudo docker compose down

echo ""
echo "2️⃣ Rebuilding with new database config..."
sudo docker compose build

echo ""
echo "3️⃣ Starting with SQLite..."
sudo docker compose up -d

echo ""
echo "4️⃣ Waiting for server..."
sleep 5

echo ""
echo "5️⃣ Testing health..."
curl -s http://192.168.0.89:5000/api/health | python3 -m json.tool

echo ""
echo "6️⃣ Testing login..."
curl -s -X POST http://192.168.0.89:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"christoph.amrein86@gmail.com","password":"test123456"}' | python3 -m json.tool

echo ""
echo "✅ Done! Try logging in now."
