"""
Database models for QuickTools
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()


class User(Base):
    """User account model"""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    
    # Credit Pack System (NEW)
    credits_balance = Column(Integer, default=10)  # Current balance (10 free starter)
    credits_purchased_total = Column(Integer, default=0)  # Lifetime purchases
    credits_lifetime_used = Column(Integer, default=0)  # Lifetime usage
    api_access_unlocked = Column(Boolean, default=False)  # Unlocked when bought Pro+ pack
    
    # Stripe
    stripe_customer_id = Column(String, nullable=True)
    last_purchase_date = Column(DateTime, nullable=True)
    last_purchase_amount = Column(Integer, nullable=True)  # Credits from last purchase
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    usage_records = relationship("UsageRecord", back_populates="user", cascade="all, delete-orphan")
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    
    @property
    def credits_remaining(self):
        """Get current credit balance"""
        return max(0, self.credits_balance)
    
    @property
    def can_process(self):
        """Check if user can process more images"""
        return self.credits_balance > 0
    
    def use_credit(self):
        """Deduct one credit"""
        if self.credits_balance > 0:
            self.credits_balance -= 1
            self.credits_lifetime_used += 1
            self.updated_at = datetime.utcnow()
        else:
            raise ValueError("Insufficient credits")
    
    def add_credits(self, amount: int, unlocks_api: bool = False):
        """Add credits from purchase"""
        self.credits_balance += amount
        self.credits_purchased_total += amount
        self.last_purchase_date = datetime.utcnow()
        self.last_purchase_amount = amount
        
        if unlocks_api:
            self.api_access_unlocked = True
        
        self.updated_at = datetime.utcnow()
    
    @property
    def support_tier(self):
        """Determine support tier based on lifetime purchases"""
        if self.credits_purchased_total >= 5000:  # Business pack
            return "Dedicated (12h response)"
        elif self.credits_purchased_total >= 1200:  # Pro pack
            return "Priority (24h response)"
        elif self.credits_purchased_total >= 500:  # Standard pack
            return "Email (48h response)"
        else:
            return "Community"


class UsageRecord(Base):
    """Track individual image processing"""
    __tablename__ = "usage_records"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    # File info
    original_filename = Column(String)
    file_id = Column(String)
    output_format = Column(String)
    
    # Processing info
    original_size = Column(Integer)
    output_size = Column(Integer)
    processing_time = Column(Integer)  # milliseconds
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="usage_records")


class APIKey(Base):
    """API keys for programmatic access (requires api_access_unlocked)"""
    __tablename__ = "api_keys"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    key_hash = Column(String, unique=True, nullable=False, index=True)  # SHA256 hash
    key_prefix = Column(String)  # First 8 chars for display (qkt_live_)
    name = Column(String)  # User-defined name
    
    is_active = Column(Boolean, default=True)
    last_used_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="api_keys")
