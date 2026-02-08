"""
RemoveBG Pro - AI Background Remover Service with Monetization
Main application file
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
from models import User, UsageRecord
from auth import (
    hash_password, verify_password, create_access_token,
    get_current_user, check_user_credits
)
from schemas import (
    UserCreate, UserLogin, Token, UserResponse,
    ProcessImageResponse, UsageStats, CheckoutSession
)
from watermark import add_watermark

# Initialize app
app = FastAPI(
    title="RemoveBG Pro API",
    description="AI-powered background removal service with monetization",
    version="2.0.0"
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

# Tier configurations
TIER_CONFIG = {
    "free": {"credits": 3, "watermark": True},
    "basic": {"credits": 50, "watermark": False},
    "pro": {"credits": 500, "watermark": False},
    "business": {"credits": 5000, "watermark": False},
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
    return HTMLResponse(content="<h1>RemoveBG Pro API</h1><p>Visit /docs for API documentation.</p>")


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
# IMAGE PROCESSING ENDPOINT (with auth and credits)
# ============================================================================

@app.post("/api/remove-background", response_model=ProcessImageResponse)
async def remove_background(
    file: UploadFile = File(...),
    format: str = Form("png"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Remove background from uploaded image (authenticated users only)
    """
    # Check credits
    check_user_credits(current_user)
    
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
        
        # Apply watermark for free users
        tier_config = TIER_CONFIG.get(current_user.subscription_tier, TIER_CONFIG["free"])
        has_watermark = tier_config["watermark"]
        
        if has_watermark:
            output_image = add_watermark(output_image)
        
        # Save processed image
        output_format = format.lower()
        if output_format not in ["png", "jpg", "jpeg", "webp"]:
            output_format = "png"
        
        output_filename = f"{file_id}.{output_format}"
        output_path = OUTPUT_DIR / output_filename
        
        if output_format in ["jpg", "jpeg"]:
            # JPG doesn't support transparency, add white background
            background = Image.new("RGB", output_image.size, (255, 255, 255))
            background.paste(output_image, mask=output_image.split()[3] if len(output_image.split()) == 4 else None)
            background.save(output_path, format="JPEG", quality=95)
        else:
            output_image.save(output_path, format=output_format.upper())
        
        # Get file sizes
        original_size = os.path.getsize(input_path)
        output_size = os.path.getsize(output_path)
        
        # Calculate processing time
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
        
        # Return result
        return ProcessImageResponse(
            success=True,
            file_id=file_id,
            output_url=f"/outputs/{output_filename}",
            download_url=f"/api/download/{file_id}",
            original_filename=file.filename,
            output_filename=output_filename,
            original_size=original_size,
            output_size=output_size,
            format=output_format,
            has_watermark=has_watermark,
            credits_remaining=current_user.credits_remaining,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


@app.get("/api/download/{file_id}")
async def download_file(
    file_id: str,
    current_user: User = Depends(get_current_user)
):
    """Download processed image"""
    # Find file with any extension
    for ext in ["png", "jpg", "jpeg", "webp"]:
        file_path = OUTPUT_DIR / f"{file_id}.{ext}"
        if file_path.exists():
            return FileResponse(
                file_path,
                media_type=f"image/{ext}",
                filename=f"removebg-pro-{file_id}.{ext}"
            )
    
    raise HTTPException(status_code=404, detail="File not found")


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
    tier: str,
    current_user: User = Depends(get_current_user)
):
    """Create Stripe checkout session for subscription"""
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
                    user.monthly_credits = TIER_CONFIG[tier]["credits"]
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
