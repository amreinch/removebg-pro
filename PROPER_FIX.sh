#!/bin/bash
set -e

echo "🔧 Proper Fix: PostgreSQL in Docker with Clean Schema"
echo ""

cd /home/influ/projects/quicktools

echo "1️⃣ Stopping containers..."
sudo docker compose down -v  # -v removes volumes (fresh DB)

echo ""
echo "2️⃣ Rebuilding containers with updated code..."
sudo docker compose build --no-cache

echo ""
echo "3️⃣ Starting PostgreSQL + App..."
sudo docker compose up -d

echo ""
echo "4️⃣ Waiting for PostgreSQL to be ready..."
sleep 10

echo ""
echo "5️⃣ Database will auto-initialize with NEW schema (no subscription fields)"
echo "   SQLAlchemy creates tables from models.py"

echo ""
echo "6️⃣ Creating your user account..."
sudo docker exec -it quicktools python3 -c "
from database import SessionLocal, init_db
from models import User
from auth import hash_password
init_db()
db = SessionLocal()
user = User(
    email='christoph.amrein86@gmail.com',
    hashed_password=hash_password('test123456'),
    credits_balance=1000,
    api_access_unlocked=True
)
db.add(user)
db.commit()
print('✅ User created: christoph.amrein86@gmail.com with 1000 credits')
" 2>&1 || echo "User might already exist, continuing..."

echo ""
echo "7️⃣ Testing health..."
sleep 2
curl -s http://192.168.0.89:5000/api/health | python3 -m json.tool

echo ""
echo "8️⃣ Testing login..."
curl -s -X POST http://192.168.0.89:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"christoph.amrein86@gmail.com","password":"test123456"}' | python3 -m json.tool

echo ""
echo "✅ Done! PostgreSQL in Docker with clean schema."
