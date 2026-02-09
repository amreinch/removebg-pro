# Production Deployment Guide

**Date:** 2026-02-09  
**Status:** Clean deployment, no migrations needed  
**Stack:** Docker Compose + PostgreSQL

---

## 🚀 Fresh Production Deployment

### Prerequisites

1. **Server Requirements:**
   - Docker & Docker Compose installed
   - Domain name pointing to server
   - SSL certificate (Let's Encrypt recommended)
   - Ports 80, 443, 5432 available

2. **Environment Setup:**
   - Create `.env` file with production values

---

## Step 1: Clone & Configure

### On Production Server

```bash
# Clone repository
git clone https://github.com/amreinch/removebg-pro.git quicktools
cd quicktools

# Create production .env file
nano .env
```

### Production .env File

```env
# Database
DB_PASSWORD=YOUR_STRONG_PASSWORD_HERE

# JWT Secret (generate with: openssl rand -hex 32)
JWT_SECRET_KEY=YOUR_RANDOM_SECRET_KEY_HERE

# Stripe (Production Keys)
STRIPE_SECRET_KEY=sk_live_YOUR_KEY
STRIPE_PUBLISHABLE_KEY=pk_live_YOUR_KEY

# Frontend URL
FRONTEND_URL=https://yourdomain.com
```

**Important:** Never commit `.env` to git!

---

## Step 2: Deploy with Docker Compose

```bash
# Build and start
docker compose up -d

# That's it! 
```

### What Happens Automatically

**1. PostgreSQL Container Starts:**
- Creates fresh database volume
- Initializes PostgreSQL
- Waits for health check

**2. App Container Starts:**
- Waits for PostgreSQL to be healthy
- Connects to PostgreSQL
- **Calls `init_db()` on startup**

**3. init_db() Auto-Creates Tables:**
```python
def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
```

This reads `models.py` and creates tables based on **current schema**.

**Result:** Tables created with **credit pack schema** (no subscription fields) ✅

---

## Step 3: Verify Deployment

### Check Containers Running

```bash
docker compose ps

# Should show:
# quicktools-db    postgres:16-alpine   Up (healthy)
# quicktools       quicktools_web       Up
```

### Check Health Endpoint

```bash
curl https://yourdomain.com/api/health

# Should return:
{
  "status": "healthy",
  "service": "RemoveBG Pro API",
  "version": "2.0.0",
  "timestamp": "..."
}
```

### Check Database Schema

```bash
# Connect to PostgreSQL
docker exec -it quicktools-db psql -U quicktools -d quicktools

# Check users table
\d users

# Should see:
# - credits_balance
# - credits_purchased_total
# - api_access_unlocked
# 
# Should NOT see:
# - subscription_tier
# - monthly_credits
# - credits_used_this_month
```

---

## Step 4: Setup Stripe Webhook

### In Stripe Dashboard

1. Go to: **Developers → Webhooks**
2. Click: **Add endpoint**
3. URL: `https://yourdomain.com/api/webhook/stripe`
4. Events to listen for:
   - `checkout.session.completed`
5. Save and copy **Signing Secret**

### Update .env

```bash
# Add to .env
STRIPE_WEBHOOK_SECRET=whsec_YOUR_SIGNING_SECRET
```

### Restart to Apply

```bash
docker compose restart web
```

---

## Step 5: Test Payment Flow

### Create Test User

```bash
# Visit your site
https://yourdomain.com

# Click "Get Started"
# Sign up with your email
# You get 10 free credits automatically
```

### Test Payment (Stripe Test Mode First!)

1. Use test Stripe keys first (`sk_test_...`)
2. Buy a credit pack
3. Use test card: `4242 4242 4242 4242`
4. Verify credits added to account
5. Switch to live keys when ready

---

## 🔄 Updates & Maintenance

### Deploying Code Updates

```bash
# On production server
cd quicktools
git pull
docker compose build
docker compose up -d
```

**No database migration needed** - schema is already correct!

### Database Backups

```bash
# Backup PostgreSQL
docker exec quicktools-db pg_dump -U quicktools quicktools > backup.sql

# Restore if needed
docker exec -i quicktools-db psql -U quicktools quicktools < backup.sql
```

### View Logs

```bash
# All logs
docker compose logs -f

# Just app
docker compose logs -f web

# Just database
docker compose logs -f db
```

---

## 🎯 Why No Migration Needed?

### For Fresh Deployments

**This is your first deployment**, so:
- PostgreSQL starts empty ✅
- `init_db()` creates tables from `models.py` ✅
- `models.py` has **only credit pack fields** ✅
- Tables created with **correct schema** ✅

**No migration needed!** ✨

### The "Fix Script" Was Only For Dev

The `PROPER_FIX.sh` script was needed because:
- ❌ Dev environment had **old PostgreSQL** with subscription schema
- ❌ We updated code but not the database
- ✅ Script deleted old database and started fresh

**Production doesn't have this problem** - fresh deployment!

---

## 🏗️ Architecture Overview

```
Production Stack:

Internet
  │
  ↓
Nginx/Caddy (SSL termination)
  │
  ↓
Docker Compose
  ├─ PostgreSQL Container
  │    └─ Volume: postgres_data (persistent)
  │
  └─ QuickTools API Container
       ├─ Python/FastAPI
       ├─ Volume: uploads (persistent)
       └─ Volume: outputs (persistent)
```

---

## 📊 Database Schema (Auto-Created)

### Users Table (Credit Pack Model)

```sql
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    full_name TEXT,
    
    -- Credit Pack System
    credits_balance INTEGER DEFAULT 10,
    credits_purchased_total INTEGER DEFAULT 0,
    credits_lifetime_used INTEGER DEFAULT 0,
    api_access_unlocked BOOLEAN DEFAULT FALSE,
    
    -- Stripe
    stripe_customer_id TEXT,
    last_purchase_date TIMESTAMP,
    last_purchase_amount INTEGER,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);
```

**No subscription fields!** ✅

---

## 🔐 Security Checklist

Before going live:

- [ ] Strong `DB_PASSWORD` in .env
- [ ] Random `JWT_SECRET_KEY` (32+ chars)
- [ ] Stripe live keys (not test keys)
- [ ] SSL certificate installed
- [ ] Firewall configured (only 80/443 open)
- [ ] `.env` not committed to git
- [ ] Stripe webhook signature verification enabled
- [ ] Database backups automated

---

## 🚨 Troubleshooting

### "Internal Server Error" on Login

**Check:** Database schema
```bash
docker exec -it quicktools-db psql -U quicktools -d quicktools -c "\d users"
```

**Should see:** credits_balance, api_access_unlocked  
**Should NOT see:** subscription_tier, monthly_credits

**If wrong schema:** Database didn't auto-create properly
```bash
# Drop and recreate (ONLY if empty database!)
docker compose down -v
docker compose up -d
```

### "Can't connect to database"

**Check:** PostgreSQL running
```bash
docker compose ps
docker compose logs db
```

**Check:** DATABASE_URL correct in .env

### "Stripe webhook failed"

**Check:** Webhook signature secret in .env  
**Check:** Webhook URL correct in Stripe dashboard  
**Check:** Server reachable from internet

---

## 📝 Summary

### For Fresh Production Deployment:

1. ✅ Clone code
2. ✅ Create `.env` with production values
3. ✅ Run `docker compose up -d`
4. ✅ Tables auto-create with correct schema
5. ✅ Setup Stripe webhook
6. ✅ Test payment flow
7. ✅ Launch! 🚀

**No migration scripts needed!**

**No manual database setup!**

**Everything automatic!**

---

## 🎉 Result

**First startup:**
- PostgreSQL creates fresh database
- App starts and calls `init_db()`
- SQLAlchemy reads `models.py`
- Tables created with **credit pack schema**
- Ready to use immediately

**Clean, simple, production-ready!**

---

**Deployment time:** ~5 minutes  
**Complexity:** Low  
**Manual steps:** Minimal  
**Result:** Production-ready SaaS platform! 🚀
