#!/bin/bash
# QuickTools - Database Restore Script

set -e

BACKUP_DIR="/home/influ/projects/quicktools/backups"
DB_PATH="/home/influ/projects/quicktools/quicktools.db"

echo "🔄 QuickTools Database Restore"
echo ""

# List available backups
echo "Available backups:"
echo ""
ls -lh "$BACKUP_DIR"/quicktools_*.db.gz 2>/dev/null | awk '{print NR". "$9" ("$5")"}'

if [ $? -ne 0 ] || [ $(ls -1 "$BACKUP_DIR"/quicktools_*.db.gz 2>/dev/null | wc -l) -eq 0 ]; then
    echo "❌ No backups found in $BACKUP_DIR"
    exit 1
fi

echo ""
read -p "Enter backup number to restore (or 'q' to quit): " CHOICE

if [ "$CHOICE" = "q" ]; then
    echo "Cancelled."
    exit 0
fi

# Get the selected backup file
BACKUP_FILE=$(ls -1 "$BACKUP_DIR"/quicktools_*.db.gz 2>/dev/null | sed -n "${CHOICE}p")

if [ -z "$BACKUP_FILE" ]; then
    echo "❌ Invalid selection"
    exit 1
fi

echo ""
echo "Selected backup: $BACKUP_FILE"
echo ""
echo "⚠️  WARNING: This will REPLACE the current database!"
echo "Current database will be backed up to: ${DB_PATH}.before_restore"
echo ""
read -p "Are you sure? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Cancelled."
    exit 0
fi

# Backup current database before restoring
if [ -f "$DB_PATH" ]; then
    echo "📦 Backing up current database..."
    cp "$DB_PATH" "${DB_PATH}.before_restore"
    echo "✅ Current database backed up"
fi

# Stop the server
echo "🛑 Stopping QuickTools..."
pkill -f "uvicorn app:app" 2>/dev/null || true
sleep 2

# Restore backup
echo "🔄 Restoring backup..."
gunzip -c "$BACKUP_FILE" > "$DB_PATH"

echo "✅ Database restored successfully!"
echo ""
echo "🚀 Restart QuickTools to use the restored database:"
echo "   cd ~/projects/quicktools"
echo "   nohup uvicorn app:app --host 0.0.0.0 --port 5000 > quicktools.log 2>&1 &"
echo ""
