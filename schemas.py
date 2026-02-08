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
    subscription_tier: str
    credits_remaining: int
    monthly_credits: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# Subscription schemas
class SubscriptionTier(BaseModel):
    name: str
    price: int  # cents
    monthly_credits: int
    features: list[str]


class CheckoutSessionRequest(BaseModel):
    tier: str = Field(..., pattern="^(basic|pro|business)$")


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
    credits_used_this_month: int
    credits_remaining: int
    monthly_credits: int
    subscription_tier: str


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
