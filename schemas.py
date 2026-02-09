"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


# Auth schemas
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str]
    credits_balance: int  # Current credits
    credits_purchased_total: int
    credits_lifetime_used: int
    api_access_unlocked: bool
    support_tier: str  # Calculated from credits_purchased_total
    created_at: datetime
    
    class Config:
        from_attributes = True
    
    # Computed property for compatibility
    @property
    def credits_remaining(self):
        """Alias for credits_balance (backwards compatibility)"""
        return self.credits_balance


# Credit Pack schemas
class CreditPack(BaseModel):
    name: str
    price: int  # cents
    credits: int
    per_credit: float
    unlocks_api: bool
    features: list[str]


class CheckoutSessionRequest(BaseModel):
    tier: str = Field(..., pattern="^(starter|standard|pro|business)$")


class CheckoutSession(BaseModel):
    session_id: str
    url: str


# Usage schemas
class ProcessImageResponse(BaseModel):
    success: bool
    file_id: str
    output_url: str
    download_url: str
    original_filename: str
    output_filename: str
    original_size: int
    output_size: int
    format: str
    has_watermark: bool
    credits_remaining: Optional[int] = None
    timestamp: datetime


class UsageStats(BaseModel):
    total_processed: int
    credits_balance: int  # Current available credits
    credits_lifetime_used: int  # Total credits used ever
    credits_purchased_total: int  # Total credits purchased
    api_access_unlocked: bool  # Has API access
    support_tier: str  # Community, Email, Priority, Dedicated


# API Key schemas
class APIKeyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class APIKeyResponse(BaseModel):
    id: str
    name: str
    prefix: str
    is_active: bool
    last_used_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class APIKeyCreateResponse(BaseModel):
    success: bool
    api_key: str  # Full key, shown only once
    key_id: str
    name: str
    created_at: datetime
    warning: str


# Support schemas
class SupportRequest(BaseModel):
    subject: str = Field(..., min_length=3, max_length=200)
    message: str = Field(..., min_length=10, max_length=2000)


class SupportResponse(BaseModel):
    success: bool
    message: str
    support_level: str
    expected_response: str
    email: str
