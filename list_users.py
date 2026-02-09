#!/usr/bin/env python3
"""
List all users and their credit balances
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import User

# Database URL (matches docker-compose.yml)
DATABASE_URL = "postgresql://quicktools_user:quicktools_pass@localhost:5432/quicktools_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

try:
    users = db.query(User).all()
    
    if not users:
        print("No users found in database.")
    else:
        print(f"\n{'Email':<40} {'Credits':<10} {'API Access':<12} {'Lifetime $':<12}")
        print("-" * 80)
        for user in users:
            lifetime_value = user.credits_purchased_total * 0.05  # Assuming $5 per 100 credits avg
            api_status = "✅ Yes" if user.api_access_unlocked else "❌ No"
            print(f"{user.email:<40} {user.credits_balance:<10} {api_status:<12} ${lifetime_value:<11.2f}")
        print(f"\nTotal users: {len(users)}")
finally:
    db.close()
