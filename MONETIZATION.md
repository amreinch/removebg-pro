# RemoveBG Pro - Monetization System

## 💰 Complete Freemium Model with Stripe Integration

**Updated:** 2026-02-08 - New pricing model implemented

---

## 🎯 Business Model

### Freemium Strategy: Preview → Test → Convert

**New Model (2026-02-08):**

1. **Preview is FREE** → Unlimited watermarked previews
2. **Test Quality** → Users can test as many images as they want
3. **Download Costs Credit** → Only pay when downloading clean version
4. **Convert to Paid** → Better UX drives higher conversion

**Why This Works:**
- Lower barrier to entry (no credit anxiety)
- Users see full value before spending
- "Try before you buy" for every image
- Higher conversion rates (users know exactly what they're getting)

---

## 📊 Subscription Tiers

### Updated Pricing (2026-02-08)

**Key Change:** Preview is UNLIMITED & FREE for all tiers. Credits = Downloads only.

### Free
- **Price:** $0/month
- **Preview:** ✅ Unlimited (watermarked)
- **Downloads:** 3/month (clean, no watermark)
- **Resolution:** Full
- **API Access:** No
- **Support:** Community

### Basic
- **Price:** $5/month
- **Preview:** ✅ Unlimited (watermarked)
- **Downloads:** 50/month (clean, no watermark)
- **Resolution:** Full
- **API Access:** No
- **Support:** Email

### Pro
- **Price:** $15/month
- **Preview:** ✅ Unlimited (watermarked)
- **Downloads:** 500/month (clean, no watermark)
- **Resolution:** Full
- **API Access:** Yes
- **Support:** Priority email

### Business
- **Price:** $50/month
- **Preview:** ✅ Unlimited (watermarked)
- **Downloads:** 5,000/month (clean, no watermark)
- **Resolution:** Full
- **API Access:** Yes
- **Support:** Priority + Custom integrations

---

## 🎨 Watermark System

### How It Works (Updated)

**ALL USERS (Free + Paid):**
1. Upload image ✅
2. AI processes (removes background) ✅
3. Preview shows result WITH watermark overlay ✅ **FREE & UNLIMITED**
4. Click "Download" to get clean version:
   - **Free users:** Use 1 of 3 monthly credits
   - **Paid users:** Use 1 of 50/500/5000 monthly credits
5. Download is clean (no watermark) ✅

**Key Benefits:**
- Users can test unlimited images for free
- No risk of "wasting" a credit on a bad result
- Clear value proposition (preview vs download)
- Lower friction → higher conversion

### Watermark Design

**Diagonal tiled pattern:**
```
┌────────────────────────┐
│  RemoveBG  RemoveBG   │
│   Pro       Pro        │
│  RemoveBG  RemoveBG   │
│   Pro       Pro        │
└────────────────────────┘
```

**Features:**
- Semi-transparent (30% opacity)
- Repeated pattern (can't crop out)
- Still shows quality clearly
- Professional appearance
- Non-destructive

**Implementation:** `watermark.py`

---

## 🔐 Authentication Flow

### Signup

```
POST /api/auth/signup
{
  "email": "user@example.com",
  "password": "secure-password",
  "full_name": "John Doe"
}

Response:
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

**What happens:**
1. Check if email exists
2. Hash password (bcrypt, Python 3.14 compatible)
3. Create user in database
4. Set tier to "free" (3 downloads/month)
5. Generate JWT token (expires in 7 days)
6. Return token

### Login

```
POST /api/auth/login
{
  "email": "user@example.com",
  "password": "secure-password"
}

Response:
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

### Authenticated Requests

All subsequent requests include token in header:

```
Authorization: Bearer eyJ...
```

**Protected endpoints:**
- `/api/remove-background` - Process images (FREE preview)
- `/api/download/{file_id}` - Download clean version (costs 1 credit)
- `/api/stats` - User statistics
- `/api/create-checkout-session` - Upgrade subscription

---

## 💳 Credit System (Updated)

### How Credits Work

**Monthly allocation:**
- Free: 3 **downloads**/month (unlimited previews)
- Basic: 50 **downloads**/month (unlimited previews)
- Pro: 500 **downloads**/month (unlimited previews)
- Business: 5,000 **downloads**/month (unlimited previews)

**Credit usage:**
- Preview: **FREE** (unlimited, watermarked)
- Download: **1 credit** (clean version, no watermark)
- Credits reset on same day each month
- Unused credits don't roll over

**Credit tracking:**
```python
class User(Base):
    monthly_credits = Column(Integer, default=3)  # Downloads per month
    credits_used_this_month = Column(Integer, default=0)
    credits_reset_date = Column(DateTime, default=datetime.utcnow)
    
    @property
    def credits_remaining(self):
        return max(0, self.monthly_credits - self.credits_used_this_month)
    
    @property
    def can_process(self):
        # Preview is always allowed (free)
        return True
    
    @property
    def can_download(self):
        # Download requires credits
        return self.credits_remaining > 0
```

### Credit Deduction Flow (Updated)

**When user previews image:**
1. No credit check ✅
2. Process image
3. Add watermark
4. Return preview ✅ **FREE**

**When user downloads clean version:**
1. Check if user has credits (`check_user_credits()`)
2. If no credits → Return 403 error with upgrade prompt
3. Serve clean file (no watermark)
4. Deduct 1 credit (`user.use_credit()`)
5. Save to database
6. Return clean file

### Monthly Reset

**Automatic reset:**
```python
def reset_monthly_credits(self):
    self.credits_used_this_month = 0
    self.credits_reset_date = datetime.utcnow()
```

---

## 💰 Stripe Integration

### Setup Required

1. **Stripe Account** (https://stripe.com)
2. **Products Created** (Basic, Pro, Business)
3. **Price IDs** (monthly recurring)
4. **Webhook Endpoint** configured

See **STRIPE_SETUP.md** for complete configuration guide.

### Checkout Flow

**User clicks "Upgrade to Pro":**

```javascript
// Frontend (static/app.js)
async function checkout(tier) {
    const response = await fetch('/api/create-checkout-session', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ tier })
    });
    
    const data = await response.json();
    window.location.href = data.url; // Redirect to Stripe
}
```

**Backend creates Stripe session:**

```python
@app.post("/api/create-checkout-session")
async def create_checkout_session(tier: str, current_user: User):
    # Create/get Stripe customer
    if not current_user.stripe_customer_id:
        customer = stripe.Customer.create(
            email=current_user.email,
            metadata={"user_id": current_user.id}
        )
        current_user.stripe_customer_id = customer.id
    
    # Create checkout session
    session = stripe.checkout.Session.create(
        customer=current_user.stripe_customer_id,
        line_items=[{"price": STRIPE_PRICE_IDS[tier], "quantity": 1}],
        mode="subscription",
        success_url=FRONTEND_URL + "/success",
        cancel_url=FRONTEND_URL + "/pricing"
    )
    
    return {"session_id": session.id, "url": session.url}
```

### Webhook Handling

**Event: `checkout.session.completed`**
```python
# Payment successful → activate subscription
user.stripe_subscription_id = subscription_id
user.subscription_status = "active"
user.subscription_tier = "pro"  # or basic/business
user.monthly_credits = 500  # pro tier downloads
db.commit()
```

**Event: `customer.subscription.deleted`**
```python
# Subscription cancelled → downgrade to free
user.subscription_tier = "free"
user.subscription_status = "cancelled"
user.monthly_credits = 3
db.commit()
```

---

## 📈 Usage Tracking

### Database Models

**User:**
```python
class User(Base):
    id: str (UUID)
    email: str (unique)
    hashed_password: str
    subscription_tier: str (free/basic/pro/business)
    monthly_credits: int  # Downloads per month
    credits_used_this_month: int
    stripe_customer_id: str (nullable)
    stripe_subscription_id: str (nullable)
```

**UsageRecord:**
```python
class UsageRecord(Base):
    id: str (UUID)
    user_id: str (foreign key)
    original_filename: str
    file_id: str
    output_format: str
    original_size: int (bytes)
    output_size: int (bytes)
    processing_time: int (ms)
    created_at: datetime
```

---

## 🎨 Frontend Integration

### User Flow (Updated)

**New user journey:**

1. **Visit site** → See homepage
2. **Upload image** → Instant preview (no signup needed)
3. **See watermarked result** → "This is the quality you'll get!"
4. **Like it? Sign up** → Get 3 free downloads/month
5. **Download clean version** → Use 1 of 3 credits
6. **Need more?** → Upgrade to Basic ($5/mo, 50 downloads)

**Key improvement:** Users see quality BEFORE spending anything.

### UI Labels (Updated)

```javascript
// Credits display
"💾 3 / 50 downloads remaining"  // Not "credits"

// Watermark notice
"📸 Watermarked Preview (FREE)"
"This is a free preview. Click Download to get clean version (1 credit)."

// Download button
"💾 Download Clean Version (1 credit)"

// Pricing tiers
"Unlimited previews + 50 downloads/month"
```

---

## 📊 Revenue Projections (Updated)

### Why This Model Makes More Money

**Old Model Problems:**
- Users afraid to "waste" credits
- Low engagement (limited testing)
- High friction to first value

**New Model Benefits:**
- Users test unlimited (higher engagement)
- See quality before spending (higher conversion)
- Lower anxiety (no wasted credits)
- Better word-of-mouth (free tier actually useful)

### Conservative (Month 6)

- 3,000 free users (up from 2,000 - easier signup)
- 80 Basic ($5) = **$400/mo** (up from 50)
- 15 Pro ($15) = **$225/mo** (up from 10)
- 3 Business ($50) = **$150/mo** (up from 2)
- **Total: $775/month** (+55% vs old model)

### Moderate (Year 1)

- 15,000 free users (up from 10,000)
- 750 Basic = **$3,750/mo** (up from 500)
- 150 Pro = **$2,250/mo** (up from 100)
- 30 Business = **$1,500/mo** (up from 20)
- **Total: $7,500/month** ($90K/year, +50% vs old model)

### Target (Year 2)

- 75,000 free users (up from 50,000)
- 3,000 Basic = **$15,000/mo**
- 750 Pro = **$11,250/mo**
- 150 Business = **$7,500/mo**
- **Total: $33,750/month** ($405K/year, +50% vs old model)

**Conversion rates (expected higher):**
- Free → Paid: 4-7% (up from 2-5% due to lower friction)
- Basic → Pro: 20% (value upgrade)
- Churn: 3-7% monthly (down from 5-10% - better retention)

---

## 🎯 Conversion Optimization

### New Messaging

**Free tier CTA:**
> "Remove backgrounds from unlimited images. Preview for free, download 3 clean images/month. No credit card required."

**Upgrade prompt:**
> "You've used all 3 downloads this month. Upgrade to Basic for $5/mo and get 50 downloads + continue unlimited previews."

**Value proposition:**
> "Test unlimited images for free. Only pay when you download the clean version. Better than Photoshop, easier than manual editing."

### Tactics (Updated)

1. **Unlimited testing** - No fear of wasting credits
2. **Watermark quality preview** - See exact result before paying
3. **Clear pricing** - "Unlimited previews FREE, $5/mo for 50 downloads"
4. **Social proof** - "Join 15,000+ users testing unlimited"
5. **Urgency** - "Limited time: First month 50% off"
6. **Comparison** - "vs Remove.bg: $0.09/image = $4.50 for 50"
7. **Use cases** - "Perfect for e-commerce sellers, designers, marketers"

---

## ✅ Implementation Checklist

### Backend
- [x] User authentication (JWT + bcrypt Python 3.14 fix)
- [x] Database models (User, UsageRecord)
- [x] Credit system (downloads only)
- [x] Watermark generation (all previews)
- [x] Free preview endpoint (unlimited)
- [x] Download endpoint (costs 1 credit)
- [x] Stripe integration
- [x] Webhook handling
- [ ] Email notifications (future)
- [ ] API rate limiting (future)

### Frontend
- [x] Signup/login forms
- [x] Auth token storage
- [x] Pricing page (updated labels)
- [x] Checkout integration
- [x] User dashboard
- [x] Usage stats display (downloads)
- [x] Watermark notice (always shown)
- [x] Download button (credit check)

### Deployment
- [x] Docker configuration
- [x] Environment variables
- [x] Database persistence
- [ ] SSL certificate
- [ ] Domain setup
- [ ] Stripe production keys

---

## 📝 Migration Notes

**Changed from old model (2026-02-08):**

| Old Model | New Model |
|-----------|-----------|
| 3 credits = 3 full processes | 3 credits = 3 downloads |
| Preview + download = 1 credit | Preview FREE, download = 1 credit |
| Limited testing (credit anxiety) | Unlimited testing (no anxiety) |
| "3 images/month" | "Unlimited previews + 3 downloads/month" |
| Watermark only on free tier | Watermark on ALL previews (all tiers) |

**Backend changes:**
- `/api/remove-background` - No credit check, always returns watermarked preview
- `/api/download/{file_id}` - Added credit check, returns clean version
- Saves both `_preview.png` (watermarked) and `_clean.png` (no watermark)

**Frontend changes:**
- Removed credit check before preview
- Added credit check before download
- Updated all labels: "downloads" instead of "images"
- Watermark notice always visible

---

**Complete monetization system with improved UX! 💰**

Better conversion expected through unlimited free testing + clear value proposition.
