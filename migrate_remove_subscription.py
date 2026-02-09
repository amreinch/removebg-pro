#!/usr/bin/env python3
"""
Database Migration: Remove Old Subscription Fields
==================================================

Removes deprecated subscription fields from users table:
- subscription_tier
- subscription_status
- stripe_subscription_id
- monthly_credits
- credits_used_this_month
- credits_reset_date

These fields were part of the old subscription model and are no longer used.
The new credit pack model uses:
- credits_balance
- credits_purchased_total
- credits_lifetime_used
- api_access_unlocked

Usage:
    python migrate_remove_subscription.py

IMPORTANT: Backup your database first!
    cp quicktools.db quicktools.db.backup
"""

import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent / "quicktools.db"

def backup_database():
    """Create automatic backup before migration"""
    backup_path = DB_PATH.with_suffix('.db.backup')
    
    print(f"📦 Creating backup: {backup_path}")
    
    # Copy database file
    import shutil
    shutil.copy2(DB_PATH, backup_path)
    
    print(f"✅ Backup created successfully")
    return backup_path

def get_column_names(cursor, table_name):
    """Get list of column names for a table"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    return [row[1] for row in cursor.fetchall()]

def migrate():
    """Run the migration"""
    
    if not DB_PATH.exists():
        print(f"❌ Database not found: {DB_PATH}")
        print("   Make sure you're running this from the quicktools directory")
        sys.exit(1)
    
    print("🚀 Starting migration: Remove old subscription fields")
    print(f"   Database: {DB_PATH}")
    print()
    
    # Create backup
    backup_path = backup_database()
    print()
    
    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check current columns
        print("📋 Checking current schema...")
        columns = get_column_names(cursor, "users")
        
        old_fields = [
            'subscription_tier',
            'subscription_status', 
            'stripe_subscription_id',
            'monthly_credits',
            'credits_used_this_month',
            'credits_reset_date'
        ]
        
        fields_to_remove = [f for f in old_fields if f in columns]
        
        if not fields_to_remove:
            print("✅ No old subscription fields found. Already migrated!")
            conn.close()
            return
        
        print(f"📝 Found {len(fields_to_remove)} old fields to remove:")
        for field in fields_to_remove:
            print(f"   - {field}")
        print()
        
        # SQLite doesn't support DROP COLUMN directly
        # We need to recreate the table
        
        print("🔧 Creating new users table schema...")
        
        # Get all users data
        cursor.execute("SELECT * FROM users")
        users_data = cursor.fetchall()
        old_columns = get_column_names(cursor, "users")
        
        print(f"   Found {len(users_data)} users to migrate")
        
        # Create new table with correct schema
        cursor.execute("""
            CREATE TABLE users_new (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                full_name TEXT,
                
                credits_balance INTEGER DEFAULT 10,
                credits_purchased_total INTEGER DEFAULT 0,
                credits_lifetime_used INTEGER DEFAULT 0,
                api_access_unlocked BOOLEAN DEFAULT 0,
                
                stripe_customer_id TEXT,
                last_purchase_date TIMESTAMP,
                last_purchase_amount INTEGER,
                
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        """)
        
        # Map old columns to new columns
        new_columns = get_column_names(cursor, "users_new")
        
        # Copy data from old table to new table
        print("📦 Migrating user data...")
        
        for user in users_data:
            user_dict = dict(zip(old_columns, user))
            
            # Build INSERT statement with only columns that exist in new table
            columns_to_insert = [col for col in new_columns if col in old_columns]
            values = [user_dict[col] for col in columns_to_insert]
            
            placeholders = ','.join(['?' for _ in columns_to_insert])
            columns_str = ','.join(columns_to_insert)
            
            cursor.execute(
                f"INSERT INTO users_new ({columns_str}) VALUES ({placeholders})",
                values
            )
        
        print(f"   ✅ Migrated {len(users_data)} users")
        
        # Drop old table and rename new table
        print("🔄 Replacing old table...")
        cursor.execute("DROP TABLE users")
        cursor.execute("ALTER TABLE users_new RENAME TO users")
        
        # Recreate indexes
        print("📑 Recreating indexes...")
        cursor.execute("CREATE INDEX idx_users_email ON users(email)")
        
        # Commit changes
        conn.commit()
        
        print()
        print("✅ Migration completed successfully!")
        print()
        print("📊 Summary:")
        print(f"   Removed fields: {', '.join(fields_to_remove)}")
        print(f"   Migrated users: {len(users_data)}")
        print(f"   Backup saved: {backup_path}")
        print()
        print("🎉 Your database is now clean and optimized!")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Migration failed: {e}")
        print(f"   Your data is safe in: {backup_path}")
        print(f"   To restore: mv {backup_path} {DB_PATH}")
        sys.exit(1)
    
    finally:
        conn.close()

if __name__ == "__main__":
    print()
    print("=" * 60)
    print("   QuickTools Database Migration")
    print("   Remove Old Subscription Fields")
    print("=" * 60)
    print()
    
    # Ask for confirmation
    response = input("⚠️  This will modify your database. Continue? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("❌ Migration cancelled")
        sys.exit(0)
    
    print()
    migrate()
