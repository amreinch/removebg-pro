# Stripe Dynamic Pricing - No Setup Required!

**Question:** Do I need to create different products/prices in Stripe for each pack?  
**Answer:** ❌ **NO! It's all automatic.**

---

## 🎯 How It Works

### Dynamic Price Creation

Your app uses **`price_data`** in Stripe Checkout, which creates prices **on-the-fly**.

**When user clicks "Buy Starter Pack ($5)":**

1. Frontend calls: `POST /api/purchase-credits` with `tier: "starter"`
2. Backend looks up pack config:
   ```python
   CREDIT_PACKS["starter"] = {
       "name": "Starter Pack",
       "price": 500,  # $5 in cents
       "credits": 100
   }
   ```
3. Backend creates Stripe checkout **dynamically**:
   ```python
   stripe.checkout.Session.create(
       line_items=[{
           "price_data": {  # ← Creates price automatically!
               "currency": "usd",
               "product_data": {
                   "name": "Starter Pack",
                   "description": "100 credits",
               },
               "unit_amount": 500,  # $5
           },
           "quantity": 1,
       }],
       mode="payment",  # One-time payment
   )
   ```
4. Stripe creates the product and price automatically
5. User gets redirected to Stripe checkout page
6. Payment processed!

**No manual Stripe configuration needed!** ✨

---

## 📊 All Packs Handled Automatically

| Pack | Price | What Happens |
|------|-------|--------------|
| **Starter** | $5 | Stripe creates "$5 product" automatically |
| **Standard** | $15 | Stripe creates "$15 product" automatically |
| **Pro** | $30 | Stripe creates "$30 product" automatically |
| **Business** | $100 | Stripe creates "$100 product" automatically |

**Each purchase creates its own product/price in Stripe dynamically.**

---

## 🔄 Two Ways to Use Stripe

### Method 1: Pre-created Products (Old Way - Not What You're Using)
```python
# Need to create products in Stripe Dashboard first
line_items=[{
    "price": "price_1234567890",  # Must exist in Stripe
    "quantity": 1
}]
```

❌ **Requires:**
- Creating products in Stripe Dashboard
- Managing price IDs
- Environment variables for each price

### Method 2: Dynamic Price Data (What You're Using) ✅
```python
# Creates products on-the-fly
line_items=[{
    "price_data": {  # ← Magic happens here!
        "currency": "usd",
        "product_data": {"name": "Starter Pack"},
        "unit_amount": 500
    },
    "quantity": 1
}]
```

✅ **Benefits:**
- No Stripe Dashboard setup
- Change prices in code instantly
- Works immediately
- Easier deployment

---

## 🎯 What You See in Stripe Dashboard

After users make purchases, you'll see in Stripe:

**Products Section:**
```
- Starter Pack ($5.00)
  Created automatically on first purchase

- Standard Pack ($15.00)
  Created automatically on first purchase

- Pro Pack ($30.00)
  Created automatically on first purchase

- Business Pack ($100.00)
  Created automatically on first purchase
```

**These appear automatically when users buy!**

---

## 💡 Want to Change Prices?

**Just edit `app.py`:**

```python
CREDIT_PACKS = {
    "starter": {
        "name": "Starter Pack",
        "price": 500,  # Change to 499 for $4.99
        "credits": 100,
    }
}
```

Restart app → New price immediately!

**No Stripe Dashboard work needed!** ✨

---

## ✅ What You Need to Do

### For Testing (Test Mode)
1. ✅ Get Stripe test keys (you already have these)
2. ✅ Add to `.env`:
   ```bash
   STRIPE_SECRET_KEY=sk_test_...
   ```
3. ✅ **That's it!** Products create automatically

### For Production (Live Mode)
1. Switch to live keys:
   ```bash
   STRIPE_SECRET_KEY=sk_live_...
   ```
2. **Done!** No product setup needed

---

## 🧪 Test It Now

### 1. Visit Your App
```
http://192.168.0.89:5000/static/index.html
```

### 2. Click "Buy Now" on Any Pack
- Starter, Standard, Pro, or Business
- Any of them will work!

### 3. Check Stripe Dashboard
https://dashboard.stripe.com/test/products

**You'll see the product created automatically after checkout!**

---

## 📋 Webhook Configuration (Only This Is Needed)

**The ONE thing you need to configure in Stripe:**

1. Go to: https://dashboard.stripe.com/test/webhooks
2. Click: "Add endpoint"
3. URL: `http://192.168.0.89:5000/api/webhook/stripe`
4. Events: Select `checkout.session.completed`
5. Save

**That's the only manual Stripe setup!**

This webhook tells your app when payment succeeds so it can add credits.

---

## 🎉 Summary

### ❌ You DON'T Need To:
- Create products in Stripe Dashboard
- Create prices in Stripe Dashboard
- Manage price IDs
- Use environment variables for prices

### ✅ You ONLY Need To:
- Have Stripe API keys in `.env`
- Configure webhook endpoint (one time)
- Everything else is automatic!

### 💡 To Change Prices:
- Edit `CREDIT_PACKS` in `app.py`
- Restart app
- Done!

---

## 🔍 Verify It's Working

### Check Current Implementation

```bash
cd /home/influ/projects/quicktools
grep -A 10 "price_data" app.py
```

You should see:
```python
"price_data": {
    "currency": "usd",
    "product_data": {
        "name": pack_config["name"],
        ...
    },
    "unit_amount": pack_config["price"],
}
```

**✅ This means dynamic pricing is active!**

---

**Your setup is already perfect! No Stripe Dashboard product creation needed!** 🎊

Just test a purchase and watch products appear automatically in Stripe.
