# PDF Merge - Multiple File Selection

**Issue:** Can't select multiple PDFs on macOS  
**Status:** ✅ Fixed (UI clarification)

---

## 🎯 How to Select Multiple Files

### On macOS:
**Hold `Cmd` key** while clicking files in the file picker

### On Windows/Linux:
**Hold `Ctrl` key** while clicking files

### Or (Both):
1. Click first file
2. Hold `Shift`
3. Click last file
→ Selects all files in between

---

## ✅ What Was Updated

**Changed instruction text from:**
```
"or click to browse (PDF - max 20MB each)"
```

**To:**
```
"or click to browse (hold Cmd/Ctrl to select multiple files)"
```

**Now users know they need to hold Cmd/Ctrl!**

---

## 🧪 How It Works

**1. Click Upload Area**
- Opens file picker

**2. Select Multiple Files**
- **Mac:** Hold `Cmd` + click each file
- **Windows:** Hold `Ctrl` + click each file
- **Range:** Click first, `Shift` + click last

**3. Click "Open"**
- All selected files appear in list
- Merge button enabled

**4. Click "Merge PDFs"**
- Merges all PDFs in order
- Downloads combined file
- 1 credit used

---

## 🎨 Alternative: Drag & Drop

**You can also drag multiple files:**
1. Select multiple PDFs in Finder/Explorer
2. Drag them to the upload area
3. Drop → All files added!

---

## 📋 File Modified

- `static/pdf-tools.html` - Updated instruction text

---

## 🚀 To Apply

**Hard refresh browser:**
```
Ctrl + Shift + R  (Windows/Linux)
Cmd + Shift + R   (Mac)
```

---

**Status:** ✅ **Instructions clearer, functionality already working!**
