# Credit Pack System Migration - February 9, 2026

## Overview
Complete overhaul from monthly subscription model to one-time credit pack purchases.

## Goals
- ✅ Simpler billing (no subscriptions)
- ✅ Credits never expire
- ✅ Buy anytime, use at your pace
- ✅ API access as premium feature
- ✅ Better user experience
- ✅ Easier to maintain

---

## New Credit Pack Tiers

### **Starter Pack**
- **Price:** $5
- **Credits:** 100
- **Per-credit cost:** $0.05
- **Features:** Web UI only

### **Standard Pack** ⭐
- **Price:** $15
- **Credits:** 500
- **Per-credit cost:** $0.03 (40% better!)
- **Features:** Web UI only

### **Pro Pack** 💎 (UNLOCKS API)
- **Price:** $30
- **Credits:** 1,200
- **Per-credit cost:** $0.025 (50% better!)
- **Features:** 
  - Web UI
  - **API Access (lifetime unlock)**
  - API documentation
  - Priority support (24h)

### **Business Pack**
- **Price:** $100
- **Credits:** 5,000
- **Per-credit cost:** $0.02 (60% better!)
- **Features:**
  - Everything in Pro
  - Higher API rate limits (500 req/min vs 100)
  - Dedicated support (12h)

---

## Database Schema Changes

### **Old Model (Subscription):**
```sql
-- Users table had:
subscription_tier VARCHAR        -- free, basic, pro, business
subscription_status VARCHAR      -- active, cancelled
stripe_subscription_id VARCHAR
monthly_credits INTEGER
credits_used_this_month INTEGER
credits_reset_date DATETIME
```

### **New Model (Credit Packs):**
```sql
-- Users table now has:
credits_balance INTEGER DEFAULT 10           -- Current balance (10 free starter)
credits_purchased_total INTEGER DEFAULT 0    -- Lifetime purchases
credits_lifetime_used INTEGER DEFAULT 0      -- Lifetime usage
api_access_unlocked BOOLEAN DEFAULT FALSE    -- Unlocked when bought Pro+ pack
last_purchase_date DATETIME
last_purchase_amount INTEGER                 -- For analytics
```

### **Migration SQL:**
```sql
-- Add new columns
ALTER TABLE users ADD COLUMN credits_balance INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN credits_purchased_total INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN credits_lifetime_used INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN api_access_unlocked BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN last_purchase_date DATETIME;
ALTER TABLE users ADD COLUMN last_purchase_amount INTEGER;

-- Migrate existing users (preserve current credits)
UPDATE users SET 
  credits_balance = CASE
    WHEN subscription_tier = 'free' THEN 10
    WHEN subscription_tier = 'basic' THEN (monthly_credits - credits_used_this_month)
    WHEN subscription_tier = 'pro' THEN (monthly_credits - credits_used_this_month)
    WHEN subscription_tier = 'business' THEN (monthly_credits - credits_used_this_month)
    ELSE 10
  END,
  api_access_unlocked = CASE
    WHEN subscription_tier IN ('pro', 'business') THEN TRUE
    ELSE FALSE
  END,
  credits_lifetime_used = COALESCE(credits_used_this_month, 0);

-- Drop old subscription columns (after migration confirmed working)
-- ALTER TABLE users DROP COLUMN subscription_tier;
-- ALTER TABLE users DROP COLUMN subscription_status;
-- ALTER TABLE users DROP COLUMN stripe_subscription_id;
-- ALTER TABLE users DROP COLUMN monthly_credits;
-- ALTER TABLE users DROP COLUMN credits_used_this_month;
-- ALTER TABLE users DROP COLUMN credits_reset_date;
```

---

## Credit Pack Configuration

```python
# Credit packs with pricing
CREDIT_PACKS = {
    "starter": {
        "name": "Starter Pack",
        "price": 500,  # $5 in cents
        "credits": 100,
        "per_credit": 0.05,
        "unlocks_api": False,
        "features": ["Web UI access", "100 tasks", "Community support"]
    },
    "standard": {
        "name": "Standard Pack",
        "price": 1500,  # $15 in cents
        "credits": 500,
        "per_credit": 0.03,
        "unlocks_api": False,
        "badge": "⭐ Popular",
        "features": ["Web UI access", "500 tasks", "Email support", "40% better value"]
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
            "🔑 API Access (lifetime)",
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
        "features": [
            "Web UI access",
            "5,000 tasks",
            "🔑 API Access (lifetime)",
            "Higher API rate limits",
            "Dedicated support (12h)",
            "60% better value"
        ]
    }
}
```

---

## API Access Model

### **How API Access Works:**

1. **Unlock Requirement:**
   - Purchase Pro Pack ($30) or Business Pack ($100)
   - `api_access_unlocked` → TRUE (lifetime)
   - Can now generate API keys

2. **Credit Usage:**
   - API calls use same credits as web UI
   - 1 API call = 1 credit (same rate)
   - No double-charging

3. **Rate Limits:**
   ```python
   RATE_LIMITS = {
       "pro": 100,      # 100 requests/minute
       "business": 500   # 500 requests/minute
   }
   
   # Determine tier by total purchased:
   if credits_purchased_total >= 5000:  # Business pack
       rate_limit = 500
   elif api_access_unlocked:  # Pro pack
       rate_limit = 100
   else:
       rate_limit = 0  # No API access
   ```

4. **Support Tiers:**
   ```python
   if credits_purchased_total >= 5000:  # Business
       support = "Dedicated (12h response)"
   elif credits_purchased_total >= 1200:  # Pro
       support = "Priority (24h response)"
   elif credits_purchased_total >= 500:  # Standard
       support = "Email (48h response)"
   else:
       support = "Community"
   ```

---

## User Flow Examples

### **Example 1: New User**
```
1. Sign up → Gets 10 free credits
2. Try the service (10 tasks)
3. Like it → Buy Starter ($5 = 100 credits)
4. Balance: 100 credits, no API
5. Run out → Buy Standard ($15 = 500 credits)
6. Balance: 500 credits, no API
7. Need API → Buy Pro ($30 = 1,200 credits)
8. Balance: 1,200 credits, API UNLOCKED ✅
9. Future purchases: Any pack adds credits, keeps API
```

### **Example 2: Power User**
```
1. Sign up → 10 free credits
2. Immediately buy Business ($100 = 5,000 credits)
3. Balance: 5,000 credits, API unlocked, 500 req/min
4. Use 3,000 credits over time
5. Balance: 2,000 credits
6. Buy another Business pack ($100 = 5,000 more)
7. Balance: 7,000 credits, still API enabled
8. Total purchased: $200 (10,000 credits lifetime)
```

### **Example 3: API-First User**
```
1. Sign up → 10 free credits
2. Read docs, wants API immediately
3. Buy Pro pack ($30 = 1,200 credits + API)
4. Generate API key
5. Integrate with their system
6. Use 1,000 credits via API
7. Balance: 200 credits
8. Buy Starter pack ($5 = 100 credits)
   - API stays unlocked (already had Pro)
   - Balance: 300 credits
```

---

## Stripe Integration (Simplified!)

### **Old (Subscription):**
```python
# Complex subscription creation
# Webhooks for: created, updated, deleted, payment_failed
# Proration calculations
# Upgrade/downgrade logic
# ~200 lines of code
```

### **New (One-Time Payments):**
```python
# Simple payment
@app.post("/api/purchase-credits")
async def purchase_credits(pack: str):
    pack_config = CREDIT_PACKS[pack]
    
    session = stripe.checkout.Session.create(
        customer=customer_id,
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "usd",
                "product_data": {
                    "name": pack_config["name"],
                    "description": f"{pack_config['credits']} credits"
                },
                "unit_amount": pack_config["price"],
            },
            "quantity": 1,
        }],
        mode="payment",  # ONE-TIME!
        metadata={
            "pack": pack,
            "credits": pack_config["credits"],
            "unlocks_api": pack_config["unlocks_api"]
        },
        success_url=f"{base_url}/success",
        cancel_url=f"{base_url}/pricing",
    )
    
    return {"url": session.url}

# Webhook (simple!)
@app.post("/webhook/stripe")
async def stripe_webhook(request: dict):
    if request["type"] == "payment_intent.succeeded":
        metadata = request["data"]["object"]["metadata"]
        
        user.credits_balance += int(metadata["credits"])
        user.credits_purchased_total += int(metadata["credits"])
        user.last_purchase_date = datetime.utcnow()
        user.last_purchase_amount = int(metadata["credits"])
        
        if metadata["unlocks_api"] == "true":
            user.api_access_unlocked = True
        
        db.commit()

# That's it! ~50 lines vs 200
```

---

## UI Changes

### **Pricing Page (index.html):**

**Before:**
```html
<div class="pricing-card">
    <h3>Pro</h3>
    <div class="price">$15<span>/month</span></div>
    <ul>
        <li>1,000 tasks per month</li>
        <li>All tools included</li>
        <li>API access</li>
    </ul>
    <button onclick="checkout('pro')">Subscribe</button>
</div>
```

**After:**
```html
<div class="pricing-card featured">
    <div class="badge">💎 Best Value + API</div>
    <h3>Pro Pack</h3>
    <div class="price">$30</div>
    <div class="per-credit">$0.025 per task</div>
    <ul>
        <li>1,200 credits</li>
        <li>🔑 Unlocks API access (lifetime)</li>
        <li>Priority support (24h)</li>
        <li>Credits never expire</li>
    </ul>
    <button onclick="buyPack('pro')">Buy Credits</button>
</div>
<p class="pack-note">✨ Buy more anytime • Stack unlimited credits</p>
```

### **Navbar Credits Display:**

**Before:**
```html
<span class="user-credits">45 credits (resets in 12 days)</span>
```

**After:**
```html
<span class="user-credits">
    <span class="credit-count">1,245</span> credits
</span>
```

Simple! No reset date needed.

### **API Keys Page:**

**Before:**
```
Tier check:
  if tier === "pro" || tier === "business"
```

**After:**
```javascript
if (currentUser.api_access_unlocked) {
    // Show API key management
} else {
    // Show:
    "🔑 Unlock API access by purchasing a Pro Pack or higher ($30+)"
    [Buy Pro Pack button]
}
```

---

## Benefits Summary

### **For Users:**
- ✅ Credits never expire (no monthly pressure)
- ✅ Buy when needed (flexible)
- ✅ Clear pricing (one-time decision)
- ✅ Stock up credits (volume discounts)
- ✅ API unlock forever (buy once, use always)

### **For Development:**
- ✅ 75% less code (no subscription management)
- ✅ No proration complexity
- ✅ Simpler Stripe integration
- ✅ Fewer edge cases
- ✅ Easier to debug

### **For Business:**
- ✅ Higher conversion (one-time easier than recurring)
- ✅ Upsell opportunities (buy more for better value)
- ✅ API as premium tier (clear monetization)
- ✅ Better analytics (lifetime value tracking)

---

## Implementation Checklist

- [ ] Database migration (add new columns)
- [ ] Update models.py (User model)
- [ ] Update app.py (remove subscription, add credit packs)
- [ ] Create CREDIT_PACKS config
- [ ] Update Stripe integration (one-time payments)
- [ ] Update pricing page UI
- [ ] Update navbar display
- [ ] Update API access checks
- [ ] Remove subscription webhooks
- [ ] Update documentation
- [ ] Test credit purchase flow
- [ ] Test API unlock
- [ ] Test credit usage
- [ ] Deploy migration

---

## Pricing Psychology

**Why this works:**

```
❌ "$15/month"
   → Sounds like commitment
   → Recurring anxiety
   → "Am I using enough to justify this?"

✅ "$15 = 500 credits"
   → Clear value
   → Use at my pace
   → "I own these credits"
   → No pressure
```

**Volume discount incentive:**
```
Starter:  $0.05/credit
Standard: $0.03/credit (40% better!) ← Users upgrade
Pro:      $0.025/credit (50% better + API!) ← Power users
Business: $0.02/credit (60% better!) ← Heavy users
```

---

Ready to implement! Shall I proceed with the code changes?
