"""
Migration script: Subscription → Credit Pack System
Run this ONCE to migrate existing users
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///quicktools.db")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def migrate():
    """Run migration"""
    session = Session()
    
    try:
        print("🔄 Starting migration to credit pack system...")
        
        # Add new columns (safe if already exist)
        print("📝 Adding new columns...")
        try:
            session.execute(text("""
                ALTER TABLE users ADD COLUMN credits_balance INTEGER DEFAULT 10
            """))
            session.commit()
        except Exception as e:
            print(f"   credits_balance: {e}")
            session.rollback()
        
        try:
            session.execute(text("""
                ALTER TABLE users ADD COLUMN credits_purchased_total INTEGER DEFAULT 0
            """))
            session.commit()
        except Exception as e:
            print(f"   credits_purchased_total: {e}")
            session.rollback()
        
        try:
            session.execute(text("""
                ALTER TABLE users ADD COLUMN credits_lifetime_used INTEGER DEFAULT 0
            """))
            session.commit()
        except Exception as e:
            print(f"   credits_lifetime_used: {e}")
            session.rollback()
        
        try:
            session.execute(text("""
                ALTER TABLE users ADD COLUMN api_access_unlocked BOOLEAN DEFAULT 0
            """))
            session.commit()
        except Exception as e:
            print(f"   api_access_unlocked: {e}")
            session.rollback()
        
        try:
            session.execute(text("""
                ALTER TABLE users ADD COLUMN last_purchase_date DATETIME
            """))
            session.commit()
        except Exception as e:
            print(f"   last_purchase_date: {e}")
            session.rollback()
        
        try:
            session.execute(text("""
                ALTER TABLE users ADD COLUMN last_purchase_amount INTEGER
            """))
            session.commit()
        except Exception as e:
            print(f"   last_purchase_amount: {e}")
            session.rollback()
        
        # Migrate existing users
        print("\n👥 Migrating existing users...")
        
        # Get all users
        result = session.execute(text("""
            SELECT id, subscription_tier, monthly_credits, credits_used_this_month 
            FROM users
        """))
        users = result.fetchall()
        
        for user in users:
            user_id, tier, monthly_credits, used = user
            
            # Calculate remaining credits from old system
            if monthly_credits and used is not None:
                remaining = max(0, monthly_credits - used)
            else:
                remaining = 10  # Default
            
            # Set API access for pro/business users
            api_unlocked = 1 if tier in ('pro', 'business') else 0
            
            # Set lifetime used
            lifetime_used = used if used else 0
            
            # Update user
            session.execute(text("""
                UPDATE users 
                SET credits_balance = :balance,
                    credits_lifetime_used = :used,
                    api_access_unlocked = :api
                WHERE id = :id
            """), {
                'balance': remaining,
                'used': lifetime_used,
                'api': api_unlocked,
                'id': user_id
            })
            
            print(f"   ✅ {user_id[:8]}... → {remaining} credits, API: {'Yes' if api_unlocked else 'No'}")
        
        session.commit()
        
        print("\n✅ Migration complete!")
        print("\n📊 Summary:")
        
        # Show stats
        result = session.execute(text("""
            SELECT 
                COUNT(*) as total_users,
                SUM(credits_balance) as total_credits,
                SUM(CASE WHEN api_access_unlocked = 1 THEN 1 ELSE 0 END) as api_users
            FROM users
        """))
        stats = result.fetchone()
        
        print(f"   Total users: {stats[0]}")
        print(f"   Total credits in system: {stats[1]}")
        print(f"   Users with API access: {stats[2]}")
        
        print("\n⚠️  Old subscription columns kept for safety.")
        print("   After confirming everything works, run:")
        print("   ALTER TABLE users DROP COLUMN subscription_tier;")
        print("   ALTER TABLE users DROP COLUMN subscription_status;")
        print("   ALTER TABLE users DROP COLUMN stripe_subscription_id;")
        print("   ALTER TABLE users DROP COLUMN monthly_credits;")
        print("   ALTER TABLE users DROP COLUMN credits_used_this_month;")
        print("   ALTER TABLE users DROP COLUMN credits_reset_date;")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    migrate()
