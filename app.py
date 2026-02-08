"""
QuickTools - Professional Automation Platform
Main application file

Multi-tool SaaS platform for quick professional tasks:
- Background removal
- Image processing
- PDF tools
- And more...

Pricing: Credit-based system (1 task = 1 credit)
"""
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from rembg import remove
from PIL import Image
import io
import uuid
from pathlib import Path
import os
from datetime import datetime
import stripe

# Import our modules
from database import get_db, init_db
from models import User, UsageRecord, APIKey
from auth import (
    hash_password, verify_password, create_access_token,
    get_current_user, check_user_credits
)
from api_auth import (
    generate_api_key, hash_api_key, 
    get_current_user_from_api_key, check_api_access
)
from schemas import (
    UserCreate, UserLogin, Token, UserResponse,
    ProcessImageResponse, UsageStats, CheckoutSession, CheckoutSessionRequest
)
from watermark import add_watermark
from typing import Union

# Initialize app
app = FastAPI(
    title="QuickTools API",
    description="Professional automation platform - Quick tools for everyday tasks",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Stripe configuration
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_placeholder")
STRIPE_PRICE_IDS = {
    "basic": os.getenv("STRIPE_PRICE_BASIC", "price_basic"),
    "pro": os.getenv("STRIPE_PRICE_PRO", "price_pro"),
    "business": os.getenv("STRIPE_PRICE_BUSINESS", "price_business"),
}

# Tier configurations - Monthly DOWNLOAD limits
TIER_CONFIG = {
    "free": {"downloads": 3},
    "basic": {"downloads": 50},
    "pro": {"downloads": 500},
    "business": {"downloads": 5000},
}

# Create directories
UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")
STATIC_DIR = Path("static")

for directory in [UPLOAD_DIR, OUTPUT_DIR, STATIC_DIR]:
    directory.mkdir(exist_ok=True)

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")


# Startup event
@app.on_event("startup")
async def startup():
    """Initialize database and cleanup old files"""
    init_db()
    
    # Cleanup old files
    import time
    current_time = time.time()
    max_age = 24 * 60 * 60  # 24 hours
    
    for directory in [UPLOAD_DIR, OUTPUT_DIR]:
        for file_path in directory.glob("*"):
            if file_path.is_file():
                file_age = current_time - file_path.stat().st_mtime
                if file_age > max_age:
                    file_path.unlink()


# ============================================================================
# PUBLIC ENDPOINTS
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def home():
    """Serve the main web interface"""
    html_path = Path("static/index.html")
    if html_path.exists():
        return HTMLResponse(content=html_path.read_text())
    return HTMLResponse(content="<h1>QuickTools API</h1><p>Visit /docs for API documentation.</p>")


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "RemoveBG Pro API",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@app.post("/api/auth/signup", response_model=Token)
async def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    """Create new user account"""
    # Check if user exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    user = User(
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        full_name=user_data.full_name,
        subscription_tier="free",
        monthly_credits=3,
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create token
    access_token = create_access_token(data={"sub": user.id})
    
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/api/auth/login", response_model=Token)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Login user"""
    user = db.query(User).filter(User.email == credentials.email).first()
    
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")
    
    access_token = create_access_token(data={"sub": user.id})
    
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/api/auth/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    return current_user


# ============================================================================
# IMAGE PROCESSING ENDPOINTS
# ============================================================================

@app.post("/api/remove-background", response_model=ProcessImageResponse)
async def remove_background(
    file: UploadFile = File(...),
    format: str = Form("png"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Remove background from uploaded image - Returns PREVIEW (watermarked, FREE!)
    
    This endpoint is FREE and always returns a watermarked preview.
    Use /api/download/{file_id} to get the clean version (costs 1 credit).
    """
    # Validate file type
    allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_types)}"
        )
    
    # Validate file size (max 10MB)
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Max 10MB")
    
    try:
        start_time = datetime.utcnow()
        
        # Generate unique ID
        file_id = str(uuid.uuid4())
        
        # Save original file
        input_path = UPLOAD_DIR / f"{file_id}_original{Path(file.filename).suffix}"
        with open(input_path, "wb") as f:
            f.write(contents)
        
        # Process image - remove background
        input_image = Image.open(io.BytesIO(contents))
        output_image = remove(input_image)
        
        # Determine output format
        output_format = format.lower()
        if output_format not in ["png", "jpg", "jpeg", "webp"]:
            output_format = "png"
        
        # Save CLEAN version (for later download)
        clean_filename = f"{file_id}_clean.{output_format}"
        clean_path = OUTPUT_DIR / clean_filename
        
        if output_format in ["jpg", "jpeg"]:
            # JPG doesn't support transparency, add white background
            background = Image.new("RGB", output_image.size, (255, 255, 255))
            background.paste(output_image, mask=output_image.split()[3] if len(output_image.split()) == 4 else None)
            background.save(clean_path, format="JPEG", quality=95)
        else:
            output_image.save(clean_path, format=output_format.upper())
        
        # Add watermark for PREVIEW
        watermarked_image = add_watermark(output_image)
        
        # Save PREVIEW version (watermarked)
        preview_filename = f"{file_id}_preview.{output_format}"
        preview_path = OUTPUT_DIR / preview_filename
        
        if output_format in ["jpg", "jpeg"]:
            background = Image.new("RGB", watermarked_image.size, (255, 255, 255))
            background.paste(watermarked_image, mask=watermarked_image.split()[3] if len(watermarked_image.split()) == 4 else None)
            background.save(preview_path, format="JPEG", quality=95)
        else:
            watermarked_image.save(preview_path, format=output_format.upper())
        
        # Get file sizes
        original_size = os.path.getsize(input_path)
        output_size = os.path.getsize(clean_path)
        
        # Calculate processing time
        processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        # Record usage (but don't charge credit yet)
        usage_record = UsageRecord(
            user_id=current_user.id,
            original_filename=file.filename,
            file_id=file_id,
            output_format=output_format,
            original_size=original_size,
            output_size=output_size,
            processing_time=processing_time
        )
        db.add(usage_record)
        db.commit()
        
        # Return PREVIEW result (watermarked, no credit charged)
        return ProcessImageResponse(
            success=True,
            file_id=file_id,
            output_url=f"/outputs/{preview_filename}",  # Watermarked preview
            download_url=f"/api/download/{file_id}",     # Clean version (costs credit)
            original_filename=file.filename,
            output_filename=preview_filename,
            original_size=original_size,
            output_size=output_size,
            format=output_format,
            has_watermark=True,  # Preview is ALWAYS watermarked
            credits_remaining=current_user.credits_remaining,  # Not deducted yet
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


@app.get("/api/download/{file_id}")
async def download_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Download processed image (CLEAN, no watermark) - Costs 1 credit
    
    This endpoint returns the clean version without watermark.
    Requires available credits (deducts 1 credit per download).
    """
    # Check if user has credits
    check_user_credits(current_user)
    
    # Find clean file
    for ext in ["png", "jpg", "jpeg", "webp"]:
        file_path = OUTPUT_DIR / f"{file_id}_clean.{ext}"
        if file_path.exists():
            # Deduct credit
            current_user.use_credit()
            db.commit()
            
            # Return clean file
            return FileResponse(
                file_path,
                media_type=f"image/{ext}",
                filename=f"removebg-pro-{file_id}.{ext}"
            )
    
    raise HTTPException(status_code=404, detail="File not found or expired")


# ============================================================================
# USER DASHBOARD & STATS
# ============================================================================

@app.get("/api/stats", response_model=UsageStats)
async def get_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user statistics"""
    total_processed = db.query(UsageRecord).filter(
        UsageRecord.user_id == current_user.id
    ).count()
    
    return UsageStats(
        total_processed=total_processed,
        credits_used_this_month=current_user.credits_used_this_month,
        credits_remaining=current_user.credits_remaining,
        monthly_credits=current_user.monthly_credits,
        subscription_tier=current_user.subscription_tier
    )


# ============================================================================
# STRIPE INTEGRATION
# ============================================================================

@app.post("/api/create-checkout-session", response_model=CheckoutSession)
async def create_checkout_session(
    request: CheckoutSessionRequest,
    current_user: User = Depends(get_current_user)
):
    """Create Stripe checkout session for subscription"""
    tier = request.tier
    if tier not in STRIPE_PRICE_IDS:
        raise HTTPException(status_code=400, detail="Invalid subscription tier")
    
    try:
        # Create Stripe customer if doesn't exist
        if not current_user.stripe_customer_id:
            customer = stripe.Customer.create(
                email=current_user.email,
                metadata={"user_id": current_user.id}
            )
            current_user.stripe_customer_id = customer.id
        
        # Create checkout session
        session = stripe.checkout.Session.create(
            customer=current_user.stripe_customer_id,
            payment_method_types=["card"],
            line_items=[{
                "price": STRIPE_PRICE_IDS[tier],
                "quantity": 1,
            }],
            mode="subscription",
            success_url=os.getenv("FRONTEND_URL", "http://localhost:5000") + "/success?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=os.getenv("FRONTEND_URL", "http://localhost:5000") + "/pricing",
        )
        
        return CheckoutSession(session_id=session.id, url=session.url)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stripe error: {str(e)}")


@app.post("/api/webhook/stripe")
async def stripe_webhook(request: dict, db: Session = Depends(get_db)):
    """Handle Stripe webhooks"""
    # In production, verify signature
    event_type = request.get("type")
    
    if event_type == "checkout.session.completed":
        session = request.get("data", {}).get("object", {})
        customer_id = session.get("customer")
        subscription_id = session.get("subscription")
        
        # Update user subscription
        user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
        if user:
            user.stripe_subscription_id = subscription_id
            user.subscription_status = "active"
            
            # Determine tier from price_id
            subscription = stripe.Subscription.retrieve(subscription_id)
            price_id = subscription["items"]["data"][0]["price"]["id"]
            
            for tier, pid in STRIPE_PRICE_IDS.items():
                if pid == price_id:
                    user.subscription_tier = tier
                    user.monthly_credits = TIER_CONFIG[tier]["downloads"]
                    break
            
            db.commit()
    
    elif event_type == "customer.subscription.deleted":
        subscription = request.get("data", {}).get("object", {})
        customer_id = subscription.get("customer")
        
        # Downgrade user to free
        user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
        if user:
            user.subscription_tier = "free"
            user.subscription_status = "cancelled"
            user.monthly_credits = 3
            db.commit()
    
    return {"status": "success"}


# ============================================================================
# ADMIN ENDPOINTS (optional)
# ============================================================================

@app.get("/api/admin/users")
async def list_users(db: Session = Depends(get_db)):
    """List all users (admin only - add auth later)"""
    users = db.query(User).all()
    return [{"id": u.id, "email": u.email, "tier": u.subscription_tier} for u in users]


# ============================================================================
# API KEY MANAGEMENT (Pro & Business tiers only)
# ============================================================================

@app.post("/api/keys/create")
async def create_api_key(
    name: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new API key (Pro & Business tiers only)
    Returns the plain key ONCE - store it securely!
    """
    # Check if user has API access
    check_api_access(current_user)
    
    # Generate new API key
    plain_key = generate_api_key()
    key_hash = hash_api_key(plain_key)
    key_prefix = plain_key[:16]  # rbp_live_xxxxxxx
    
    # Save to database
    api_key = APIKey(
        user_id=current_user.id,
        key_hash=key_hash,
        key_prefix=key_prefix,
        name=name
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    
    return {
        "success": True,
        "api_key": plain_key,  # ONLY shown once!
        "key_id": api_key.id,
        "name": name,
        "created_at": api_key.created_at,
        "warning": "Save this key securely! It will not be shown again."
    }


@app.get("/api/keys/list")
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all API keys for current user"""
    check_api_access(current_user)
    
    keys = db.query(APIKey).filter(
        APIKey.user_id == current_user.id
    ).all()
    
    return {
        "keys": [
            {
                "id": k.id,
                "name": k.name,
                "prefix": k.key_prefix,
                "is_active": k.is_active,
                "last_used_at": k.last_used_at,
                "created_at": k.created_at
            }
            for k in keys
        ]
    }


@app.delete("/api/keys/{key_id}")
async def revoke_api_key(
    key_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Revoke (delete) an API key"""
    check_api_access(current_user)
    
    api_key = db.query(APIKey).filter(
        APIKey.id == key_id,
        APIKey.user_id == current_user.id
    ).first()
    
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    db.delete(api_key)
    db.commit()
    
    return {"success": True, "message": f"API key '{api_key.name}' revoked"}


# ============================================================================
# API ENDPOINTS (Use with X-API-Key header)
# ============================================================================

@app.post("/api/v1/remove-background")
async def api_remove_background(
    file: UploadFile = File(...),
    format: str = Form("png"),
    current_user: User = Depends(get_current_user_from_api_key),
    db: Session = Depends(get_db)
):
    """
    API endpoint for background removal (requires API key)
    
    Usage:
    curl -X POST https://yourapp.com/api/v1/remove-background \
         -H "X-API-Key: rbp_live_xxxxxxxxxx" \
         -F "file=@image.jpg" \
         -F "format=png"
    
    Returns clean image directly (no watermark, costs 1 credit)
    """
    # Check credits
    check_user_credits(current_user)
    
    # Validate file type
    allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    # Read file
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Max 10MB")
    
    try:
        start_time = datetime.utcnow()
        
        # Generate ID
        file_id = str(uuid.uuid4())
        
        # Save original
        input_path = UPLOAD_DIR / f"{file_id}_api_original{Path(file.filename).suffix}"
        with open(input_path, "wb") as f:
            f.write(contents)
        
        # Process image
        input_image = Image.open(io.BytesIO(contents))
        output_image = remove(input_image)
        
        # Determine format
        output_format = format.lower()
        if output_format not in ["png", "jpg", "jpeg", "webp"]:
            output_format = "png"
        
        # Save clean version (NO WATERMARK for API)
        output_filename = f"{file_id}_api.{output_format}"
        output_path = OUTPUT_DIR / output_filename
        
        if output_format in ["jpg", "jpeg"]:
            background = Image.new("RGB", output_image.size, (255, 255, 255))
            background.paste(output_image, mask=output_image.split()[3] if len(output_image.split()) == 4 else None)
            background.save(output_path, format="JPEG", quality=95)
        else:
            output_image.save(output_path, format=output_format.upper())
        
        # Get sizes
        original_size = os.path.getsize(input_path)
        output_size = os.path.getsize(output_path)
        processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        # Deduct credit
        current_user.use_credit()
        
        # Record usage
        usage_record = UsageRecord(
            user_id=current_user.id,
            original_filename=file.filename,
            file_id=file_id,
            output_format=output_format,
            original_size=original_size,
            output_size=output_size,
            processing_time=processing_time
        )
        db.add(usage_record)
        db.commit()
        
        # Return clean file
        return FileResponse(
            output_path,
            media_type=f"image/{output_format}",
            filename=f"removed-bg-{file_id}.{output_format}",
            headers={
                "X-Credits-Remaining": str(current_user.credits_remaining),
                "X-Processing-Time-Ms": str(processing_time)
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


# ============================================================================
# SUPPORT & CONTACT
# ============================================================================

@app.post("/api/support/contact")
async def contact_support(
    subject: str = Form(...),
    message: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit a support request
    
    Support levels:
    - Free: Community support (email saved, manual review)
    - Basic: Email support (48h response)
    - Pro: Priority support (24h response)
    - Business: Priority support (12h response)
    """
    # Determine support tier
    support_tier = {
        "free": "community",
        "basic": "email",
        "pro": "priority",
        "business": "priority-plus"
    }.get(current_user.subscription_tier, "community")
    
    # Log support request (in production, send email or create ticket)
    support_data = {
        "user_id": current_user.id,
        "email": current_user.email,
        "tier": current_user.subscription_tier,
        "support_level": support_tier,
        "subject": subject,
        "message": message,
        "timestamp": datetime.utcnow()
    }
    
    # TODO: In production, integrate with:
    # - Email service (SendGrid, Mailgun)
    # - Support ticket system (Zendesk, Intercom)
    # - Or save to database and notify admin
    
    print(f"[SUPPORT REQUEST] {support_data}")  # For now, just log
    
    # Return expected response time
    response_time = {
        "community": "We'll review your message and respond when possible.",
        "email": "We'll respond within 48 hours.",
        "priority": "We'll respond within 24 hours.",
        "priority-plus": "We'll respond within 12 hours."
    }
    
    return {
        "success": True,
        "message": "Support request submitted successfully.",
        "support_level": support_tier,
        "expected_response": response_time[support_tier],
        "email": current_user.email
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
