# PDF Split File Naming Improvement

**Date:** 2026-02-09  
**Issue:** Split PDF files have cryptic UUID names  
**Status:** ✅ Fixed

---

## 🔍 Problem

**Before:**
When you split `invoice.pdf`, files were named:
```
abc123-def456-789_page1.pdf
abc123-def456-789_page2.pdf
abc123-def456-789_page3.pdf
```

❌ **Not user-friendly!** Hard to identify which file it came from.

---

## ✅ Solution

**After:**
When you split `invoice.pdf`, files are now named:
```
invoice_page1_abc12345.pdf
invoice_page2_abc12345.pdf
invoice_page3_abc12345.pdf
```

✅ **Much better!** Clear which file it came from.

---

## 📋 Naming Pattern

```
{original_filename}_page{number}_{short_id}.pdf
```

**Example:**
- Original: `contract_2024.pdf`
- Split files:
  - `contract_2024_page1_a1b2c3d4.pdf`
  - `contract_2024_page2_a1b2c3d4.pdf`
  - `contract_2024_page3_a1b2c3d4.pdf`

**Benefits:**
- ✅ Original filename preserved
- ✅ Clear page number
- ✅ Short ID for uniqueness (8 chars, not full UUID)
- ✅ Easy to identify and organize

---

## 🎯 All PDF Operations Filenames

### Merge
```
merged_abc12345.pdf
```

### Split
```
original_page1_abc12345.pdf
original_page2_abc12345.pdf
```

### Compress
```
original_compressed_abc12345.pdf
```

---

## 📝 What Was Changed

**File:** `app.py`

**Before:**
```python
output_filename = f"{file_id}_page{idx}.pdf"
```

**After:**
```python
original_name = Path(file.filename).stem
output_filename = f"{original_name}_page{idx}_{file_id[:8]}.pdf"
```

**Changes:**
- Uses original filename (without extension)
- Adds clear `_page{number}` suffix
- Adds short 8-character ID (not full UUID)
- Much more user-friendly!

---

## 🚀 To Apply

```bash
cd /home/influ/projects/quicktools
sudo docker compose build
sudo docker compose restart
```

---

## 🧪 Test It

1. Upload a PDF named `report.pdf`
2. Click "Split PDF"
3. Download files → Should be named:
   - `report_page1_abc12345.pdf`
   - `report_page2_abc12345.pdf`
   - etc.

---

**Status:** ✅ **User-friendly filenames!**
