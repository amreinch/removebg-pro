# RemoveBG Pro - Monetization System

## 💰 Complete Freemium Model with Stripe Integration

This document explains how the monetization system works.

---

## 🎯 Business Model

### Freemium Strategy

**Free Tier** → **Paid Conversion** → **Retention**

Users get value immediately (free tier), see quality, then upgrade for more credits and no watermark.

---

## 📊 Subscription Tiers

### Free
- **Price:** $0/month
- **Credits:** 3 images/month
- **Watermark:** Yes (diagonal overlay)
- **Resolution:** Full
- **API Access:** No
- **Support:** Community

### Basic
- **Price:** $5/month
- **Credits:** 50 images/month
- **Watermark:** No
- **Resolution:** Full
- **API Access:** No
- **Support:** Email

### Pro
- **Price:** $15/month
- **Credits:** 500 images/month
- **Watermark:** No
- **Resolution:** Full
- **API Access:** Yes
- **Support:** Priority email

### Business
- **Price:** $50/month
- **Credits:** 5,000 images/month
- **Watermark:** No
- **Resolution:** Full
- **API Access:** Yes
- **Support:** Priority + Custom integrations

---

## 🎨 Watermark System

### How It Works

**Free users:**
1. Upload image ✅
2. AI processes (removes background) ✅
3. Preview shows result WITH watermark overlay ✅
4. Download includes watermark ✅

**Paid users:**
1. Upload image ✅
2. AI processes ✅
3. Preview shows result WITHOUT watermark ✅
4. Download is clean (no watermark) ✅

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
2. Hash password (bcrypt)
3. Create user in database
4. Set tier to "free" (3 credits/month)
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
- `/api/remove-background` - Process images
- `/api/download/{file_id}` - Download results
- `/api/stats` - User statistics
- `/api/create-checkout-session` - Upgrade subscription

---

## 💳 Credit System

### How Credits Work

**Monthly allocation:**
- Free: 3 credits/month
- Basic: 50 credits/month
- Pro: 500 credits/month
- Business: 5,000 credits/month

**Credit usage:**
- 1 credit = 1 image processed
- Credits reset on same day each month
- Unused credits don't roll over

**Credit tracking:**
```python
class User(Base):
    monthly_credits = Column(Integer, default=3)
    credits_used_this_month = Column(Integer, default=0)
    credits_reset_date = Column(DateTime, default=datetime.utcnow)
    
    @property
    def credits_remaining(self):
        return max(0, self.monthly_credits - self.credits_used_this_month)
    
    @property
    def can_process(self):
        return self.credits_remaining > 0
```

### Credit Deduction Flow

**When user processes image:**

1. Check if user has credits (`check_user_credits()`)
2. If no credits → Return 403 error
3. Process image
4. Deduct 1 credit (`user.use_credit()`)
5. Save to database
6. Return result with `credits_remaining` in response

### Monthly Reset

**Automatic reset:**
```python
def check_user_credits(user: User):
    # Reset if new month
    if (datetime.utcnow() - user.credits_reset_date).days >= 30:
        user.reset_monthly_credits()
```

**Manual reset (admin):**
```python
user.reset_monthly_credits()
db.commit()
```

---

## 💰 Stripe Integration

### Setup Required

1. **Stripe Account** (https://stripe.com)
2. **Products Created** (Basic, Pro, Business)
3. **Price IDs** (monthly recurring)
4. **Webhook Endpoint** configured

### Checkout Flow

**User clicks "Upgrade to Pro":**

```javascript
// Frontend
fetch('/api/create-checkout-session', {
    method: 'POST',
    headers: {
        'Authorization': 'Bearer ' + token,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({ tier: 'pro' })
})
.then(res => res.json())
.then(data => {
    // Redirect to Stripe Checkout
    window.location.href = data.url;
});
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

**User completes payment on Stripe:**
- Enters card details
- Stripe processes payment
- Redirects back to success page

### Webhook Handling

**Stripe sends events to `/api/webhook/stripe`:**

**Event: `checkout.session.completed`**
```python
# Payment successful
user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
user.stripe_subscription_id = subscription_id
user.subscription_status = "active"
user.subscription_tier = "pro"  # or basic/business
user.monthly_credits = 500  # pro tier
db.commit()
```

**Event: `customer.subscription.deleted`**
```python
# Subscription cancelled
user.subscription_tier = "free"
user.subscription_status = "cancelled"
user.monthly_credits = 3
db.commit()
```

**Event: `customer.subscription.updated`**
```python
# Plan changed (upgrade/downgrade)
# Update tier and credits accordingly
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
    monthly_credits: int
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

### Analytics Queries

**Total images processed:**
```python
total = db.query(UsageRecord).filter(UsageRecord.user_id == user.id).count()
```

**This month's usage:**
```python
from datetime import datetime, timedelta
month_ago = datetime.utcnow() - timedelta(days=30)
monthly = db.query(UsageRecord).filter(
    UsageRecord.user_id == user.id,
    UsageRecord.created_at >= month_ago
).count()
```

**Average processing time:**
```python
from sqlalchemy import func
avg_time = db.query(func.avg(UsageRecord.processing_time)).filter(
    UsageRecord.user_id == user.id
).scalar()
```

---

## 🎨 Frontend Integration

### Authentication UI

**Signup Form:**
```html
<form id="signupForm">
    <input type="email" name="email" required>
    <input type="password" name="password" minlength="8" required>
    <input type="text" name="full_name">
    <button type="submit">Sign Up</button>
</form>
```

**Login Form:**
```html
<form id="loginForm">
    <input type="email" name="email" required>
    <input type="password" name="password" required>
    <button type="submit">Log In</button>
</form>
```

**Store Token:**
```javascript
// After signup/login
localStorage.setItem('token', response.access_token);

// Include in all requests
headers: {
    'Authorization': 'Bearer ' + localStorage.getItem('token')
}
```

### Pricing Page

```html
<div class="pricing-tiers">
    <div class="tier free">
        <h3>Free</h3>
        <p class="price">$0/month</p>
        <ul>
            <li>3 images/month</li>
            <li>With watermark</li>
            <li>Full resolution</li>
        </ul>
        <button>Current Plan</button>
    </div>
    
    <div class="tier basic">
        <h3>Basic</h3>
        <p class="price">$5/month</p>
        <ul>
            <li>50 images/month</li>
            <li>No watermark</li>
            <li>Full resolution</li>
        </ul>
        <button onclick="checkout('basic')">Upgrade</button>
    </div>
    
    <!-- Pro and Business tiers -->
</div>
```

### Dashboard

```html
<div class="dashboard">
    <h2>Your Account</h2>
    
    <div class="stats">
        <div class="stat">
            <strong id="creditsRemaining">--</strong>
            <span>Credits Remaining</span>
        </div>
        <div class="stat">
            <strong id="creditsTotal">--</strong>
            <span>Monthly Credits</span>
        </div>
        <div class="stat">
            <strong id="totalProcessed">--</strong>
            <span>Total Processed</span>
        </div>
    </div>
    
    <div class="subscription">
        <h3>Current Plan: <span id="currentTier">Free</span></h3>
        <button onclick="showPricing()">Upgrade</button>
    </div>
</div>
```

---

## 🔄 User Journey

### New User (Free Tier)

1. **Visit site** → See homepage
2. **Try for free** → Upload image (no signup)
3. **See watermarked result** → "This is what you'll get!"
4. **Want clean version?** → Prompt to sign up
5. **Sign up** → Get 3 credits/month
6. **Process images** → Use 3 credits
7. **Need more?** → Upgrade prompt
8. **Upgrade to Basic** → $5/month, 50 credits, no watermark

### Upgrading User

1. **Click "Upgrade"** → See pricing page
2. **Choose plan** → Basic/Pro/Business
3. **Checkout** → Redirected to Stripe
4. **Enter payment** → Secure Stripe checkout
5. **Success** → Redirected back
6. **Credits updated** → Immediately available
7. **Process without watermark** → Clean downloads

### Subscription Management

1. **Dashboard** → View current plan
2. **Change plan** → Upgrade or downgrade
3. **Cancel** → Return to free tier (keeps current credits until month end)
4. **Reactivate** → Resume paid plan

---

## 📊 Revenue Projections

### Conservative (Month 6)

- 2,000 free users
- 50 Basic ($5) = **$250/mo**
- 10 Pro ($15) = **$150/mo**
- 2 Business ($50) = **$100/mo**
- **Total: $500/month** ($6K/year)

### Moderate (Year 1)

- 10,000 free users
- 500 Basic = **$2,500/mo**
- 100 Pro = **$1,500/mo**
- 20 Business = **$1,000/mo**
- **Total: $5,000/month** ($60K/year)

### Target (Year 2)

- 50,000 free users
- 2,000 Basic = **$10,000/mo**
- 500 Pro = **$7,500/mo**
- 100 Business = **$5,000/mo**
- **Total: $22,500/month** ($270K/year)

**Conversion rates:**
- Free → Paid: 2-5% (industry average)
- Basic → Pro: 20% (value upgrade)
- Churn: 5-10% monthly (managed with value adds)

---

## 🎯 Conversion Optimization

### Tactics

1. **Show value immediately** - Free tier works fully
2. **Watermark preview** - See quality before paying
3. **Usage limits** - Run out of credits → upgrade prompt
4. **Social proof** - "Join 10,000+ users"
5. **Urgency** - "Limited time: First month 50% off"
6. **Comparison** - "vs Photoshop: $5 vs $30/mo"
7. **Testimonials** - Real user reviews
8. **Use cases** - "Perfect for e-commerce sellers"

### Messaging

**Free tier CTA:**
> "Remove backgrounds from 3 images free every month. No credit card required."

**Upgrade prompt:**
> "You've used all 3 free credits this month. Upgrade to Basic for just $5/mo and get 50 credits + no watermark."

**Value proposition:**
> "Remove backgrounds in seconds with AI. Better than Photoshop, easier than manual editing, cheaper than hiring a designer."

---

## ✅ Implementation Checklist

### Backend
- [x] User authentication (JWT)
- [x] Password hashing (bcrypt)
- [x] Database models (User, UsageRecord)
- [x] Credit system
- [x] Watermark generation
- [x] Stripe integration
- [x] Webhook handling
- [ ] Email notifications (future)
- [ ] API rate limiting (future)

### Frontend
- [ ] Signup/login forms
- [ ] Auth token storage
- [ ] Pricing page
- [ ] Checkout integration
- [ ] User dashboard
- [ ] Usage stats display
- [ ] Upgrade prompts
- [ ] Watermark indicator

### Deployment
- [x] Docker configuration
- [x] Environment variables
- [x] Database persistence
- [ ] SSL certificate
- [ ] Domain setup
- [ ] Stripe production keys

---

**Full monetization system ready to deploy! 💰**

Next step: Build the frontend UI for auth + pricing!
