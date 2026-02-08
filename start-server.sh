#!/bin/bash
# RemoveBG Pro - Server Startup Script

cd ~/projects/removebg-pro

# Kill any existing instance
pkill -f "uvicorn app:app" 2>/dev/null
sleep 2

# Start server in background
nohup python3 -m uvicorn app:app \
    --host 0.0.0.0 \
    --port 5000 \
    --log-level info \
    > /tmp/removebg-server.log 2>&1 &

# Wait for startup
sleep 3

# Check if running
if ss -tuln | grep -q 5000; then
    echo "✅ RemoveBG Pro started successfully!"
    echo "   Local: http://localhost:5000"
    echo "   Network: http://192.168.0.89:5000"
    echo ""
    echo "Logs: tail -f /tmp/removebg-server.log"
else
    echo "❌ Failed to start server"
    echo "Check logs: cat /tmp/removebg-server.log"
    exit 1
fi
