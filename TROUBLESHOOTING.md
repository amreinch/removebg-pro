# RemoveBG Pro - Troubleshooting Guide

## 🔧 Can't Access from Remote Browser

### Step 1: Verify Server is Running

```bash
# Check if port 5000 is listening
ss -tuln | grep 5000

# Expected output:
# tcp   LISTEN 0      2048     0.0.0.0:5000     0.0.0.0:*
```

If no output, the server is **not running**. Start it:

```bash
cd ~/projects/removebg-pro
./start-server.sh
```

---

### Step 2: Test Local Access

```bash
# From the server machine
curl http://localhost:5000/api/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "service": "RemoveBG Pro API",
  "version": "1.0.0"
}
```

If this works but remote doesn't, it's a **network issue**.

---

### Step 3: Test Network Access

```bash
# From the server machine, test via local IP
curl http://192.168.0.89:5000/api/health
```

If this works, the server is fine. The issue is on your **client side** or **network**.

---

### Step 4: Check from Another Device

**From your remote computer/phone:**

1. Make sure you're on the **same network** (same WiFi/LAN)
2. Try accessing: http://192.168.0.89:5000
3. Try the health endpoint: http://192.168.0.89:5000/api/health

**If it doesn't work:**

#### Option A: Check Client Device
- Clear browser cache
- Try different browser (Chrome, Firefox, Safari)
- Disable browser extensions
- Try incognito/private mode
- Check if device can ping the server: `ping 192.168.0.89`

#### Option B: Check Network
- Verify both devices are on same network
- Check WiFi router settings (client isolation disabled?)
- Try from different device on same network
- Restart WiFi router

#### Option C: Check Server Firewall

```bash
# Check if firewall is blocking
sudo ufw status

# If active, allow port 5000
sudo ufw allow 5000/tcp
sudo ufw reload
```

---

### Step 5: Verify Server Binding

Check that server is listening on **all interfaces** (0.0.0.0), not just localhost (127.0.0.1):

```bash
ss -tuln | grep 5000

# ✅ Good: 0.0.0.0:5000 (accessible from network)
# ❌ Bad: 127.0.0.1:5000 (localhost only)
```

If showing 127.0.0.1, restart with correct binding:

```bash
cd ~/projects/removebg-pro
./start-server.sh
```

---

### Step 6: Check Server Logs

```bash
tail -50 /tmp/removebg-server.log
```

Look for errors like:
- Port already in use
- Permission denied
- Module not found
- Binding failures

---

## 🐛 Common Issues

### "Connection Refused"
**Cause:** Server not running or firewall blocking

**Fix:**
```bash
# Start server
cd ~/projects/removebg-pro
./start-server.sh

# Check firewall
sudo ufw allow 5000/tcp
```

---

### "Connection Timeout"
**Cause:** Network routing issue or different networks

**Fix:**
- Verify both devices on same WiFi/LAN
- Check router settings (disable AP isolation)
- Try connecting via Ethernet instead of WiFi
- Restart router

---

### "404 Not Found"
**Cause:** Wrong URL or server routing issue

**Fix:**
- Use correct URL: http://192.168.0.89:5000
- Don't add /index.html or other paths
- Try /api/health endpoint first

---

### "500 Internal Server Error"
**Cause:** Backend error during processing

**Fix:**
```bash
# Check logs
tail -100 /tmp/removebg-server.log

# Common causes:
# - Missing dependencies
# - File permission issues
# - Out of memory
```

---

### Server Keeps Stopping
**Cause:** Process crashes or system kills it

**Fix:**
Use the keepalive monitor:

```bash
cd ~/projects/removebg-pro
nohup ./keepalive.sh > /tmp/removebg-keepalive.log 2>&1 &
```

This will auto-restart the server if it crashes.

---

## 🌐 Accessing from Internet (Outside Your Network)

Currently, RemoveBG Pro is only accessible on your **local network**. To access from internet:

### Option 1: ngrok (Easiest, Free)

```bash
# Install ngrok
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | \
  sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | \
  sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update && sudo apt install ngrok

# Get free auth token from https://dashboard.ngrok.com/get-started/your-authtoken
ngrok config add-authtoken YOUR_TOKEN_HERE

# Create tunnel
ngrok http 5000
```

You'll get a public URL like: `https://abc123.ngrok.io`

**Pros:** Instant, free, easy  
**Cons:** URL changes each restart (pay for static)

---

### Option 2: Cloudflare Tunnel (Free, Permanent)

```bash
# Install cloudflared
curl -L --output cloudflared.deb \
  https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared.deb

# Login to Cloudflare
cloudflared tunnel login

# Create tunnel
cloudflared tunnel create removebg-pro

# Configure tunnel
cloudflared tunnel --url http://localhost:5000 run removebg-pro
```

**Pros:** Free, permanent, secure  
**Cons:** Requires Cloudflare account and domain

---

### Option 3: Port Forwarding (Your Router)

1. Login to router admin (usually http://192.168.0.1 or http://192.168.1.1)
2. Find "Port Forwarding" or "Virtual Server" section
3. Add rule:
   - External port: 5000
   - Internal IP: 192.168.0.89
   - Internal port: 5000
   - Protocol: TCP
4. Find your public IP: https://whatismyip.com
5. Access via: http://YOUR_PUBLIC_IP:5000

⚠️ **Security Warning:** Add authentication before exposing publicly!

**Pros:** Full control, no third party  
**Cons:** Requires router access, security risk, dynamic IP

---

## 📊 Diagnostic Commands

### Full Status Check

```bash
#!/bin/bash
echo "=== RemoveBG Pro Status ==="
echo ""

echo "1. Server Process:"
ps aux | grep uvicorn | grep -v grep || echo "   ❌ Not running"
echo ""

echo "2. Port Listening:"
ss -tuln | grep 5000 || echo "   ❌ Port 5000 not listening"
echo ""

echo "3. Local Access:"
curl -s http://localhost:5000/api/health || echo "   ❌ Failed"
echo ""

echo "4. Network Access:"
curl -s http://192.168.0.89:5000/api/health || echo "   ❌ Failed"
echo ""

echo "5. Firewall Status:"
sudo ufw status 2>/dev/null || echo "   UFW not active"
echo ""

echo "6. Recent Logs:"
tail -20 /tmp/removebg-server.log
```

Save as `diagnostic.sh`, make executable, and run:

```bash
chmod +x diagnostic.sh
./diagnostic.sh
```

---

## 🔍 Network Debugging

### Test from Client Device

**Windows:**
```cmd
curl http://192.168.0.89:5000/api/health
# or
telnet 192.168.0.89 5000
```

**Mac/Linux:**
```bash
curl http://192.168.0.89:5000/api/health
# or
nc -zv 192.168.0.89 5000
```

**Phone:**
- Open browser to: http://192.168.0.89:5000
- If using iOS/Android, ensure on same WiFi network

---

### Check Router Configuration

Common router issues:
1. **AP Isolation / Client Isolation:** Prevents devices from talking to each other
   - Usually in WiFi settings
   - Disable it for local network access

2. **Guest Network:** If client is on guest WiFi, it may be isolated
   - Move to main WiFi network

3. **Firewall Rules:** Some routers block certain ports
   - Check router firewall settings
   - Add allow rule for port 5000

---

## 💡 Quick Fixes

### "It was working yesterday"

```bash
# Restart everything
cd ~/projects/removebg-pro
./start-server.sh
```

---

### "Works on server but not remote"

```bash
# Verify server binding
ss -tuln | grep 5000
# Should show 0.0.0.0:5000, not 127.0.0.1:5000

# If wrong, restart with correct binding
./start-server.sh
```

---

### "Slow or hanging"

```bash
# Check CPU/memory
htop

# Check disk space
df -h

# Restart server
./start-server.sh
```

---

## 📞 Still Not Working?

1. **Check server logs:** `tail -100 /tmp/removebg-server.log`
2. **Run diagnostics:** `./diagnostic.sh`
3. **Test simple server:** `python3 -m http.server 8080` and try accessing http://192.168.0.89:8080
4. **Verify Python version:** `python3 --version` (need 3.8+)
5. **Reinstall dependencies:** `pip install -r requirements.txt --break-system-packages --force-reinstall`

---

**Current Status:**
- Server IP: 192.168.0.89
- Port: 5000
- URL: http://192.168.0.89:5000
- Logs: /tmp/removebg-server.log
