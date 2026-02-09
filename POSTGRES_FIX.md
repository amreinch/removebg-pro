# PostgreSQL Docker Fix

**Date:** 2026-02-09  
**Issue:** Login broken after migration  
**Root Cause:** PostgreSQL still has old subscription schema  
**Solution:** Fresh PostgreSQL with new schema

---

## What Happened

1. ✅ We removed subscription code from Python files
2. ✅ We migrated SQLite database (quicktools.db)
3. ❌ **PostgreSQL in Docker still has old schema**
4. ❌ Docker tries to use old schema → crashes on login

---

## The Proper Fix

### Option 1: Quick Fix (Recommended)

**Drop and recreate PostgreSQL with clean schema:**

```bash
cd /home/influ/projects/quicktools
./PROPER_FIX.sh
```

This will:
- Stop containers
- **Delete PostgreSQL volume** (fresh start)
- Rebuild with new code
- Start with clean database
- Auto-create tables with NEW schema (no subscription fields)
- Recreate your user account (1000 credits, API unlocked)

**Time:** ~30 seconds  
**Risk:** None (fresh database, no data loss since we're in dev)

---

### Option 2: Manual Steps

```bash
# Stop everything
cd /home/influ/projects/quicktools
sudo docker compose down -v  # -v removes volumes

# Rebuild
sudo docker compose build --no-cache

# Start fresh
sudo docker compose up -d

# Wait for PostgreSQL
sleep 10

# Tables will auto-create with NEW schema
# Create your user via API or psql
```

---

## Why This Works

**Before:**
```
PostgreSQL has:
  - subscription_tier (old)
  - monthly_credits (old)
  - credits_used_this_month (old)
  
Python models expect:
  - credits_balance (new)
  - api_access_unlocked (new)
  
Result: MISMATCH → Error
```

**After:**
```
PostgreSQL gets:
  - credits_balance (new)
  - api_access_unlocked (new)
  
Python models expect:
  - credits_balance (new)
  - api_access_unlocked (new)
  
Result: MATCH → Works!
```

---

## What About My Data?

**Development data:** Lost (but it's just test data)  
**Production:** Would use proper migration (Alembic)

**Your test user:**
- Email: christoph.amrein86@gmail.com
- Password: test123456
- Credits: 1000
- API: Unlocked

Will be recreated automatically by script.

---

## Stack After Fix

```
Docker Compose:
├─ PostgreSQL (fresh, clean schema)
└─ QuickTools API (updated code)

All in Docker ✅
PostgreSQL (not SQLite) ✅
Production-ready ✅
```

---

## Verification

After running fix:

```bash
# Test health
curl http://192.168.0.89:5000/api/health

# Test login
curl -X POST http://192.168.0.89:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"christoph.amrein86@gmail.com","password":"test123456"}'
```

Should return access token ✅

---

## For Production

When deploying to production:

1. **Use Alembic for migrations** (proper database migrations)
2. **Backup before migrating**
3. **Never use `down -v`** (preserves data)
4. **Run migration scripts** instead of recreating

This quick fix works for development but not production.

---

## Run the Fix

```bash
cd /home/influ/projects/quicktools
sudo ./PROPER_FIX.sh
```

**Takes:** 30 seconds  
**Result:** Fresh PostgreSQL + working login

---

**Status:** Ready to run!
