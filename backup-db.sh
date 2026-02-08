#!/bin/bash
# QuickTools - SQLite Database Backup Script

set -e

# Configuration
DB_PATH="/home/influ/projects/quicktools/quicktools.db"
BACKUP_DIR="/home/influ/projects/quicktools/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/quicktools_${TIMESTAMP}.db"
KEEP_DAYS=30  # Keep backups for 30 days

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}🔒 QuickTools Database Backup${NC}"
echo ""

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Check if database exists
if [ ! -f "$DB_PATH" ]; then
    echo "❌ Database not found at: $DB_PATH"
    exit 1
fi

# Get database size
DB_SIZE=$(du -h "$DB_PATH" | cut -f1)
echo "📊 Database size: $DB_SIZE"

# Perform backup using SQLite's backup command (safer than cp)
echo "💾 Creating backup..."
sqlite3 "$DB_PATH" ".backup '$BACKUP_FILE'"

# Verify backup
if [ -f "$BACKUP_FILE" ]; then
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo -e "${GREEN}✅ Backup created successfully!${NC}"
    echo "📁 Location: $BACKUP_FILE"
    echo "📊 Size: $BACKUP_SIZE"
else
    echo "❌ Backup failed!"
    exit 1
fi

# Compress backup to save space
echo "🗜️  Compressing backup..."
gzip "$BACKUP_FILE"
COMPRESSED_FILE="${BACKUP_FILE}.gz"
COMPRESSED_SIZE=$(du -h "$COMPRESSED_FILE" | cut -f1)
echo "✅ Compressed to: $COMPRESSED_SIZE"

# Delete old backups (keep last 30 days)
echo "🧹 Cleaning old backups (keeping last $KEEP_DAYS days)..."
find "$BACKUP_DIR" -name "quicktools_*.db.gz" -type f -mtime +$KEEP_DAYS -delete
REMAINING=$(ls -1 "$BACKUP_DIR"/quicktools_*.db.gz 2>/dev/null | wc -l)
echo "📦 Total backups: $REMAINING"

echo ""
echo -e "${GREEN}✅ Backup complete!${NC}"
echo ""
echo "To restore this backup:"
echo "  gunzip -c $COMPRESSED_FILE > quicktools.db"
echo ""
