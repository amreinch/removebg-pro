"""
Database models for RemoveBG Pro
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
    
    # Subscription
    subscription_tier = Column(String, default="free")  # free, basic, pro, business
    subscription_status = Column(String, default="active")  # active, cancelled, expired
    stripe_customer_id = Column(String, nullable=True)
    stripe_subscription_id = Column(String, nullable=True)
    
    # Credits
    monthly_credits = Column(Integer, default=3)  # Resets monthly
    credits_used_this_month = Column(Integer, default=0)
    credits_reset_date = Column(DateTime, default=datetime.utcnow)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    usage_records = relationship("UsageRecord", back_populates="user", cascade="all, delete-orphan")
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    
    @property
    def credits_remaining(self):
        """Calculate remaining credits for current month"""
        return max(0, self.monthly_credits - self.credits_used_this_month)
    
    @property
    def can_process(self):
        """Check if user can process more images"""
        return self.credits_remaining > 0
    
    def use_credit(self):
        """Deduct one credit"""
        self.credits_used_this_month += 1
        self.updated_at = datetime.utcnow()
    
    def reset_monthly_credits(self):
        """Reset credits for new month"""
        self.credits_used_this_month = 0
        self.credits_reset_date = datetime.utcnow()
        self.updated_at = datetime.utcnow()


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
    """API keys for programmatic access (Pro & Business tiers only)"""
    __tablename__ = "api_keys"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    key_hash = Column(String, unique=True, nullable=False, index=True)  # SHA256 hash
    key_prefix = Column(String)  # First 8 chars for display (rbp_live_)
    name = Column(String)  # User-defined name
    
    is_active = Column(Boolean, default=True)
    last_used_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="api_keys")
