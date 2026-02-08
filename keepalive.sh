#!/bin/bash
# RemoveBG Pro - Keepalive Monitor
# Run this in background to auto-restart if server crashes

while true; do
    # Check if server is running
    if ! ss -tuln | grep -q ":5000 "; then
        echo "[$(date)] Server not running, restarting..."
        
        cd ~/projects/removebg-pro
        pkill -f "uvicorn app:app" 2>/dev/null
        sleep 2
        
        nohup python3 -m uvicorn app:app \
            --host 0.0.0.0 \
            --port 5000 \
            --log-level info \
            > /tmp/removebg-server.log 2>&1 &
        
        sleep 5
        
        if ss -tuln | grep -q ":5000 "; then
            echo "[$(date)] Server restarted successfully"
        else
            echo "[$(date)] Failed to restart server"
        fi
    fi
    
    # Check every 30 seconds
    sleep 30
done
