# QuickTools - Monetization System

## 💰 Credit Pack Model (One-Time Purchases)

**Updated:** 2026-02-09 - Aligned to credit pack implementation

---

## 🎯 Business Model

### Why Credit Packs (Not Subscriptions)

**Model:** One-time purchases, credits never expire

**Benefits:**
1. **Better User Value** - Credits don't expire, use at your own pace
2. **Lower Friction** - No recurring billing anxiety
3. **Simpler Implementation** - No proration, no subscription management
4. **Higher Conversion** - Clearer value proposition
5. **API as Permanent Unlock** - Buy once, keep forever

**Why This Wins:**
- Users hate subscriptions for sporadic use tools
- "Pay once" messaging resonates stronger
- Credits accumulate (users can buy multiple packs)
- API access becomes a one-time unlock (huge value)

---

## 📊 Credit Pack Tiers

### Current Pricing (2026-02-09)

| Pack | Price | Credits | Per Credit | API | Support |
|------|-------|---------|------------|-----|---------|
| **Free Starter** | $0 | 10 | - | ❌ | Community |
| **Starter Pack** | $5 | 100 | $0.05 | ❌ | Email (48h) |
| **Standard Pack** | $15 | 500 | $0.03 | ❌ | Email (48h) |
| **Pro Pack** | $30 | 1,200 | $0.025 | ✅ | Priority (24h) |
| **Business Pack** | $100 | 5,000 | $0.02 | ✅ | Dedicated (12h) |

### Key Features

**All Packs Include:**
- All tools (background removal, resize, PDF, QR, etc.)
- Full resolution output
- Credits never expire
- Stack multiple purchases (credits accumulate)

**Pro & Business Only:**
- 🔑 **Permanent API access** (unlock once, keep forever)
- API documentation
- Higher priority support

---

## 🎨 How It Works

### User Journey

1. **Sign Up (Free)** → Get 10 free credits
2. **Use Tools** → Each task = 1 credit
3. **Run Out?** → Buy a credit pack
4. **Credits Add** → Balance updates immediately
5. **Never Expire** → Use at your own pace

### Credit Deduction

**1 task = 1 credit** across ALL tools:
- Remove background: 1 credit
- Resize image: 1 credit
- PDF merge: 1 credit
- Generate QR code: 1 credit

**Simple, transparent pricing.**

### API Access Unlock

**How it works:**
1. User buys **Pro Pack** ($30) or **Business Pack** ($100)
2. `api_access_unlocked = true` set in database
3. User can now create API keys (unlimited)
4. API access remains **even after credits run out**
5. New credits can be purchased without buying Pro again

**Result:** One-time $30 payment for lifetime API access + 1,200 credits

---

## 💳 Stripe Integration

### Setup Required

1. **Stripe Account** (https://stripe.com)
2. **Webhook Endpoint** configured: `/api/webhook/stripe`
3. **Events:** `checkout.session.completed`

See **STRIPE_SETUP.md** for complete configuration guide.

### Checkout Flow

**User clicks "Buy Now" on Starter Pack:**

```javascript
// Frontend (static/app.js)
async function checkout(pack) {
    const response = await fetch('/api/create-checkout-session', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ tier: pack })  // 'starter', 'standard', 'pro', 'business'
    });
    
    const data = await response.json();
    window.location.href = data.url; // Redirect to Stripe
}
```

**Backend creates Stripe session:**

```python
@app.post("/api/create-checkout-session")
async def create_checkout_session(request: CheckoutSessionRequest, current_user: User):
    pack = request.tier  # Pack name
    pack_config = CREDIT_PACKS[pack]
    
    # Create checkout session for ONE-TIME PAYMENT
    session = stripe.checkout.Session.create(
        customer=current_user.stripe_customer_id,
        line_items=[{
            "price_data": {
                "currency": "usd",
                "product_data": {
                    "name": pack_config["name"],
                    "description": f"{pack_config['credits']} credits - Never expire!",
                },
                "unit_amount": pack_config["price"],  # Cents
            },
            "quantity": 1,
        }],
        mode="payment",  # ONE-TIME PAYMENT (not subscription!)
        metadata={
            "pack": pack,
            "credits": pack_config["credits"],
            "unlocks_api": str(pack_config["unlocks_api"]),
            "user_id": current_user.id
        },
        success_url=f"{FRONTEND_URL}/success?credits={pack_config['credits']}",
        cancel_url=f"{FRONTEND_URL}/#pricing",
    )
    
    return {"session_id": session.id, "url": session.url}
```

### Webhook Handling

**Event: `checkout.session.completed`**

```python
@app.post("/api/webhook/stripe")
async def stripe_webhook(request: dict, db: Session = Depends(get_db)):
    event_type = request.get("type")
    
    if event_type == "checkout.session.completed":
        session = request.get("data", {}).get("object", {})
        metadata = session.get("metadata", {})
        
        user_id = metadata.get("user_id")
        credits = int(metadata.get("credits", 0))
        unlocks_api = metadata.get("unlocks_api") == "True"
        
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            # Add credits to balance
            user.add_credits(credits, unlocks_api=unlocks_api)
            db.commit()
    
    return {"status": "ok"}
```

**What happens:**
1. Payment successful → webhook fires
2. Credits added to `user.credits_balance`
3. If Pro/Business → `user.api_access_unlocked = True`
4. User can immediately use credits

---

## 📈 Database Schema

### User Model (Credit Pack Fields)

```python
class User(Base):
    # Credit Pack System
    credits_balance = Column(Integer, default=10)  # Current balance
    credits_purchased_total = Column(Integer, default=0)  # Lifetime purchases
    credits_lifetime_used = Column(Integer, default=0)  # Lifetime usage
    api_access_unlocked = Column(Boolean, default=False)  # Permanent unlock
    
    # Stripe
    stripe_customer_id = Column(String, nullable=True)
    last_purchase_date = Column(DateTime, nullable=True)
    last_purchase_amount = Column(Integer, nullable=True)  # Credits
    
    @property
    def credits_remaining(self):
        return max(0, self.credits_balance)
    
    @property
    def can_process(self):
        return self.credits_balance > 0
    
    def use_credit(self):
        if self.credits_balance > 0:
            self.credits_balance -= 1
            self.credits_lifetime_used += 1
        else:
            raise ValueError("Insufficient credits")
    
    def add_credits(self, amount: int, unlocks_api: bool = False):
        self.credits_balance += amount
        self.credits_purchased_total += amount
        self.last_purchase_date = datetime.utcnow()
        self.last_purchase_amount = amount
        
        if unlocks_api:
            self.api_access_unlocked = True
```

### Support Tier (Based on Lifetime Purchases)

```python
@property
def support_tier(self):
    if self.credits_purchased_total >= 5000:  # Business
        return "Dedicated (12h response)"
    elif self.credits_purchased_total >= 1200:  # Pro
        return "Priority (24h response)"
    elif self.credits_purchased_total >= 500:  # Standard
        return "Email (48h response)"
    else:
        return "Community"
```

**Smart:** Support tier based on total lifetime value, not current balance!

---

## 🎨 Frontend Integration

### Pricing Display (static/index.html)

```html
<div class="pricing-card">
    <div class="pricing-header">
        <h3>Pro Pack</h3>
        <div class="pricing-amount">
            <span class="price">$30</span>
            <span class="period">one-time</span>  <!-- NOT /month! -->
        </div>
    </div>
    <ul class="pricing-features">
        <li>1,200 tasks (never expire)</li>
        <li>50% better value</li>
        <li>🔑 Unlock API access</li>
        <li>Priority support (24h)</li>
    </ul>
    <button class="btn btn-primary w-full" onclick="checkout('pro')">
        Buy Now
    </button>
</div>
```

### Credits Display (Navbar)

```javascript
// Show credits remaining in user menu
if (userData.credits_balance !== undefined) {
    creditsEl.textContent = `${userData.credits_balance} credits`;
    creditsEl.classList.add('user-credits-badge');
}
```

### API Access Badge

```javascript
// Show API badge if unlocked
if (userData.api_access_unlocked) {
    const apiBadge = document.createElement('span');
    apiBadge.className = 'api-badge';
    apiBadge.textContent = '🔑 API';
    userMenu.appendChild(apiBadge);
}
```

---

## 📊 Revenue Projections

### Conservative (Month 6)

- 3,000 free users
- 100 Starter ($5) = **$500/mo**
- 50 Standard ($15) = **$750/mo**
- 20 Pro ($30) = **$600/mo**
- 5 Business ($100) = **$500/mo**
- **Total: $2,350/month**

**Conversion:** 5.8% free → paid (industry average: 2-5%)

### Moderate (Year 1)

- 15,000 free users
- 750 Starter = **$3,750/mo**
- 300 Standard = **$4,500/mo**
- 150 Pro = **$4,500/mo**
- 30 Business = **$3,000/mo**
- **Total: $15,750/month** ($189K/year)

**Conversion:** 8% free → paid (higher due to no subscription anxiety)

### Target (Year 2)

- 75,000 free users
- 3,000 Starter = **$15,000/mo**
- 1,500 Standard = **$22,500/mo**
- 750 Pro = **$22,500/mo**
- 150 Business = **$15,000/mo**
- **Total: $75,000/month** ($900K/year)

**Conversion:** 7% free → paid (sustainable)

---

## 🎯 Conversion Optimization

### Messaging

**Homepage Hero:**
> "Professional automation tools. No subscriptions. Credits never expire."

**Free tier CTA:**
> "Try QuickTools free. 10 credits to test all tools. No credit card required."

**Upgrade prompt:**
> "Out of credits? Buy a pack and keep them forever. No monthly fees."

**Value proposition:**
> "Better than Photoshop plugins. Easier than manual editing. Cheaper than subscriptions."

### Tactics

1. **No Subscription Anxiety** - "Credits never expire" messaging everywhere
2. **Stacking Value** - Users can buy multiple packs (credits accumulate)
3. **API as Upgrade Path** - "Unlock API access forever with Pro pack"
4. **Clear Pricing** - "$30 one-time = 1,200 tasks + API access"
5. **Social Proof** - "Join 15,000+ users automating their workflow"
6. **Comparison** - "vs competitors charging $10-20/month"
7. **Use Cases** - "Perfect for: e-commerce, designers, marketers, developers"

---

## ✅ Implementation Status

### Backend ✅ COMPLETE
- [x] User authentication (JWT + bcrypt)
- [x] Database models (User, UsageRecord, APIKey)
- [x] Credit system (balance, deduction, accumulation)
- [x] Stripe integration (one-time payments)
- [x] Webhook handling (checkout.session.completed)
- [x] API access gating (check api_access_unlocked)
- [x] Support tier calculation (lifetime purchases)

### Frontend ✅ COMPLETE
- [x] Signup/login forms
- [x] Auth token storage
- [x] Pricing page (credit packs)
- [x] Checkout integration (Stripe redirect)
- [x] User dashboard (credits display)
- [x] Usage stats
- [x] API key management page
- [x] Credit balance in navbar

### Deployment 🚀 READY
- [x] Docker configuration
- [x] Environment variables
- [x] Database persistence (SQLite/PostgreSQL)
- [ ] SSL certificate (production)
- [ ] Domain setup (production)
- [ ] Stripe production keys (when ready)

---

## 🔄 Migration Path (Old Subscription Users)

**If you had subscription fields in database:**

1. **Existing users:** Keep credits from old monthly allocation
2. **New system:** All users on credit pack model
3. **Database cleanup:** Drop old subscription columns in future migration
4. **Backward compatibility:** Old fields ignored by application

**Current:** Both old + new fields exist, application uses only credit pack fields.

---

## 📝 Key Takeaways

### Why Credit Packs Win

**User Psychology:**
- "One-time" sounds better than "monthly"
- "Never expire" removes urgency anxiety
- "Unlock API forever" = huge perceived value

**Business Benefits:**
- Simpler implementation (no subscription logic)
- Higher average transaction value ($30 vs $15/mo)
- Lower churn (no monthly cancellations)
- Clearer unit economics

**Implementation:**
- No proration handling needed
- No subscription upgrade/downgrade logic
- Webhook only handles payment success
- Credits accumulate (users can buy multiple packs)

---

**Complete monetization system implemented! 💰**

**Next:** Deploy to production, setup Stripe keys, launch!
