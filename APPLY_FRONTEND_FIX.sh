#!/bin/bash
echo "🔧 Applying frontend fixes for credit display..."
echo ""

cd /home/influ/projects/quicktools

echo "1️⃣ Rebuilding with updated app.js..."
sudo docker compose build web

echo ""
echo "2️⃣ Restarting..."
sudo docker compose restart web

echo ""
echo "3️⃣ Waiting for restart..."
sleep 3

echo ""
echo "4️⃣ Testing health..."
curl -s http://192.168.0.89:5000/api/health | python3 -m json.tool

echo ""
echo "✅ Done! Hard refresh your browser (Ctrl+Shift+R)"
echo "   Credits should now display correctly!"
