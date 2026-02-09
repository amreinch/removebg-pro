#!/usr/bin/env python3
"""
Quick script to add credits to a user account for testing
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import User
import sys

# Database URL (matches docker-compose.yml)
DATABASE_URL = "postgresql://quicktools_user:quicktools_pass@localhost:5432/quicktools_db"

def add_credits(email, credits_to_add):
    """Add credits to a user account"""
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Find user by email
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            print(f"❌ User not found: {email}")
            print("\nAvailable users:")
            users = db.query(User).all()
            for u in users:
                print(f"  - {u.email} (current credits: {u.credits_balance})")
            return False
        
        # Add credits
        old_balance = user.credits_balance
        user.credits_balance += credits_to_add
        db.commit()
        
        print(f"✅ Success!")
        print(f"   User: {email}")
        print(f"   Old balance: {old_balance} credits")
        print(f"   Added: {credits_to_add} credits")
        print(f"   New balance: {user.credits_balance} credits")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python add_credits.py <email> <credits>")
        print("Example: python add_credits.py user@example.com 100")
        sys.exit(1)
    
    email = sys.argv[1]
    try:
        credits = int(sys.argv[2])
    except ValueError:
        print("❌ Credits must be a number")
        sys.exit(1)
    
    add_credits(email, credits)
