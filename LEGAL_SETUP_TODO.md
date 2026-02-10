# Legal Pages - Setup Guide

## ✅ What's Done

Created 3 legal pages with Swiss/EU compliance:
- `/static/impressum.html` - Contact & business info
- `/static/privacy.html` - GDPR + Swiss DPA compliant
- `/static/terms.html` - Service terms + credit pack terms

**Implementation:**
- ✅ Footer added to index.html with links
- ✅ Terms checkbox added to signup form (required)
- ✅ All pages styled and mobile-responsive

## 📝 What YOU Need to Fill In

Search and replace these placeholders in the legal pages:

### In ALL 3 Files (impressum.html, privacy.html, terms.html):

1. **`[YOUR FULL NAME or COMPANY NAME]`**
   - Example: "Christoph Amrein" or "QuickTools GmbH"
   
2. **`[YOUR STREET ADDRESS]`**
   - Example: "Musterstrasse 123"
   
3. **`[POSTAL CODE] [CITY]`**
   - Example: "8001 Zürich"
   
4. **`[YOUR-EMAIL]@example.com`**
   - Example: "contact@quicktools.com" or your personal email
   
5. **`[COMPANY REGISTRATION NUMBER if applicable]`**
   - If registered: "CHE-123.456.789"
   - If not: Remove this line or write "N/A - Individual"
   
6. **`[VAT ID if applicable: CHE-XXX.XXX.XXX MWST]`**
   - Only if revenue > CHF 100K/year
   - Otherwise remove this line

### In privacy.html only:

7. **`[SERVER LOCATION]`**
   - Example: "Switzerland" or "EU (Germany)" depending on your hosting

### In terms.html only:

8. **`[YOUR CANTON]`**
   - Example: "Zürich" or "Bern" (for court jurisdiction)

## 🚀 Quick Find & Replace

Run these commands to update all at once:

```bash
cd ~/projects/quicktools/static

# Your name/company
sed -i 's/\[YOUR FULL NAME or COMPANY NAME\]/Your Actual Name/g' impressum.html privacy.html terms.html

# Your address
sed -i 's/\[YOUR STREET ADDRESS\]/Your Street 123/g' impressum.html privacy.html terms.html
sed -i 's/\[POSTAL CODE\] \[CITY\]/8001 Zürich/g' impressum.html privacy.html terms.html

# Your email
sed -i 's/\[YOUR-EMAIL\]@example.com/your-email@domain.com/g' impressum.html privacy.html terms.html

# Server location (in privacy.html)
sed -i 's/\[SERVER LOCATION\]/Switzerland/g' privacy.html

# Canton (in terms.html)
sed -i 's/\[YOUR CANTON\]/Zürich/g' terms.html
```

## ⚖️ Legal Compliance Checklist

Before launching:

### Required Now:
- [ ] Fill in all placeholder text above
- [ ] Verify email address is correct
- [ ] Confirm server location (check hosting provider)
- [ ] Test signup flow (Terms checkbox must be checked)
- [ ] Check all footer links work

### Required at CHF 100K Revenue:
- [ ] Register for VAT (MWST)
- [ ] Add VAT ID to Impressum
- [ ] Consider registering GmbH

### Recommended:
- [ ] Get lawyer review (CHF 500-800 one-time)
- [ ] Business liability insurance (optional until scaling)
- [ ] Professional email address (not @gmail)

## 📄 What Each Page Does

### Impressum
- Swiss/EU legal requirement
- Shows who runs the service
- Contact information
- Business registration details

### Privacy Policy
- GDPR + Swiss DPA compliant
- Explains data collection
- User rights (access, deletion, export)
- Required for EU customers

### Terms of Service
- Legal contract with users
- Credit pack terms (non-refundable, no expiry)
- Service usage rules
- Liability limitations

## 🔒 GDPR Compliance

Your current setup is GDPR-compliant:
- ✅ Privacy Policy with all required info
- ✅ Clear data collection notice
- ✅ User consent at signup (checkbox)
- ✅ Right to deletion (users can delete account)
- ✅ Right to export data
- ✅ Stripe handles payment data
- ✅ Files deleted after 24-48h

## 💡 Pro Tips

### Email Address
Use a professional domain email:
- ❌ quicktools123@gmail.com
- ✅ contact@yourdomain.com
- ✅ support@quicktools.com

### Physical Address
- Can use a virtual office (Regus, etc.) if you don't want home address public
- Must be a valid postal address in Switzerland

### Starting as Individual (Einzelfirma)
- Use your personal name
- No company registration needed
- Just declare income on tax return
- Simple and free to start

### Upgrading to GmbH Later
- Once revenue grows (CHF 50-100K+)
- Costs CHF 2K-5K to register
- Better liability protection
- More professional image

## 🆘 Need Help?

### Quick Legal Review (Swiss):
- LegalTech: lexly.ch (~CHF 500)
- Traditional lawyer: CHF 800-1500
- Worth it once you have first paying customers

### Tax Questions:
- Swiss tax office: admin.ch
- Accountant: ~CHF 800/year for simple setup

## ✅ Launch Checklist

Before accepting first payment:
1. Fill in all placeholders
2. Test signup with Terms checkbox
3. Verify all footer links work
4. Have someone review the pages
5. Keep a copy of these terms (date-stamped)

You're 95% there - just fill in your details! 🚀
