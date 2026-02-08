# QuickTools - Professional Automation Platform

**Status:** 🚀 Production Ready  
**Built:** 2026-02-07 to 2026-02-08  
**Version:** 1.0.0  

---

## 🎯 What is QuickTools?

QuickTools is a professional automation platform that makes everyday tasks instant. Remove backgrounds, process images, merge PDFs, generate QR codes, and more - all in one place.

**Mission:** Replace 10 different SaaS subscriptions with one simple platform.

---

## ✨ Features

### Current Tools
- **Background Removal** - AI-powered background removal for perfect product photos
- **Coming Soon:** Bulk Resize, PDF Tools, QR Codes, and more

### Platform Features
- ✅ Credit-based pricing (1 task = 1 credit)
- ✅ Unlimited FREE previews (watermarked)
- ✅ Clean downloads (costs credits)
- ✅ User authentication (JWT + bcrypt)
- ✅ Stripe subscription integration
- ✅ RESTful API access (Pro & Business tiers)
- ✅ Tier-based support system
- ✅ Beautiful, professional UI
- ✅ Docker deployment ready

---

## 💰 Pricing

| Tier | Price | Credits/Month | API Access | Support |
|------|-------|---------------|------------|---------|
| **Free** | $0 | 10 | ❌ | Community |
| **Basic** | $5 | 100 | ❌ | Email |
| **Pro** | $15 | 1,000 | ✅ | Priority |
| **Business** | $50 | 10,000 | ✅ | Priority+ |

**Note:** All credits work across ALL tools. Use them however you want!

---

## 🚀 Quick Start

### Local Development

```bash
# Clone repository
git clone https://github.com/amreinch/quicktools.git
cd quicktools

# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn app:app --host 0.0.0.0 --port 5000
```

Visit: http://localhost:5000

### Docker Deployment

```bash
# Build and run
docker compose up -d

# View logs
docker compose logs -f

# Stop
docker compose down
```

---

## 📊 Tech Stack

### Backend
- **Framework:** FastAPI 0.128+
- **Server:** Uvicorn (ASGI)
- **Database:** SQLAlchemy + SQLite/PostgreSQL
- **Auth:** JWT + bcrypt
- **Payments:** Stripe SDK
- **AI:** rembg (U2-Net model)
- **Images:** Pillow

### Frontend
- **HTML5/CSS3/JavaScript** (no frameworks)
- **Design:** Modern, professional, responsive
- **Font:** Inter (Google Fonts)
- **Icons:** Custom SVG

### Infrastructure
- **Container:** Docker + docker-compose
- **Database:** Volume-persisted SQLite/PostgreSQL
- **Environment:** .env configuration

---

## 🔑 Configuration

Copy `.env.example` to `.env` and configure:

```bash
# Required
JWT_SECRET_KEY=<generate with: openssl rand -hex 32>

# Database (SQLite by default, PostgreSQL for production)
DATABASE_URL=sqlite:///./quicktools.db

# Stripe (for payments)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PRICE_BASIC=price_...
STRIPE_PRICE_PRO=price_...
STRIPE_PRICE_BUSINESS=price_...

# Frontend URL
FRONTEND_URL=http://localhost:5000
```

See `STRIPE_SETUP.md` for complete Stripe configuration guide.

---

## 📚 Documentation

- **[STRIPE_SETUP.md](STRIPE_SETUP.md)** - Complete Stripe configuration
- **[MONETIZATION.md](MONETIZATION.md)** - Business model & pricing
- **[API_AND_SUPPORT.md](API_AND_SUPPORT.md)** - API access & support features
- **[LAUNCH_READY.md](LAUNCH_READY.md)** - Launch checklist
- **[DEPLOYMENT_DOCKER.md](DEPLOYMENT_DOCKER.md)** - Docker deployment

---

## 🎨 Brand

**Name:** QuickTools  
**Tagline:** Professional tools, instantly  
**Colors:** Blue (#3B82F6) + Purple (#8B5CF6) gradient  
**Font:** Inter  
**Vibe:** Modern, professional, efficient  

---

## 🛣️ Roadmap

### Phase 1 (Current)
- [x] Background removal
- [x] User authentication
- [x] Stripe payments
- [x] API access
- [x] Support system
- [x] Professional UI

### Phase 2 (Week 1)
- [ ] Bulk image resize
- [ ] Format conversion (JPG/PNG/WebP)
- [ ] Image compression

### Phase 3 (Week 2)
- [ ] PDF merge/split
- [ ] QR code generator
- [ ] Background replacement

### Phase 4 (Month 1)
- [ ] Batch processing
- [ ] Watermark adding
- [ ] Text tools
- [ ] Screenshot tools

---

## 🔒 Security

- ✅ JWT token authentication (7-day expiry)
- ✅ Bcrypt password hashing (Python 3.14 compatible)
- ✅ API key SHA256 hashing
- ✅ CORS middleware
- ✅ Input validation (Pydantic)
- ✅ Rate limiting ready
- ✅ `.env` gitignored

---

## 📈 Market Opportunity

**Target Market:**
- E-commerce sellers (Amazon, Shopify, eBay)
- Social media managers
- Graphic designers
- Small businesses
- Content creators
- Developers (API access)

**Revenue Potential:**
- Conservative (Month 6): $775/mo
- Moderate (Year 1): $7,500/mo
- Target (Year 2): $33,750/mo

**Conversion Strategy:**
- Freemium model (10 free tasks)
- Unlimited preview testing
- Pay-per-use (1 credit = 1 task)
- Multi-tool value proposition

---

## 🤝 Contributing

This is a private project. For questions or suggestions, contact via the support form.

---

## 📄 License

All rights reserved © 2026 QuickTools

---

## 🚀 Deployment

### Production Checklist
- [ ] Configure production Stripe keys
- [ ] Set secure JWT_SECRET_KEY
- [ ] Switch to PostgreSQL database
- [ ] Set up SSL certificate
- [ ] Configure domain
- [ ] Enable Stripe webhooks
- [ ] Set up monitoring
- [ ] Configure backups

### Recommended Hosting
- **Render.com** (easiest, $7/mo)
- **Fly.io** (fast, free tier)
- **DigitalOcean** (full control, $4-12/mo)

---

**Built with ❤️ by pioneering developers**

**Repository:** https://github.com/amreinch/quicktools  
**Live Demo:** Coming Soon  
**Contact:** support@quicktools.com (coming soon)
