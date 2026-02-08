# PostgreSQL Setup for QuickTools

**Status:** ✅ Configured and ready to use  
**Date:** 2026-02-08

---

## 🐘 Why PostgreSQL?

✅ **No user limits** - Handles millions of users  
✅ **Concurrent writes** - Multiple users simultaneously  
✅ **Better performance** - Optimized for web apps  
✅ **Industry standard** - Used by Stripe, Instagram, Spotify  
✅ **Automatic backups** - Built-in backup tools  
✅ **Horizontal scaling** - Add read replicas later  

---

## 🚀 Quick Start

### Option 1: Docker (Recommended)

```bash
# Deploy with PostgreSQL
./deploy-local.sh

# This will:
# 1. Start PostgreSQL in Docker
# 2. Migrate SQLite data (if exists)
# 3. Start QuickTools app
```

### Option 2: Manual Docker

```bash
# Start PostgreSQL + App
docker compose up -d

# View logs
docker compose logs -f

# Stop everything
docker compose down
```

---

## 📊 Database Access

**Connection Details:**
- **Host:** localhost
- **Port:** 5432
- **Database:** quicktools
- **User:** quicktools
- **Password:** `quicktools_dev_password` (dev) / set in `.env`

**Connection String:**
```
postgresql://quicktools:quicktools_dev_password@localhost:5432/quicktools
```

**Connect via psql:**
```bash
docker exec -it quicktools-db psql -U quicktools
```

---

## 💾 Backup & Restore

### Backup Database

```bash
# Create backup
docker exec quicktools-db pg_dump -U quicktools quicktools > backup_$(date +%Y%m%d).sql

# Or compressed
docker exec quicktools-db pg_dump -U quicktools quicktools | gzip > backup_$(date +%Y%m%d).sql.gz
```

### Restore Database

```bash
# From SQL file
cat backup.sql | docker exec -i quicktools-db psql -U quicktools quicktools

# From compressed
gunzip -c backup.sql.gz | docker exec -i quicktools-db psql -U quicktools quicktools
```

### Automated Backups

Add to crontab:
```bash
# Backup every day at 2 AM
0 2 * * * docker exec quicktools-db pg_dump -U quicktools quicktools | gzip > /backups/quicktools_$(date +\%Y\%m\%d).sql.gz
```

---

## 🔄 Migration from SQLite

**Automatic Migration:**

The `deploy-local.sh` script automatically migrates data if it finds `quicktools.db`.

**Manual Migration:**

```bash
# 1. Ensure PostgreSQL is running
docker compose up -d db

# 2. Run migration script
python3 migrate_sqlite_to_postgres.py

# 3. Backup SQLite
mv quicktools.db quicktools.db.backup

# 4. Start app
docker compose up -d web
```

---

## 🛠️ Maintenance

### View Database Size

```bash
docker exec quicktools-db psql -U quicktools -c "SELECT pg_size_pretty(pg_database_size('quicktools'));"
```

### View Tables

```bash
docker exec quicktools-db psql -U quicktools -c "\dt"
```

### View Table Counts

```bash
docker exec quicktools-db psql -U quicktools -c "
SELECT 
  tablename,
  (SELECT count(*) FROM users) as users,
  (SELECT count(*) FROM usage_records) as usage_records,
  (SELECT count(*) FROM api_keys) as api_keys;
"
```

### Vacuum Database (Optimize)

```bash
docker exec quicktools-db psql -U quicktools -c "VACUUM ANALYZE;"
```

---

## 🔒 Production Setup

### Change Password

1. Update `.env`:
```bash
DB_PASSWORD=your_strong_password_here
DATABASE_URL=postgresql://quicktools:your_strong_password_here@localhost:5432/quicktools
```

2. Restart containers:
```bash
docker compose down
docker compose up -d
```

### Security Best Practices

✅ Use strong passwords (16+ chars, random)  
✅ Keep PostgreSQL internal (don't expose port 5432 publicly)  
✅ Use SSL/TLS for remote connections  
✅ Regular backups (automated)  
✅ Monitor disk space  

---

## 🐛 Troubleshooting

### Connection Refused

```bash
# Check if PostgreSQL is running
docker compose ps

# View PostgreSQL logs
docker compose logs db

# Restart PostgreSQL
docker compose restart db
```

### Database Already Exists Error

```bash
# Drop and recreate (⚠️ DELETES ALL DATA!)
docker exec quicktools-db psql -U quicktools -c "DROP DATABASE quicktools;"
docker exec quicktools-db psql -U quicktools -c "CREATE DATABASE quicktools;"
```

### Reset Everything

```bash
# Stop containers
docker compose down

# Delete volume (⚠️ DELETES ALL DATA!)
docker volume rm quicktools_postgres_data

# Start fresh
docker compose up -d
```

---

## 📈 Performance Tips

### Enable Connection Pooling

Already configured in SQLAlchemy. Default pool size: 5 connections.

### Index Optimization

Common queries are already indexed:
- `users.email` (unique index)
- `api_keys.key_hash` (unique index)
- Foreign keys are automatically indexed

### Query Monitoring

```bash
# View slow queries
docker exec quicktools-db psql -U quicktools -c "
SELECT query, calls, total_time, mean_time 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;
"
```

---

## 🚀 Deploy to VPS

When ready to deploy to your VPS:

1. **Copy this setup:**
```bash
# On VPS
git clone <your-repo>
cd quicktools
```

2. **Update .env with production values:**
```bash
DB_PASSWORD=<strong-production-password>
DATABASE_URL=postgresql://quicktools:<password>@db:5432/quicktools
```

3. **Deploy:**
```bash
docker compose up -d
```

4. **Set up backups** (cron job)

---

## ✅ Benefits Over SQLite

| Feature | SQLite | PostgreSQL |
|---------|--------|------------|
| Concurrent writes | ❌ One at a time | ✅ Many simultaneously |
| Max users | ~100 | ✅ Unlimited |
| Remote access | ❌ No | ✅ Yes |
| Backups | Manual | ✅ Automated tools |
| Replication | ❌ No | ✅ Yes |
| Full-text search | Limited | ✅ Advanced |
| JSON support | Basic | ✅ Native |
| Scaling | ❌ Vertical only | ✅ Horizontal |

---

**PostgreSQL is now your production database! 🎉**

All QuickTools functionality works identically - just with better performance and scalability.
