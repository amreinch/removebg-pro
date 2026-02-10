# Support Ticket System - QuickTools

Complete support system with database storage and admin dashboard.

## 🎫 How It Works

### For Users:

1. **Free Tier (0 credits purchased):**
   - ❌ Cannot access support page at all
   - Redirected to pricing page with message
   - Must purchase credits to get support

2. **Paying Customers (any credit pack purchased):**
   - ✅ Can access support page
   - Fill out form: Subject + Message
   - Submit creates ticket in database
   - Receives confirmation message

### For You (Admin):

**Access Dashboard:**
```
http://localhost:5000/static/admin-support.html
```

Or when deployed:
```
https://quicktools.io/static/admin-support.html
```

**Dashboard Features:**
- 📊 Real-time stats (open tickets, total tickets)
- 🔍 Filter tickets (Open, Closed, All)
- 📧 See user email, tier, credits purchased
- 💬 Read full ticket message
- ✅ Close tickets with one click
- 🔄 Auto-refreshes every 30 seconds

---

## 📋 Database Schema

### SupportTicket Table:
```
id                     - UUID (primary key)
user_id               - Foreign key to users
subject               - Ticket subject line
message               - Full ticket text
status                - open/in_progress/closed
priority              - low/normal/high
user_email            - Email snapshot
user_credits_purchased - Credits purchased snapshot
user_support_tier     - Support tier snapshot
created_at            - When submitted
updated_at            - Last modified
closed_at             - When closed (nullable)
```

---

## 🔌 API Endpoints

### User Endpoints:

**Submit Support Ticket:**
```
POST /api/support/contact
Headers: Authorization: Bearer {token}
Body (form-data):
  - subject: string (required)
  - message: string (required)

Response:
{
  "success": true,
  "ticket_id": "abc123...",
  "support_level": "Email (48h response)",
  "email": "user@example.com"
}

Errors:
- 401: Not logged in
- 403: Free tier user (no credits purchased)
```

### Admin Endpoints:

**List Tickets:**
```
GET /api/admin/support-tickets?status=open|closed|all

Response:
[
  {
    "id": "abc123...",
    "user_email": "user@example.com",
    "subject": "Need help",
    "message": "Full message text...",
    "status": "open",
    "priority": "normal",
    "support_tier": "Email (48h response)",
    "credits_purchased": 100,
    "created_at": "2026-02-10T14:30:00",
    "updated_at": "2026-02-10T14:30:00"
  }
]
```

**Close Ticket:**
```
POST /api/admin/support-tickets/{ticket_id}/close

Response:
{
  "success": true,
  "message": "Ticket closed"
}
```

---

## 🚀 How to Use (Day-to-Day)

### When User Submits Ticket:

1. **You'll see in console logs:**
   ```
   [SUPPORT TICKET #abc12345] From: user@example.com | Subject: Need help
   ```

2. **Open admin dashboard:**
   - Go to: `http://localhost:5000/static/admin-support.html`
   - See new ticket at top (newest first)

3. **Read ticket:**
   - See full message
   - See user's email, support tier, credits purchased
   - Check when submitted

4. **Respond to user:**
   - Copy their email
   - Reply via Gmail/email client
   - Once resolved, click "✅ Close Ticket"

5. **Track stats:**
   - Dashboard shows open count vs total
   - Filter to see closed tickets (history)

---

## 📧 Responding to Tickets

**Manual Process (Current):**
1. User submits ticket
2. You see it in dashboard
3. Copy user's email
4. Send reply via your email client
5. Close ticket in dashboard when resolved

**Future: Email Integration (Optional):**
- Setup SendGrid/Mailgun
- Send automatic confirmation to user
- Get email notifications when ticket submitted
- Reply-to email creates response (advanced)

---

## 🔒 Security Notes

**Current State:**
- ✅ Users must be logged in (JWT token)
- ✅ Free tier blocked from submitting
- ⚠️ Admin dashboard has NO authentication

**For Production:**

### Option 1: Simple Password Protection
Add basic auth to admin endpoints:

```python
from fastapi import Header

def verify_admin(x_admin_key: str = Header(None)):
    if x_admin_key != "your-secret-admin-key":
        raise HTTPException(401, "Unauthorized")
    return True

@app.get("/api/admin/support-tickets")
async def list_tickets(
    admin: bool = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    # ... rest of code
```

Then add header to dashboard:
```javascript
fetch('/api/admin/support-tickets', {
    headers: {
        'X-Admin-Key': 'your-secret-admin-key'
    }
})
```

### Option 2: Admin User System
- Create admin flag on User model
- Require admin login to access dashboard
- More complex but more secure

### Option 3: VPN/Firewall
- Restrict `/static/admin-*` pages to your IP only
- Configure in nginx/hosting

**For Launch:** 
- Option 1 is enough (simple password)
- Very few people will even find /static/admin-support.html
- Add better auth later if needed

---

## 📊 Example Workflow

**Scenario:** User buys $5 starter pack, has trouble with OCR tool.

1. **User submits ticket:**
   - Subject: "OCR not working on my PDF"
   - Message: "I uploaded a PDF but it says 'error'. Can you help?"

2. **You see notification:**
   ```
   [SUPPORT TICKET #7f3e9a12] From: john@example.com | Subject: OCR not working on my PDF
   ```

3. **You open dashboard:**
   - See ticket at top
   - User: john@example.com
   - Support Tier: Email Support
   - Credits Purchased: 100
   - Message: "I uploaded a PDF but it says 'error'. Can you help?"

4. **You investigate:**
   - Check logs: See error was PDF too large (>20MB)
   - Solution: Need to tell user about file size limit

5. **You respond:**
   - Email john@example.com:
   ```
   Hi John,

   Thanks for contacting QuickTools support!

   The error you're seeing is because your PDF is larger than our 20MB limit. 
   Try compressing the PDF first, or splitting it into smaller files.

   Let me know if you need more help!

   Best,
   QuickTools Support
   ```

6. **You close ticket:**
   - Click "✅ Close Ticket" in dashboard
   - Ticket moves to "Closed" filter
   - Keeps history for reference

---

## 📈 Metrics to Track

**Things to Monitor:**
- Open ticket count (should stay low!)
- Average time to close
- Most common issues (subject lines)
- Support tier distribution

**Good Performance:**
- <5 open tickets at any time
- Close within 24-48 hours
- Common issues = opportunities to improve docs/UI

---

## 🎯 Future Improvements (Optional)

**Phase 2 (Month 2-3):**
- Email notifications when ticket submitted
- Auto-reply confirmation to user
- In-dashboard reply system (no need for Gmail)
- Ticket priority system (high/normal/low)

**Phase 3 (Month 6+):**
- Live chat integration (Crisp, Tawk.to)
- FAQ/Help Center to reduce tickets
- Auto-close tickets after X days
- Ticket assignment (if you hire support staff)
- Email parser (reply to ticket via email)

---

## ✅ Summary

**What's Built:**
- ✅ Free tier blocked from support
- ✅ Database storage for tickets
- ✅ Admin dashboard to view/manage tickets
- ✅ Filter, search, close tickets
- ✅ Real-time stats

**What You Do:**
1. Open `http://localhost:5000/static/admin-support.html` daily
2. Check for new tickets
3. Reply to users via email
4. Close tickets when resolved
5. Track patterns to improve product

**Time Investment:**
- 0-5 customers: ~5 min/day
- 10-20 customers: ~15 min/day
- 50+ customers: Consider hiring support or adding live chat

---

## 🔗 Quick Links

**Admin Dashboard:**
- Local: http://localhost:5000/static/admin-support.html
- Production: https://quicktools.io/static/admin-support.html

**API Docs:**
- List tickets: GET /api/admin/support-tickets?status=open
- Close ticket: POST /api/admin/support-tickets/{id}/close

**Database:**
- Table: `support_tickets`
- Query: `SELECT * FROM support_tickets WHERE status='open'`

---

**Ready to handle support tickets like a pro!** 🎫✨
