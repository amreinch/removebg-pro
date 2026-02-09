# Pricing Text & Environment Variables Cleanup

**Date:** 2026-02-09  
**Issue:** Misleading pricing text + obsolete Stripe variables  
**Status:** ✅ Fixed

---

## 🎯 What Was Misleading

### Old Pricing Text (Removed)
❌ "forever"  
❌ "one-time"  
❌ "never expire"  
❌ "Credits never expire"  

**Why misleading:**  
Credits **can be used up** by performing tasks. While there's no time expiration, saying "never expire" implies they last forever regardless of usage, which is confusing.

---

## ✅ What Was Fixed

### 1. Pricing Cards (static/index.html)

**Before:**
```html
<span class="period">one-time</span>
<li>100 tasks (never expire)</li>
```

**After:**
```html
<!-- No period text -->
<li>100 credits</li>
```

**Changed:**
- Removed "forever", "one-time", "never expire" text
- Changed "tasks (never expire)" → "credits"
- Simplified messaging

### 2. Pricing Subtitle

**Before:**
> "Buy credit packs once. No subscriptions. Credits never expire."

**After:**
> "Buy credit packs. No subscriptions. 1 credit = 1 task."

**Why better:**
- Clear and simple
- No misleading claims
- Explains the core mechanic

---

## 🗑️ Obsolete Stripe Variables Removed

### Old Subscription Model Used:
```bash
STRIPE_PRICE_BASIC=price_basic_monthly_id
STRIPE_PRICE_PRO=price_pro_monthly_id
STRIPE_PRICE_BUSINESS=price_business_monthly_id
```

**Why obsolete:**  
We now use **dynamic price creation** in the checkout API. Prices are created on-the-fly based on the CREDIT_PACKS configuration in `app.py`, not predefined in Stripe.

### Files Updated:

**1. `.env.example`**
```diff
- # Stripe Price IDs (create these in Stripe Dashboard)
- STRIPE_PRICE_BASIC=price_basic_monthly_id
- STRIPE_PRICE_PRO=price_pro_monthly_id
- STRIPE_PRICE_BUSINESS=price_business_monthly_id
```

**2. `.env`**
```diff
- # Stripe Price IDs (create products in Stripe Dashboard first)
- # Guide: https://dashboard.stripe.com/products
- STRIPE_PRICE_BASIC=price_1SyhruPpSjTQz50hSnSCCbdA
- STRIPE_PRICE_PRO=price_1SysTePpSjTQz50hid9Dc5SA
- STRIPE_PRICE_BUSINESS=price_business_monthly_id
```

**3. `docker-compose.yml`**
```diff
  environment:
    - STRIPE_SECRET_KEY=${STRIPE_SECRET_KEY}
-   - STRIPE_PRICE_BASIC=${STRIPE_PRICE_BASIC}
-   - STRIPE_PRICE_PRO=${STRIPE_PRICE_PRO}
-   - STRIPE_PRICE_BUSINESS=${STRIPE_PRICE_BUSINESS}
    - FRONTEND_URL=${FRONTEND_URL}
```

---

## 💡 How Pricing Works Now

### Dynamic Price Creation (Current)

When user clicks "Buy Now", the API:

1. Gets pack config from `CREDIT_PACKS` in `app.py`:
   ```python
   "starter": {
       "name": "Starter Pack",
       "price": 500,  # $5 in cents
       "credits": 100,
       ...
   }
   ```

2. Creates Stripe checkout with dynamic price:
   ```python
   session = stripe.checkout.Session.create(
       line_items=[{
           "price_data": {
               "currency": "usd",
               "product_data": {
                   "name": pack_config["name"],
                   "description": f"{pack_config['credits']} credits",
               },
               "unit_amount": pack_config["price"],
           },
           "quantity": 1,
       }],
       mode="payment",  # One-time payment
       ...
   )
   ```

3. No need for predefined Stripe price IDs!

**Benefits:**
- ✅ Change prices in code without Stripe dashboard
- ✅ One source of truth (CREDIT_PACKS)
- ✅ Simpler deployment
- ✅ Easier to test

---

## 📋 Files Modified

1. **static/index.html** - Removed misleading pricing text
2. **.env.example** - Removed obsolete Stripe price IDs
3. **.env** - Removed obsolete Stripe price IDs
4. **docker-compose.yml** - Removed Stripe price ID env vars

---

## ✅ Result

### Cleaner Pricing Messaging
- No confusing "never expire" claims
- Simple: "$5 = 100 credits"
- Clear value proposition

### Simpler Configuration
- Only need 2 Stripe variables:
  - `STRIPE_SECRET_KEY`
  - `STRIPE_PUBLISHABLE_KEY` (frontend)
- No price IDs needed

### Easier Maintenance
- Update prices in `app.py` only
- No Stripe dashboard product management
- Single source of truth

---

## 🚀 To Apply Changes

```bash
cd /home/influ/projects/quicktools
sudo docker compose build
sudo docker compose restart
```

Then hard refresh browser: `Ctrl+Shift+R`

---

**Status:** ✅ **Clean and honest pricing!**
