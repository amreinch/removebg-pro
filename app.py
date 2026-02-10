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
from typing import Union, List
import math

# Import our modules
from database import get_db, init_db
from models import User, UsageRecord, APIKey
from auth import (
    hash_password, verify_password, create_access_token,
    get_current_user, require_credits, check_user_has_credits
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

# Credit Pack System (replaces subscription tiers)
CREDIT_PACKS = {
    "starter": {
        "name": "Starter Pack",
        "price": 500,  # $5 in cents
        "credits": 100,
        "per_credit": 0.05,
        "unlocks_api": False,
        "badge": None,
        "features": ["Web UI access", "100 tasks", "Community support"]
    },
    "standard": {
        "name": "Standard Pack",
        "price": 1500,  # $15 in cents
        "credits": 500,
        "per_credit": 0.03,
        "unlocks_api": False,
        "badge": "⭐ Popular",
        "features": ["Web UI access", "500 tasks", "Email support (48h)", "40% better value"]
    },
    "pro": {
        "name": "Pro Pack",
        "price": 3000,  # $30 in cents
        "credits": 1200,
        "per_credit": 0.025,
        "unlocks_api": True,
        "badge": "💎 Best Value + API",
        "features": [
            "Web UI access",
            "1,200 tasks",
            "🔑 API Access (lifetime unlock)",
            "API documentation",
            "Priority support (24h)",
            "50% better value"
        ]
    },
    "business": {
        "name": "Business Pack",
        "price": 10000,  # $100 in cents
        "credits": 5000,
        "per_credit": 0.02,
        "unlocks_api": True,
        "badge": None,
        "features": [
            "Web UI access",
            "5,000 tasks",
            "🔑 API Access (lifetime unlock)",
            "Dedicated support (12h)",
            "60% better value"
        ]
    }
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
    
    # Create user with 10 free starter credits
    user = User(
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        full_name=user_data.full_name,
        credits_balance=10,  # Free starter credits
        credits_purchased_total=0,
        api_access_unlocked=False,
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
    check_user_has_credits(current_user)
    
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
        credits_balance=current_user.credits_balance,
        credits_lifetime_used=current_user.credits_lifetime_used,
        credits_purchased_total=current_user.credits_purchased_total,
        api_access_unlocked=current_user.api_access_unlocked,
        support_tier=current_user.support_tier
    )


# ============================================================================
# STRIPE INTEGRATION
# ============================================================================

@app.post("/api/purchase-credits", response_model=CheckoutSession)
async def purchase_credits(
    request: CheckoutSessionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create Stripe checkout session for credit pack purchase (one-time payment)"""
    pack = request.tier  # Reusing 'tier' field for pack name
    if pack not in CREDIT_PACKS:
        raise HTTPException(status_code=400, detail="Invalid credit pack")
    
    pack_config = CREDIT_PACKS[pack]
    
    try:
        # Create Stripe customer if doesn't exist
        if not current_user.stripe_customer_id:
            customer = stripe.Customer.create(
                email=current_user.email,
                metadata={"user_id": current_user.id}
            )
            current_user.stripe_customer_id = customer.id
            db.commit()
        
        # Create checkout session for ONE-TIME PAYMENT
        session = stripe.checkout.Session.create(
            customer=current_user.stripe_customer_id,
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": pack_config["name"],
                        "description": f"{pack_config['credits']} credits - Never expire!",
                    },
                    "unit_amount": pack_config["price"],
                },
                "quantity": 1,
            }],
            mode="payment",  # ONE-TIME PAYMENT, not subscription!
            metadata={
                "pack": pack,
                "credits": pack_config["credits"],
                "unlocks_api": str(pack_config["unlocks_api"]),
                "user_id": current_user.id
            },
            success_url=os.getenv("FRONTEND_URL", "http://localhost:5000") + "/success?credits=" + str(pack_config["credits"]),
            cancel_url=os.getenv("FRONTEND_URL", "http://localhost:5000") + "/#pricing",
        )
        
        return CheckoutSession(session_id=session.id, url=session.url)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stripe error: {str(e)}")


@app.post("/api/webhook/stripe")
async def stripe_webhook(request: dict, db: Session = Depends(get_db)):
    """Handle Stripe webhooks for credit pack purchases"""
    # In production, verify signature with:
    # sig_header = request.headers.get('stripe-signature')
    # event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    
    event_type = request.get("type")
    
    if event_type == "checkout.session.completed":
        session = request.get("data", {}).get("object", {})
        
        # Get metadata from session
        metadata = session.get("metadata", {})
        user_id = metadata.get("user_id")
        credits = int(metadata.get("credits", 0))
        unlocks_api = metadata.get("unlocks_api") == "True"
        
        if user_id and credits > 0:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                # Add credits to user balance
                user.add_credits(credits, unlocks_api=unlocks_api)
                db.commit()
                
                print(f"✅ Added {credits} credits to user {user.email}, API unlocked: {unlocks_api}")
    
    return {"status": "success"}


# ============================================================================
# ADMIN ENDPOINTS (optional)
# ============================================================================

@app.get("/api/admin/users")
async def list_users(db: Session = Depends(get_db)):
    """List all users (admin only - add auth later)"""
    users = db.query(User).all()
    return [{
        "id": u.id,
        "email": u.email,
        "credits_balance": u.credits_balance,
        "credits_purchased_total": u.credits_purchased_total,
        "api_access_unlocked": u.api_access_unlocked,
        "support_tier": u.support_tier
    } for u in users]


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
    check_user_has_credits(current_user)
    
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
# QR CODE GENERATOR
# ============================================================================

from tools import generate_qr_code, resize_image, bulk_resize_images, merge_pdfs, split_pdf, compress_pdf

@app.post("/api/qr-code/generate")
async def generate_qr(
    data: str = Form(...),
    size: int = Form(300),
    error_correction: str = Form("M"),
    current_user: User = Depends(require_credits),
    db: Session = Depends(get_db)
):
    """
    Generate a QR code (costs 1 credit)
    
    Args:
        data: Text or URL to encode
        size: Size in pixels (default 300)
        error_correction: L, M, Q, H (default M)
    """
    try:
        start_time = datetime.utcnow()
        
        # Generate QR code
        qr_bytes = generate_qr_code(data, size=size, error_correction=error_correction)
        
        # Generate unique ID
        file_id = str(uuid.uuid4())
        output_filename = f"{file_id}_qrcode.png"
        output_path = OUTPUT_DIR / output_filename
        
        # Save file
        with open(output_path, "wb") as f:
            f.write(qr_bytes)
        
        # Deduct credit
        current_user.use_credit()
        
        # Record usage
        processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        usage_record = UsageRecord(
            user_id=current_user.id,
            original_filename=f"qr_{data[:30]}",
            file_id=file_id,
            output_format="png",
            original_size=len(data),
            output_size=len(qr_bytes),
            processing_time=processing_time
        )
        db.add(usage_record)
        db.commit()
        
        return {
            "success": True,
            "file_id": file_id,
            "download_url": f"/outputs/{output_filename}",
            "credits_remaining": current_user.credits_remaining,
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"QR generation error: {str(e)}")


@app.post("/api/barcode/generate")
async def generate_barcode_endpoint(
    data: str = Form(...),
    barcode_type: str = Form("code128"),
    show_text: bool = Form(True),
    current_user: User = Depends(require_credits),
    db: Session = Depends(get_db)
):
    """
    Generate a barcode (costs 1 credit)
    
    Args:
        data: Data to encode
        barcode_type: code128, code39, ean13, upca, etc.
        show_text: Whether to show human-readable text below barcode
    """
    try:
        import barcode
        from barcode.writer import ImageWriter
        import io as barcode_io
        
        start_time = datetime.utcnow()
        
        # Validate and clean data based on type
        data = data.strip()
        
        # Map frontend names to barcode library names
        type_map = {
            'code128': 'code128',
            'code39': 'code39',
            'ean13': 'ean13',
            'ean8': 'ean8',
            'upca': 'upca',
            'jan': 'jan',
            'isbn13': 'isbn13',
            'isbn10': 'isbn10',
            'issn': 'issn'
        }
        
        barcode_class_name = type_map.get(barcode_type.lower(), 'code128')
        
        # Get barcode class
        try:
            barcode_class = barcode.get_barcode_class(barcode_class_name)
        except:
            raise HTTPException(status_code=400, detail=f"Invalid barcode type: {barcode_type}")
        
        # Generate barcode
        try:
            barcode_instance = barcode_class(data, writer=ImageWriter())
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid data for {barcode_type}: {str(e)}")
        
        # Save to bytes
        buffer = barcode_io.BytesIO()
        barcode_instance.write(buffer, options={
            'module_width': 0.3,
            'module_height': 12.0,
            'quiet_zone': 2.5,
            'font_size': 10,
            'text_distance': 5.0,
            'write_text': show_text
        })
        barcode_bytes = buffer.getvalue()
        
        # Generate unique ID
        file_id = str(uuid.uuid4())
        output_filename = f"{file_id}_barcode.png"
        output_path = OUTPUT_DIR / output_filename
        
        # Save file
        with open(output_path, "wb") as f:
            f.write(barcode_bytes)
        
        # Deduct credit
        current_user.use_credit()
        
        # Record usage
        processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        usage_record = UsageRecord(
            user_id=current_user.id,
            original_filename=f"barcode_{data[:30]}",
            file_id=file_id,
            output_format="png",
            original_size=len(data),
            output_size=len(barcode_bytes),
            processing_time=processing_time
        )
        db.add(usage_record)
        db.commit()
        
        return {
            "success": True,
            "file_id": file_id,
            "download_url": f"/outputs/{output_filename}",
            "barcode_type": barcode_type,
            "credits_remaining": current_user.credits_remaining,
            "timestamp": datetime.utcnow()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Barcode generation error: {str(e)}")


# ============================================================================
# IMAGE RESIZE
# ============================================================================

@app.post("/api/resize/single")
async def resize_single_image(
    file: UploadFile = File(...),
    width: int = Form(None),
    height: int = Form(None),
    format: str = Form("png"),
    maintain_aspect: str = Form("true"),
    current_user: User = Depends(require_credits),
    db: Session = Depends(get_db)
):
    """
    Resize a single image (costs 1 credit)
    """
    # Validate file type
    allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    contents = await file.read()
    
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Max 10MB")
    
    # Convert string to boolean
    maintain_aspect_bool = maintain_aspect.lower() == "true"
    
    try:
        start_time = datetime.utcnow()
        
        # Resize image
        resized_bytes = resize_image(contents, width=width, height=height, maintain_aspect=maintain_aspect_bool, format=format)
        
        # Save file
        file_id = str(uuid.uuid4())
        ext = format.lower() if format.lower() != "jpeg" else "jpg"
        output_filename = f"{file_id}_resized.{ext}"
        output_path = OUTPUT_DIR / output_filename
        
        with open(output_path, "wb") as f:
            f.write(resized_bytes)
        
        # Deduct credit
        current_user.use_credit()
        
        # Record usage
        processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        usage_record = UsageRecord(
            user_id=current_user.id,
            original_filename=file.filename,
            file_id=file_id,
            output_format=format,
            original_size=len(contents),
            output_size=len(resized_bytes),
            processing_time=processing_time
        )
        db.add(usage_record)
        db.commit()
        
        return {
            "success": True,
            "file_id": file_id,
            "download_url": f"/outputs/{output_filename}",
            "original_size": len(contents),
            "output_size": len(resized_bytes),
            "credits_remaining": current_user.credits_remaining,
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Resize error: {str(e)}")


# ============================================================================
# IMAGE FORMAT CONVERTER
# ============================================================================

@app.post("/api/convert/format")
async def convert_image_format(
    file: UploadFile = File(...),
    to_format: str = Form(...),
    quality: int = Form(100),
    current_user: User = Depends(require_credits),
    db: Session = Depends(get_db)
):
    """
    Convert image between formats (costs 1 credit)
    
    Args:
        to_format: Target format (png, jpg, webp, bmp, tiff)
        quality: Output quality 1-100 (for lossy formats like JPG/WebP only)
    """
    # Validate file type
    allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/webp", "image/bmp", "image/tiff", "image/heic"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid image format")
    
    # Validate target format
    to_format = to_format.lower()
    valid_formats = ["png", "jpg", "jpeg", "webp", "bmp", "tiff"]
    if to_format not in valid_formats:
        raise HTTPException(status_code=400, detail=f"Invalid target format. Allowed: {', '.join(valid_formats)}")
    
    contents = await file.read()
    
    if len(contents) > 20 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Max 20MB")
    
    try:
        start_time = datetime.utcnow()
        
        # Open image
        input_image = Image.open(io.BytesIO(contents))
        
        # Convert RGBA to RGB if saving as JPEG
        if to_format in ["jpg", "jpeg"] and input_image.mode in ["RGBA", "LA", "P"]:
            # Create white background
            rgb_image = Image.new("RGB", input_image.size, (255, 255, 255))
            if input_image.mode == "P":
                input_image = input_image.convert("RGBA")
            rgb_image.paste(input_image, mask=input_image.split()[-1] if input_image.mode in ["RGBA", "LA"] else None)
            input_image = rgb_image
        
        # Save in new format
        output_buffer = io.BytesIO()
        save_format = "JPEG" if to_format in ["jpg", "jpeg"] else to_format.upper()
        
        # Quality settings
        save_kwargs = {}
        if to_format in ["jpg", "jpeg", "webp"]:
            save_kwargs["quality"] = min(max(quality, 1), 100)
            save_kwargs["optimize"] = True
        elif to_format == "png":
            save_kwargs["optimize"] = True
        
        input_image.save(output_buffer, format=save_format, **save_kwargs)
        output_bytes = output_buffer.getvalue()
        
        # Save file
        file_id = str(uuid.uuid4())
        ext = "jpg" if to_format == "jpeg" else to_format
        original_name = Path(file.filename).stem
        output_filename = f"{original_name}_converted_{file_id[:8]}.{ext}"
        output_path = OUTPUT_DIR / output_filename
        
        with open(output_path, "wb") as f:
            f.write(output_bytes)
        
        # Deduct credit
        current_user.use_credit()
        
        # Record usage
        processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        usage_record = UsageRecord(
            user_id=current_user.id,
            original_filename=file.filename,
            file_id=file_id,
            output_format=to_format,
            original_size=len(contents),
            output_size=len(output_bytes),
            processing_time=processing_time
        )
        db.add(usage_record)
        db.commit()
        
        return {
            "success": True,
            "file_id": file_id,
            "download_url": f"/outputs/{output_filename}",
            "original_format": file.content_type.split("/")[-1],
            "output_format": ext,
            "original_size": len(contents),
            "output_size": len(output_bytes),
            "size_change_percent": round((len(output_bytes) - len(contents)) / len(contents) * 100, 1),
            "credits_remaining": current_user.credits_remaining,
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Conversion error: {str(e)}")


# ============================================================================
# IMAGE COMPRESSION
# ============================================================================

@app.post("/api/compress/image")
async def compress_image(
    file: UploadFile = File(...),
    quality: int = Form(85),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Compress image - Preview FREE, download costs 1 credit
    
    Args:
        quality: Compression quality 1-100 (default 85 = good balance)
    
    Returns preview with watermark. Use /api/download/{file_id} to get clean version.
    """
    # Validate file type
    allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid image format. Supported: JPG, PNG, WebP")
    
    contents = await file.read()
    
    if len(contents) > 20 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Max 20MB")
    
    try:
        start_time = datetime.utcnow()
        
        # Open image
        input_image = Image.open(io.BytesIO(contents))
        original_format = input_image.format or "JPEG"
        
        # Determine output format (keep original)
        if original_format.upper() in ["JPEG", "JPG"]:
            output_format = "JPEG"
            ext = "jpg"
        elif original_format.upper() == "PNG":
            output_format = "PNG"
            ext = "png"
        elif original_format.upper() == "WEBP":
            output_format = "WEBP"
            ext = "webp"
        else:
            output_format = "JPEG"
            ext = "jpg"
        
        # Convert RGBA to RGB if needed for JPEG
        if output_format == "JPEG" and input_image.mode in ["RGBA", "LA", "P"]:
            rgb_image = Image.new("RGB", input_image.size, (255, 255, 255))
            if input_image.mode == "P":
                input_image = input_image.convert("RGBA")
            rgb_image.paste(input_image, mask=input_image.split()[-1] if input_image.mode in ["RGBA", "LA"] else None)
            input_image = rgb_image
        
        # Compress with quality settings
        output_buffer = io.BytesIO()
        save_kwargs = {
            "optimize": True,
            "quality": min(max(quality, 1), 100)
        }
        
        # PNG-specific optimization
        if output_format == "PNG":
            # For PNG, quality doesn't apply but we can optimize
            # Lower quality means more aggressive optimization
            save_kwargs.pop("quality")
            save_kwargs["compress_level"] = 9  # Maximum compression
        
        input_image.save(output_buffer, format=output_format, **save_kwargs)
        output_bytes = output_buffer.getvalue()
        
        # Generate file ID
        file_id = str(uuid.uuid4())
        original_name = Path(file.filename).stem
        
        # Save CLEAN version (for download later)
        clean_filename = f"{file_id}_clean.{ext}"
        clean_path = OUTPUT_DIR / clean_filename
        with open(clean_path, "wb") as f:
            f.write(output_bytes)
        
        # Create PREVIEW version (with watermark)
        compressed_image = Image.open(io.BytesIO(output_bytes))
        watermarked_image = add_watermark(compressed_image)
        
        # Convert RGBA back to RGB for JPEG (watermark adds alpha channel)
        if output_format == "JPEG" and watermarked_image.mode == "RGBA":
            rgb_image = Image.new("RGB", watermarked_image.size, (255, 255, 255))
            rgb_image.paste(watermarked_image, mask=watermarked_image.split()[-1])
            watermarked_image = rgb_image
        
        preview_filename = f"{file_id}_preview.{ext}"
        preview_path = OUTPUT_DIR / preview_filename
        watermarked_image.save(preview_path, format=output_format, **save_kwargs)
        
        # Calculate savings
        size_reduction = len(contents) - len(output_bytes)
        reduction_percent = round((size_reduction / len(contents)) * 100, 1)
        
        # NO credit deduction yet - only on download!
        
        return {
            "success": True,
            "file_id": file_id,
            "preview_url": f"/outputs/{preview_filename}",
            "download_url": f"/api/download/{file_id}",
            "original_size": len(contents),
            "compressed_size": len(output_bytes),
            "size_reduction": size_reduction,
            "reduction_percent": reduction_percent,
            "credits_remaining": current_user.credits_remaining,
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Compression error: {str(e)}")


@app.post("/api/watermark/add")
async def add_custom_watermark(
    file: UploadFile = File(...),
    text: str = Form(...),
    position: str = Form("tiled"),
    opacity: int = Form(60),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add custom watermark to image - Preview FREE, download costs 1 credit
    
    Args:
        text: Watermark text (e.g., "© 2026 Your Name")
        position: tiled, bottom-right, bottom-left, top-right, top-left, center
        opacity: 1-100 (default 60 = semi-transparent)
    
    Returns preview with your watermark. Use /api/download/{file_id} to get full version.
    """
    # Validate file type
    allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid image format. Supported: JPG, PNG, WebP")
    
    contents = await file.read()
    
    if len(contents) > 20 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Max 20MB")
    
    if not text or len(text.strip()) == 0:
        raise HTTPException(status_code=400, detail="Watermark text is required")
    
    if len(text) > 100:
        raise HTTPException(status_code=400, detail="Watermark text too long (max 100 characters)")
    
    # Validate opacity
    opacity = min(max(opacity, 1), 100)
    
    try:
        start_time = datetime.utcnow()
        
        # Open image
        input_image = Image.open(io.BytesIO(contents))
        original_format = input_image.format or "PNG"
        
        # Convert to RGBA for watermarking
        if input_image.mode != 'RGBA':
            input_image = input_image.convert('RGBA')
        
        # Apply custom watermark based on position
        watermarked_image = apply_custom_watermark(
            input_image, 
            text, 
            position, 
            opacity
        )
        
        # Determine output format
        if original_format.upper() in ["JPEG", "JPG"]:
            output_format = "JPEG"
            ext = "jpg"
            # Convert to RGB for JPEG
            rgb_image = Image.new("RGB", watermarked_image.size, (255, 255, 255))
            rgb_image.paste(watermarked_image, mask=watermarked_image.split()[-1])
            watermarked_image = rgb_image
        elif original_format.upper() == "PNG":
            output_format = "PNG"
            ext = "png"
        elif original_format.upper() == "WEBP":
            output_format = "WEBP"
            ext = "webp"
        else:
            output_format = "PNG"
            ext = "png"
        
        # Save watermarked version
        output_buffer = io.BytesIO()
        save_kwargs = {"optimize": True}
        if output_format == "JPEG":
            save_kwargs["quality"] = 95
        
        watermarked_image.save(output_buffer, format=output_format, **save_kwargs)
        output_bytes = output_buffer.getvalue()
        
        # Generate file ID
        file_id = str(uuid.uuid4())
        original_name = Path(file.filename).stem
        
        # Save CLEAN version (full quality watermarked - for download)
        clean_filename = f"{file_id}_clean.{ext}"
        clean_path = OUTPUT_DIR / clean_filename
        with open(clean_path, "wb") as f:
            f.write(output_bytes)
        
        # Create PREVIEW version (lower quality + preview watermark)
        preview_watermarked = add_watermark(watermarked_image, "PREVIEW")
        
        preview_filename = f"{file_id}_preview.{ext}"
        preview_path = OUTPUT_DIR / preview_filename
        
        # Convert to RGB if needed for JPEG preview
        if output_format == "JPEG" and preview_watermarked.mode == "RGBA":
            rgb_preview = Image.new("RGB", preview_watermarked.size, (255, 255, 255))
            rgb_preview.paste(preview_watermarked, mask=preview_watermarked.split()[-1])
            preview_watermarked = rgb_preview
        
        preview_watermarked.save(preview_path, format=output_format, quality=85 if output_format == "JPEG" else None)
        
        # NO credit deduction yet - only on download!
        
        return {
            "success": True,
            "file_id": file_id,
            "preview_url": f"/outputs/{preview_filename}",
            "download_url": f"/api/download/{file_id}",
            "original_size": len(contents),
            "watermarked_size": len(output_bytes),
            "watermark_text": text,
            "position": position,
            "credits_remaining": current_user.credits_balance,
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Watermark error: {str(e)}")


def apply_custom_watermark(image: Image.Image, text: str, position: str, opacity: int) -> Image.Image:
    """
    Apply custom watermark to image
    
    Args:
        image: PIL Image (RGBA mode)
        text: Watermark text
        position: tiled, bottom-right, bottom-left, top-right, top-left, center
        opacity: 1-100
    
    Returns:
        Watermarked PIL Image (RGBA)
    """
    from PIL import ImageDraw, ImageFont
    import math
    
    watermarked = image.copy()
    overlay = Image.new('RGBA', watermarked.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    width, height = watermarked.size
    font_size = max(int(min(width, height) / 20), 24)
    
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
    except:
        font = ImageFont.load_default()
    
    # Calculate text size
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Calculate opacity (0-255)
    alpha = int((opacity / 100) * 255)
    
    if position == "tiled":
        # Tile watermark across ENTIRE image (diagonal pattern)
        x_spacing = text_width * 2
        y_spacing = text_height * 3
        
        # Need extra tiles to cover image after rotation (diagonal adds area)
        diagonal = math.sqrt(width**2 + height**2)
        x_count = int(diagonal / x_spacing) + 2
        y_count = int(diagonal / y_spacing) + 2
        
        # Start from negative to ensure full coverage after rotation
        x_start = -int(diagonal / 4)
        y_start = -int(diagonal / 4)
        
        # Draw grid that covers entire image + margins for rotation
        for i in range(x_count):
            for j in range(y_count):
                x = x_start + (i * x_spacing)
                y = y_start + (j * y_spacing)
                draw.text(
                    (x, y), text, font=font,
                    fill=(255, 255, 255, alpha),
                    stroke_width=2,
                    stroke_fill=(0, 0, 0, int(alpha * 0.7))
                )
        
        # Rotate for diagonal effect (around center)
        overlay = overlay.rotate(-25, expand=False, resample=Image.Resampling.BICUBIC)
    
    else:
        # Corner/center positioning
        padding = 30
        
        if position == "bottom-right":
            x = width - text_width - padding
            y = height - text_height - padding
        elif position == "bottom-left":
            x = padding
            y = height - text_height - padding
        elif position == "top-right":
            x = width - text_width - padding
            y = padding
        elif position == "top-left":
            x = padding
            y = padding
        elif position == "center":
            x = (width - text_width) // 2
            y = (height - text_height) // 2
        else:
            x = width - text_width - padding
            y = height - text_height - padding
        
        # Draw with shadow
        shadow_offset = 3
        draw.text(
            (x + shadow_offset, y + shadow_offset), text, font=font,
            fill=(0, 0, 0, int(alpha * 0.6))
        )
        draw.text((x, y), text, font=font, fill=(255, 255, 255, alpha))
    
    # Composite watermark onto image
    watermarked = Image.alpha_composite(watermarked, overlay)
    
    return watermarked


@app.post("/api/crop/image")
async def crop_image(
    file: UploadFile = File(...),
    x: int = Form(...),
    y: int = Form(...),
    width: int = Form(...),
    height: int = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Crop image with custom coordinates - Preview FREE, download costs 1 credit
    
    Args:
        x: Left coordinate (pixels)
        y: Top coordinate (pixels)
        width: Crop width (pixels)
        height: Crop height (pixels)
    
    Returns preview with watermark. Use /api/download/{file_id} to get clean version.
    """
    # Validate file type
    allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid image format. Supported: JPG, PNG, WebP")
    
    contents = await file.read()
    
    if len(contents) > 20 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Max 20MB")
    
    try:
        start_time = datetime.utcnow()
        
        # Open image
        input_image = Image.open(io.BytesIO(contents))
        original_format = input_image.format or "JPEG"
        original_width, original_height = input_image.size
        
        # Validate crop coordinates
        if x < 0 or y < 0 or width <= 0 or height <= 0:
            raise HTTPException(status_code=400, detail="Invalid crop coordinates")
        
        if x + width > original_width or y + height > original_height:
            raise HTTPException(status_code=400, detail="Crop area exceeds image bounds")
        
        # Crop image using provided coordinates
        cropped_image = input_image.crop((x, y, x + width, y + height))
        
        # Determine output format
        if original_format.upper() in ["JPEG", "JPG"]:
            output_format = "JPEG"
            ext = "jpg"
        elif original_format.upper() == "PNG":
            output_format = "PNG"
            ext = "png"
        elif original_format.upper() == "WEBP":
            output_format = "WEBP"
            ext = "webp"
        else:
            output_format = "JPEG"
            ext = "jpg"
        
        # Convert RGBA to RGB for JPEG
        if output_format == "JPEG" and cropped_image.mode in ["RGBA", "LA", "P"]:
            rgb_image = Image.new("RGB", cropped_image.size, (255, 255, 255))
            if cropped_image.mode == "P":
                cropped_image = cropped_image.convert("RGBA")
            rgb_image.paste(cropped_image, mask=cropped_image.split()[-1] if cropped_image.mode in ["RGBA", "LA"] else None)
            cropped_image = rgb_image
        
        # Save CLEAN version
        clean_buffer = io.BytesIO()
        save_kwargs = {"optimize": True}
        if output_format == "JPEG":
            save_kwargs["quality"] = 95
        
        cropped_image.save(clean_buffer, format=output_format, **save_kwargs)
        clean_bytes = clean_buffer.getvalue()
        
        # Generate file ID
        file_id = str(uuid.uuid4())
        original_name = Path(file.filename).stem
        
        # Save CLEAN cropped version (for download)
        clean_filename = f"{file_id}_clean.{ext}"
        clean_path = OUTPUT_DIR / clean_filename
        with open(clean_path, "wb") as f:
            f.write(clean_bytes)
        
        # Create PREVIEW version (with watermark)
        if cropped_image.mode != 'RGBA':
            cropped_image = cropped_image.convert('RGBA')
        
        watermarked_image = add_watermark(cropped_image, "PREVIEW")
        
        # Convert back to RGB if needed for JPEG
        if output_format == "JPEG" and watermarked_image.mode == "RGBA":
            rgb_preview = Image.new("RGB", watermarked_image.size, (255, 255, 255))
            rgb_preview.paste(watermarked_image, mask=watermarked_image.split()[-1])
            watermarked_image = rgb_preview
        
        preview_filename = f"{file_id}_preview.{ext}"
        preview_path = OUTPUT_DIR / preview_filename
        watermarked_image.save(preview_path, format=output_format, quality=85 if output_format == "JPEG" else None)
        
        # NO credit deduction yet - only on download!
        
        # Calculate aspect ratio for display
        aspect_ratio = f"{width}:{height}"
        gcd_val = math.gcd(width, height)
        if gcd_val > 1:
            aspect_ratio = f"{width//gcd_val}:{height//gcd_val}"
        
        return {
            "success": True,
            "file_id": file_id,
            "preview_url": f"/outputs/{preview_filename}",
            "download_url": f"/api/download/{file_id}",
            "original_size": f"{original_width}x{original_height}",
            "cropped_size": f"{width}x{height}",
            "aspect_ratio": aspect_ratio,
            "credits_remaining": current_user.credits_balance,
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Crop error: {str(e)}")


# ============================================================================
# PDF TOOLS
# ============================================================================

@app.post("/api/pdf/merge")
async def merge_pdf_files(
    files: List[UploadFile] = File(...),
    current_user: User = Depends(require_credits),
    db: Session = Depends(get_db)
):
    """
    Merge multiple PDF files (costs 1 credit)
    """
    if len(files) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 PDFs to merge")
    
    pdf_bytes_list = []
    
    for file in files:
        if file.content_type != "application/pdf":
            raise HTTPException(status_code=400, detail=f"File {file.filename} is not a PDF")
        
        contents = await file.read()
        
        if len(contents) > 20 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="PDF too large. Max 20MB per file")
        
        pdf_bytes_list.append(contents)
    
    try:
        start_time = datetime.utcnow()
        
        # Merge PDFs
        merged_bytes = merge_pdfs(pdf_bytes_list)
        
        # Save file
        file_id = str(uuid.uuid4())
        output_filename = f"{file_id}_merged.pdf"
        output_path = OUTPUT_DIR / output_filename
        
        with open(output_path, "wb") as f:
            f.write(merged_bytes)
        
        # Deduct credit
        current_user.use_credit()
        
        # Record usage
        processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        usage_record = UsageRecord(
            user_id=current_user.id,
            original_filename=f"merge_{len(files)}_pdfs",
            file_id=file_id,
            output_format="pdf",
            original_size=sum(len(b) for b in pdf_bytes_list),
            output_size=len(merged_bytes),
            processing_time=processing_time
        )
        db.add(usage_record)
        db.commit()
        
        return {
            "success": True,
            "file_id": file_id,
            "download_url": f"/outputs/{output_filename}",
            "files_merged": len(files),
            "output_size": len(merged_bytes),
            "credits_remaining": current_user.credits_remaining,
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"PDF merge error: {str(e)}")


@app.post("/api/pdf/split")
async def split_pdf_file(
    file: UploadFile = File(...),
    pages: str = Form("all"),
    current_user: User = Depends(require_credits),
    db: Session = Depends(get_db)
):
    """
    Split a PDF into separate pages (costs 1 credit)
    
    Args:
        pages: "all" or "1-3,5,7-9" for specific pages/ranges
    """
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    contents = await file.read()
    
    if len(contents) > 20 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="PDF too large. Max 20MB")
    
    try:
        start_time = datetime.utcnow()
        
        # Split PDF
        split_pdfs = split_pdf(contents, pages=pages)
        
        # Save files with original filename base
        file_id = str(uuid.uuid4())
        download_urls = []
        
        # Get original filename without extension
        original_name = Path(file.filename).stem
        
        for idx, pdf_bytes in enumerate(split_pdfs, 1):
            output_filename = f"{original_name}_page{idx}_{file_id[:8]}.pdf"
            output_path = OUTPUT_DIR / output_filename
            
            with open(output_path, "wb") as f:
                f.write(pdf_bytes)
            
            download_urls.append(f"/outputs/{output_filename}")
        
        # Deduct credit
        current_user.use_credit()
        
        # Record usage
        processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        usage_record = UsageRecord(
            user_id=current_user.id,
            original_filename=file.filename,
            file_id=file_id,
            output_format="pdf",
            original_size=len(contents),
            output_size=sum(len(p) for p in split_pdfs),
            processing_time=processing_time
        )
        db.add(usage_record)
        db.commit()
        
        return {
            "success": True,
            "file_id": file_id,
            "download_urls": download_urls,
            "pages_count": len(split_pdfs),
            "credits_remaining": current_user.credits_remaining,
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"PDF split error: {str(e)}")


@app.post("/api/pdf/compress")
async def compress_pdf_file(
    file: UploadFile = File(...),
    current_user: User = Depends(require_credits),
    db: Session = Depends(get_db)
):
    """
    Compress a PDF file (costs 1 credit)
    """
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    contents = await file.read()
    
    if len(contents) > 20 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="PDF too large. Max 20MB")
    
    try:
        start_time = datetime.utcnow()
        
        # Compress PDF
        compressed_bytes = compress_pdf(contents)
        
        # Save file
        file_id = str(uuid.uuid4())
        output_filename = f"{file_id}_compressed.pdf"
        output_path = OUTPUT_DIR / output_filename
        
        with open(output_path, "wb") as f:
            f.write(compressed_bytes)
        
        # Deduct credit
        current_user.use_credit()
        
        # Record usage
        processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        compression_ratio = (1 - len(compressed_bytes) / len(contents)) * 100
        
        usage_record = UsageRecord(
            user_id=current_user.id,
            original_filename=file.filename,
            file_id=file_id,
            output_format="pdf",
            original_size=len(contents),
            output_size=len(compressed_bytes),
            processing_time=processing_time
        )
        db.add(usage_record)
        db.commit()
        
        return {
            "success": True,
            "file_id": file_id,
            "download_url": f"/outputs/{output_filename}",
            "original_size": len(contents),
            "compressed_size": len(compressed_bytes),
            "compression_ratio": f"{compression_ratio:.1f}%",
            "credits_remaining": current_user.credits_remaining,
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"PDF compression error: {str(e)}")


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
    # Get support tier from user property (based on lifetime purchases)
    support_tier = current_user.support_tier
    
    # Log support request (in production, send email or create ticket)
    support_data = {
        "user_id": current_user.id,
        "email": current_user.email,
        "credits_purchased_total": current_user.credits_purchased_total,
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
