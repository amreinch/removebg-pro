# Image Quality Settings Explained

**Updated:** 2026-02-09  
**Default Quality:** Changed from 95% → 100%

---

## 🎯 Why Only JPG/WebP Have Quality Slider?

### Lossy Formats (Quality Matters)
**JPG, WebP**
- ✅ Quality slider available
- Discard data to reduce file size
- Lower quality = smaller file but worse image
- Can choose 1-100%

### Lossless Formats (No Quality Needed)
**PNG, BMP, TIFF**
- ❌ No quality slider (doesn't apply)
- Preserve ALL image data perfectly
- File size is what it is
- Always "100% quality" by nature

---

## 📊 Format Comparison

| Format | Type | Quality Control | Best For |
|--------|------|----------------|----------|
| **JPG** | Lossy | ✅ Yes (1-100%) | Photos, web images |
| **WebP** | Lossy | ✅ Yes (1-100%) | Modern web, smallest size |
| **PNG** | Lossless | ❌ No | Graphics, transparency, text |
| **BMP** | Lossless | ❌ No | Raw images, legacy |
| **TIFF** | Lossless | ❌ No | Professional, print |

---

## 🎚️ Quality Settings Guide

### Default: 100% (Maximum Quality)
**Why 100% as default:**
- Safest choice (no data loss)
- User can always reduce if needed
- Better to start high and go down than vice versa

### Recommended Settings

**100% - Maximum Quality**
- Perfect for: Professional work, print, archival
- File size: Largest
- Visual quality: Perfect

**90-95% - High Quality**
- Perfect for: Web use, most purposes
- File size: 20-40% smaller than 100%
- Visual quality: Barely noticeable difference

**80-85% - Good Quality**
- Perfect for: Email, social media
- File size: 50-60% smaller
- Visual quality: Slight loss but acceptable

**50-70% - Medium Quality**
- Perfect for: Thumbnails, quick previews
- File size: 70-80% smaller
- Visual quality: Visible compression artifacts

---

## 💡 Why Not Always 100%?

**Trade-offs:**

| Quality | File Size | Use Case |
|---------|-----------|----------|
| 100% | 2.5 MB | Professional, print |
| 95% | 1.5 MB | Web (great quality) ⭐ |
| 85% | 800 KB | Web (good quality) |
| 70% | 400 KB | Email, social media |
| 50% | 200 KB | Thumbnails only |

**Most users choose 85-95% for web use.**

---

## 🔄 What Changed

**Before:**
- Default: 95%
- Help text: "Higher quality = larger file size"

**After:**
- Default: 100%
- Help text: "100% = Maximum quality (larger file). 85-95% = Good balance. JPG/WebP only."

**Why better:**
- Conservative default (no surprise quality loss)
- Clear explanation of trade-offs
- Notes that it only applies to JPG/WebP
- Suggests good alternatives (85-95%)

---

## 🧪 Example: Converting Same Image

**PNG → JPG conversions:**

```
Original PNG: 3.2 MB (lossless)

JPG 100%: 2.8 MB (perfect quality)
JPG 95%:  1.6 MB (excellent quality, barely noticeable)
JPG 85%:  900 KB (good quality, slight artifacts)
JPG 70%:  500 KB (ok quality, visible compression)
JPG 50%:  250 KB (poor quality, obvious artifacts)
```

**Conclusion:** 85-95% is the "sweet spot" for most web use!

---

## 🎯 User Guidance

**We should add this to the UI:**

**For JPG/WebP conversions, show tip:**
> 💡 Tip: 100% gives maximum quality. For web use, try 90-95% for smaller files with minimal quality loss.

**For PNG/BMP/TIFF conversions:**
> ℹ️ These formats are lossless - quality is always 100% (no data loss).

---

## 📝 Summary

**Why quality slider:**
- Only for lossy formats (JPG, WebP)
- Lossless formats (PNG, BMP, TIFF) don't need it

**Why 100% default:**
- Conservative choice
- User decides if they want smaller files
- No surprise quality loss

**Common use:**
- Professional: 100%
- Web: 85-95%
- Social: 70-85%
- Thumbnails: 50-70%

---

**Status:** ✅ **Default changed to 100% + better explanation!**
