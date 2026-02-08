# RemoveBG Pro - Docker Deployment Guide

## 🚀 Production Deployment with Docker

This guide covers deploying RemoveBG Pro with full monetization features using Docker.

---

## 📋 Prerequisites

1. **Docker** installed (`docker --version`)
2. **Docker Compose** installed (`docker compose version`)
3. **Stripe account** (https://stripe.com)
4. **Domain name** (optional, for production)

---

## 🔧 Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/amreinch/removebg-pro.git
cd removebg-pro
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit with your values
nano .env
```

**Required configuration:**

```env
# JWT Secret (generate with: openssl rand -hex 32)
JWT_SECRET_KEY=your-generated-secret-key

# Stripe Keys (from https://dashboard.stripe.com/apikeys)
STRIPE_SECRET_KEY=sk_test_or_sk_live_your_key
STRIPE_PUBLISHABLE_KEY=pk_test_or_pk_live_your_key

# Stripe Price IDs (create products in Stripe Dashboard)
STRIPE_PRICE_BASIC=price_1234567890basic
STRIPE_PRICE_PRO=price_1234567890pro
STRIPE_PRICE_BUSINESS=price_1234567890business

# Frontend URL
FRONTEND_URL=http://your-domain.com
```

### 3. Build and Run

```bash
# Build the Docker image
docker compose build

# Start the service
docker compose up -d

# Check logs
docker compose logs -f
```

### 4. Verify Deployment

```bash
# Check if container is running
docker compose ps

# Test health endpoint
curl http://localhost:5000/api/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "service": "RemoveBG Pro API",
  "version": "2.0.0"
}
```

---

## 🔐 Stripe Setup

### 1. Create Stripe Account

Visit https://stripe.com and create account.

### 2. Create Products & Prices

In Stripe Dashboard → Products:

**Basic Plan:**
- Name: RemoveBG Pro Basic
- Price: $5/month
- Recurring: Monthly
- Copy the Price ID → Add to `.env` as `STRIPE_PRICE_BASIC`

**Pro Plan:**
- Name: RemoveBG Pro Pro
- Price: $15/month
- Recurring: Monthly
- Copy the Price ID → Add to `.env` as `STRIPE_PRICE_PRO`

**Business Plan:**
- Name: RemoveBG Pro Business
- Price: $50/month
- Recurring: Monthly
- Copy the Price ID → Add to `.env` as `STRIPE_PRICE_BUSINESS`

### 3. Configure Webhook

In Stripe Dashboard → Developers → Webhooks:

1. Click "Add endpoint"
2. Endpoint URL: `https://your-domain.com/api/webhook/stripe`
3. Select events:
   - `checkout.session.completed`
   - `customer.subscription.deleted`
   - `customer.subscription.updated`
4. Add endpoint
5. Copy signing secret (for production, add signature verification)

---

## 💾 Database Management

### SQLite (Default - Development)

Database stored in `removebg.db` file (persisted in Docker volume).

**Backup:**
```bash
docker compose cp web:/app/removebg.db ./backup.db
```

**Restore:**
```bash
docker compose cp ./backup.db web:/app/removebg.db
docker compose restart
```

### PostgreSQL (Production - Recommended)

Update `docker-compose.yml`:

```yaml
services:
  db:
    image: postgres:15
    container_name: removebg-db
    environment:
      POSTGRES_USER: removebg
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: removebg
    volumes:
      - pgdata:/var/lib/postgresql/data
    restart: unless-stopped

  web:
    depends_on:
      - db
    environment:
      - DATABASE_URL=postgresql://removebg:${DB_PASSWORD}@db:5432/removebg

volumes:
  pgdata:
```

---

## 🌐 Production Deployment Options

### Option 1: VPS (DigitalOcean, AWS, etc.)

**1. Provision Server:**
- 1GB RAM minimum (2GB recommended)
- Ubuntu 22.04 LTS
- Public IP address

**2. Install Docker:**
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

**3. Clone & Deploy:**
```bash
git clone https://github.com/amreinch/removebg-pro.git
cd removebg-pro
cp .env.example .env
nano .env  # Configure
docker compose up -d
```

**4. Setup Nginx Reverse Proxy:**
```bash
sudo apt install nginx

# Create config
sudo nano /etc/nginx/sites-available/removebg
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    client_max_body_size 10M;
}
```

```bash
sudo ln -s /etc/nginx/sites-available/removebg /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

**5. Add SSL (Let's Encrypt):**
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

---

### Option 2: Render.com (Easy Deploy)

1. Push code to GitHub (done ✓)
2. Go to https://render.com
3. New → Web Service
4. Connect GitHub repo
5. Configure:
   - **Build Command:** `docker build -t removebg .`
   - **Start Command:** `uvicorn app:app --host 0.0.0.0 --port $PORT`
   - **Environment:** Add all `.env` variables
6. Deploy!

**Free tier available**, auto SSL, global CDN.

---

### Option 3: Fly.io (Fast Global Deploy)

```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh

# Login
flyctl auth login

# Initialize
flyctl launch

# Deploy
flyctl deploy
```

Edit `fly.toml`:
```toml
[env]
  PORT = "5000"

[services]
  http_checks = []
  internal_port = 5000
  processes = ["app"]
  protocol = "tcp"
  
[[services.ports]]
  handlers = ["http"]
  port = 80

[[services.ports]]
  handlers = ["tls", "http"]
  port = 443
```

---

## 🔄 Updates & Maintenance

### Update Code

```bash
# Pull latest changes
git pull origin master

# Rebuild and restart
docker compose down
docker compose build
docker compose up -d
```

### View Logs

```bash
# All logs
docker compose logs -f

# Last 100 lines
docker compose logs --tail=100

# Specific service
docker compose logs -f web
```

### Restart Service

```bash
# Restart all
docker compose restart

# Restart specific service
docker compose restart web
```

### Stop Service

```bash
# Stop all
docker compose down

# Stop and remove volumes
docker compose down -v
```

---

## 📊 Monitoring

### Check Resource Usage

```bash
# Container stats
docker stats removebg-pro

# Disk usage
docker system df

# Container processes
docker top removebg-pro
```

### Health Checks

Add to `docker-compose.yml`:

```yaml
services:
  web:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

---

## 🔐 Security Best Practices

### 1. Environment Variables

**Never commit `.env` file!**

Generate secure secrets:
```bash
# JWT secret
openssl rand -hex 32

# Database password
openssl rand -base64 32
```

### 2. HTTPS Only (Production)

Update `docker-compose.yml`:
```yaml
environment:
  - FORCE_HTTPS=true
```

Add redirect in nginx config.

### 3. Rate Limiting

Install nginx rate limiting or use Cloudflare.

### 4. Firewall

```bash
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

### 5. Regular Backups

Automated daily backup script:

```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"

# Backup database
docker compose cp web:/app/removebg.db $BACKUP_DIR/removebg_$DATE.db

# Backup uploads (if needed)
tar -czf $BACKUP_DIR/uploads_$DATE.tar.gz uploads/

# Keep only last 7 days
find $BACKUP_DIR -name "removebg_*.db" -mtime +7 -delete
find $BACKUP_DIR -name "uploads_*.tar.gz" -mtime +7 -delete
```

Add to crontab:
```bash
0 2 * * * /path/to/backup.sh
```

---

## 🐛 Troubleshooting

### Container won't start

```bash
# Check logs
docker compose logs

# Check if port is in use
sudo lsof -i :5000

# Rebuild from scratch
docker compose down -v
docker compose build --no-cache
docker compose up -d
```

### Database errors

```bash
# Enter container
docker compose exec web /bin/bash

# Check database file
ls -la removebg.db

# Run Python shell
python3
>>> from database import init_db
>>> init_db()
```

### Stripe webhook not working

1. Check webhook URL is accessible publicly
2. Verify webhook secret in Stripe Dashboard
3. Check webhook logs in Stripe Dashboard
4. Add signature verification in production

---

## 📈 Scaling

### Horizontal Scaling

Use multiple instances with shared database:

```yaml
services:
  web:
    deploy:
      replicas: 3
    
  loadbalancer:
    image: nginx:alpine
    ports:
      - "80:80"
    depends_on:
      - web
```

### Caching

Add Redis for session/response caching.

### CDN

Use Cloudflare for static assets and processed images.

---

## 💰 Cost Estimate

**Minimum (Development):**
- VPS (1GB): $5-6/mo (DigitalOcean, Linode)
- Domain: $10-15/year
- **Total: ~$8/month**

**Production (Growing):**
- VPS (2GB): $12-18/mo
- PostgreSQL managed: $15/mo
- Cloudflare (free tier): $0
- **Total: ~$30/month**

**Scaling (1000+ users):**
- VPS (4GB) or App Platform: $30-50/mo
- Database: $25-50/mo
- CDN/Storage: $10-30/mo
- **Total: ~$100/month**

---

## ✅ Deployment Checklist

- [ ] Environment variables configured
- [ ] Stripe account created & configured
- [ ] Products & prices created in Stripe
- [ ] Webhook endpoint configured
- [ ] Docker containers running
- [ ] Health check passing
- [ ] SSL certificate installed
- [ ] Domain configured
- [ ] Backups automated
- [ ] Monitoring setup
- [ ] Firewall configured
- [ ] Testing complete

---

**Your RemoveBG Pro instance is now production-ready! 🚀**

Access: http://your-domain.com
API Docs: http://your-domain.com/docs
