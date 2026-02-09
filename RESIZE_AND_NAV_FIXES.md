# Resize Tool & Navigation Fixes - February 9, 2026

## Issues Fixed

### 1. ✅ Image Resize: Force Exact Dimensions Option
**Problem:** Users could not force exact dimensions (e.g., 400×400 → 2000×600) - tool always maintained aspect ratio.

**Solution:** Added checkbox option to toggle between:
- **Maintain aspect ratio** (default, recommended)
- **Force exact dimensions** (may stretch/distort)

**Changes Made:**

#### Frontend (`resize.html`)
```html
<label>
    <input type="checkbox" id="maintainAspect" checked>
    <span>Maintain aspect ratio (recommended)</span>
</label>
<small>
    💡 When unchecked, image will be forced to exact dimensions 
    (may stretch/distort). When checked, leave one dimension 
    empty to auto-calculate.
</small>
```

**JavaScript validation:**
```javascript
const maintainAspect = document.getElementById('maintainAspect').checked;

// Validate both dimensions required when not maintaining aspect
if (!maintainAspect && (!width || !height)) {
    showMessage('Both width and height required when forcing exact dimensions', 'error');
    return;
}

formData.append('maintain_aspect', maintainAspect ? 'true' : 'false');
```

#### Backend (`app.py`)
```python
@app.post("/api/resize/single")
async def resize_single_image(
    file: UploadFile = File(...),
    width: int = Form(None),
    height: int = Form(None),
    format: str = Form("png"),
    maintain_aspect: str = Form("true"),  # NEW
    current_user: User = Depends(require_credits),
    db: Session = Depends(get_db)
):
    # Convert string to boolean
    maintain_aspect_bool = maintain_aspect.lower() == "true"
    
    # Resize image with maintain_aspect parameter
    resized_bytes = resize_image(
        contents, 
        width=width, 
        height=height, 
        maintain_aspect=maintain_aspect_bool,  # NEW
        format=format
    )
```

**How It Works Now:**

1. **Maintain Aspect Ratio (Checked - Default):**
   ```
   Original: 400×400px
   Input: Width=2000, Height=Auto
   Result: 2000×2000px ✅ (auto-calculated)
   
   Original: 400×400px
   Input: Width=2000, Height=600
   Result: 600×600px ✅ (fits within bounds)
   ```

2. **Force Exact Dimensions (Unchecked):**
   ```
   Original: 400×400px
   Input: Width=2000, Height=600
   Result: 2000×600px ✅ (stretched/distorted)
   
   Original: 800×600px
   Input: Width=1000, Height=1000
   Result: 1000×1000px ✅ (stretched to square)
   ```

**Validation:**
- If "Force exact dimensions" is checked, BOTH width AND height are required
- If "Maintain aspect ratio" is checked, at least ONE dimension is required

---

### 2. ✅ Background Remover: Fixed Navbar Navigation
**Problem:** When background remover tool was open (index.html#tools), clicking "Tools" or "Pricing" in navbar didn't work because you were already on index.html.

**Solution:** Added JavaScript handler to close the workspace and scroll to the clicked section.

**Changes Made:**

#### HTML (`index.html`)
```html
<div class="nav-links">
    <a href="#tools" class="nav-link" onclick="closeToolWorkspaceIfOpen(event)">Tools</a>
    <a href="#pricing" class="nav-link" onclick="closeToolWorkspaceIfOpen(event)">Pricing</a>
    <a href="/static/support.html" class="nav-link">Support</a>
    <a href="/static/api-keys.html" class="nav-link" id="apiKeysNav">API</a>
</div>
```

#### JavaScript (`app.js`)
```javascript
function closeToolWorkspaceIfOpen(event) {
    const workspace = document.getElementById('toolWorkspace');
    
    // Check if workspace is currently open
    if (workspace && workspace.style.display !== 'none') {
        closeToolWorkspace();  // Close it
        
        // Scroll to the target section after closing
        setTimeout(() => {
            const target = event.target.getAttribute('href');
            if (target) {
                document.querySelector(target)?.scrollIntoView({ behavior: 'smooth' });
            }
        }, 100);
        
        event.preventDefault();
    }
    // If workspace is not open, let the default anchor behavior work
}
```

**How It Works Now:**

1. **Background remover closed:**
   - Click "Tools" → Scrolls to tools section (normal behavior)
   - Click "Pricing" → Scrolls to pricing section (normal behavior)

2. **Background remover open:**
   - Click "Tools" → Closes workspace, shows tools section ✅
   - Click "Pricing" → Closes workspace, shows pricing section ✅
   - Smooth scrolling after workspace closes

3. **Other tool pages (resize, pdf, qr):**
   - Click "Tools" → Goes to index.html#tools (normal behavior)
   - No workspace to close, standard navigation

---

## Files Modified

### Frontend
1. `static/resize.html`
   - Added "Maintain aspect ratio" checkbox
   - Added validation for force exact dimensions
   - Pass maintain_aspect parameter to backend

2. `static/index.html`
   - Added onclick handlers to Tools/Pricing navbar links

3. `static/app.js`
   - Added `closeToolWorkspaceIfOpen()` function
   - Handles workspace closure and smooth scrolling

### Backend
4. `app.py`
   - Updated `/api/resize/single` endpoint
   - Added `maintain_aspect` parameter
   - Pass parameter to `resize_image()` function

---

## Testing Checklist

### Resize Tool
- [x] Checkbox toggles on/off
- [x] Default state: checked (maintain aspect)
- [x] With maintain aspect: one dimension auto-calculates
- [x] With maintain aspect: both dimensions fit within bounds
- [x] Without maintain aspect: both dimensions required
- [x] Without maintain aspect: image stretches to exact size
- [x] Validation errors show correctly

### Background Remover Navigation
- [x] Tools link works when workspace closed
- [x] Tools link closes workspace and scrolls to tools
- [x] Pricing link works when workspace closed
- [x] Pricing link closes workspace and scrolls to pricing
- [x] Smooth scrolling after workspace closes
- [x] Other navbar links work normally

---

## User Experience Improvements

**Before:**
- ❌ Could not force exact dimensions (always maintained aspect ratio)
- ❌ Navbar links didn't work when background remover was open

**After:**
- ✅ Users can choose to maintain aspect ratio OR force exact dimensions
- ✅ Clear UI with checkbox and helpful hint text
- ✅ Validation prevents errors
- ✅ Navbar navigation works from all states
- ✅ Smooth transitions between workspace and sections

---

## Hard Refresh Required!

Users need to clear cache to see these changes:
- **Windows/Linux:** `Ctrl + Shift + R`
- **Mac:** `Cmd + Shift + R`

Or use **Incognito/Private mode**.
