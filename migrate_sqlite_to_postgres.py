#!/usr/bin/env python3
"""
Migrate data from SQLite to PostgreSQL
Usage: python migrate_sqlite_to_postgres.py
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from models import Base, User, UsageRecord, APIKey

# Database URLs
SQLITE_URL = "sqlite:///./quicktools.db"
POSTGRES_URL = os.getenv("DATABASE_URL", "postgresql://quicktools:quicktools_dev_password@localhost:5432/quicktools")

def migrate():
    """Migrate all data from SQLite to PostgreSQL"""
    
    print("🔄 QuickTools: SQLite → PostgreSQL Migration")
    print("=" * 60)
    
    # Check if SQLite database exists
    if not os.path.exists("quicktools.db"):
        print("⚠️  No SQLite database found. Creating fresh PostgreSQL database...")
        postgres_engine = create_engine(POSTGRES_URL)
        Base.metadata.create_all(postgres_engine)
        print("✅ Fresh PostgreSQL database created!")
        return
    
    print("\n📊 Step 1: Connecting to databases...")
    
    # Connect to SQLite
    sqlite_engine = create_engine(SQLITE_URL)
    SqliteSession = sessionmaker(bind=sqlite_engine)
    sqlite_session = SqliteSession()
    print("  ✅ Connected to SQLite")
    
    # Connect to PostgreSQL
    postgres_engine = create_engine(POSTGRES_URL)
    PostgresSession = sessionmaker(bind=postgres_engine)
    postgres_session = PostgresSession()
    print("  ✅ Connected to PostgreSQL")
    
    print("\n🏗️  Step 2: Creating PostgreSQL tables...")
    Base.metadata.create_all(postgres_engine)
    print("  ✅ Tables created")
    
    print("\n📦 Step 3: Migrating data...")
    
    # Migrate Users
    users = sqlite_session.query(User).all()
    print(f"  👥 Migrating {len(users)} users...")
    for user in users:
        # Check if user already exists
        existing = postgres_session.query(User).filter(User.id == user.id).first()
        if not existing:
            postgres_session.add(user)
    postgres_session.commit()
    print(f"  ✅ Users migrated")
    
    # Migrate UsageRecords
    records = sqlite_session.query(UsageRecord).all()
    print(f"  📝 Migrating {len(records)} usage records...")
    for record in records:
        existing = postgres_session.query(UsageRecord).filter(UsageRecord.id == record.id).first()
        if not existing:
            postgres_session.add(record)
    postgres_session.commit()
    print(f"  ✅ Usage records migrated")
    
    # Migrate API Keys
    api_keys = sqlite_session.query(APIKey).all()
    print(f"  🔑 Migrating {len(api_keys)} API keys...")
    for key in api_keys:
        existing = postgres_session.query(APIKey).filter(APIKey.id == key.id).first()
        if not existing:
            postgres_session.add(key)
    postgres_session.commit()
    print(f"  ✅ API keys migrated")
    
    print("\n✅ Step 4: Verifying migration...")
    
    # Verify counts
    pg_users = postgres_session.query(User).count()
    pg_records = postgres_session.query(UsageRecord).count()
    pg_keys = postgres_session.query(APIKey).count()
    
    print(f"  PostgreSQL now has:")
    print(f"    👥 Users: {pg_users}")
    print(f"    📝 Usage records: {pg_records}")
    print(f"    🔑 API keys: {pg_keys}")
    
    # Close sessions
    sqlite_session.close()
    postgres_session.close()
    
    print("\n" + "=" * 60)
    print("✅ Migration complete!")
    print("\n💡 Next steps:")
    print("  1. Backup SQLite: mv quicktools.db quicktools.db.backup")
    print("  2. Restart app to use PostgreSQL")
    print("=" * 60)

if __name__ == "__main__":
    try:
        migrate()
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
