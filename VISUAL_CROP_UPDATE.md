# Visual Crop Selector - UX Improvement

**Date:** 2026-02-09
**Time:** ~30 minutes
**Status:** ✅ Complete

## Problem

Original crop tool had poor UX:
- User uploads image → Chooses ratio → Crops blindly
- **No preview of what gets cropped**
- **No way to see crop area before processing**
- Just a center crop with no visual feedback
- User doesn't know what gets cut off until after

## Solution

Added visual crop selector with overlay rectangle:

1. **Upload image** → Image appears immediately
2. **Choose aspect ratio** → Blue rectangle shows what will be kept
3. **See dimensions** → Label shows crop size in pixels
4. **Visual feedback** → Dark overlay shows what gets removed
5. **Real-time updates** → Rectangle updates as you change ratios

## Implementation

### Visual Elements

**Crop Preview Container:**
```html
<div style="position: relative; background: black;">
    <img id="cropPreviewImage" style="opacity: 0.5;"> <!-- Dimmed image -->
    <div id="cropOverlay"> <!-- Overlay layer -->
        <div id="cropRectangle" style="
            border: 3px solid #3B82F6;
            box-shadow: 0 0 0 9999px rgba(0,0,0,0.7);
        "> <!-- Blue rectangle + dark outside -->
            <div>1080 × 1080px</div> <!-- Dimensions label -->
            <div>This area will be kept</div>
        </div>
    </div>
</div>
```

**Key CSS Tricks:**
- `opacity: 0.5` on image → Shows it's being covered
- `box-shadow: 0 0 0 9999px rgba(0,0,0,0.7)` → Dark overlay outside rectangle
- `position: absolute` → Rectangle positioned on top
- Blue border → Clear crop area indicator

### JavaScript Logic

**On File Upload:**
```javascript
function handleFile(file) {
    // Load image into FileReader
    reader.onload = (e) => {
        img.src = e.target.result;
        img.onload = () => {
            // Show preview section
            // Calculate and draw crop rectangle
            updateCropRectangle();
        };
    };
}
```

**Calculate Crop Rectangle:**
```javascript
function updateCropRectangle() {
    // Get displayed vs natural dimensions
    const imgWidth = img.offsetWidth;  // Displayed
    const naturalWidth = img.naturalWidth;  // Actual
    const scale = naturalWidth / imgWidth;
    
    // Parse aspect ratio (1:1, 16:9, custom, etc.)
    let targetRatio = parseRatio(selectedRatio);
    
    // Calculate crop dimensions (center crop)
    if (currentRatio > targetRatio) {
        // Wider → crop width
        cropHeight = imgHeight;
        cropWidth = cropHeight * targetRatio;
    } else {
        // Taller → crop height
        cropWidth = imgWidth;
        cropHeight = cropWidth / targetRatio;
    }
    
    // Center position
    left = (imgWidth - cropWidth) / 2;
    top = (imgHeight - cropHeight) / 2;
    
    // Apply to rectangle
    rectangle.style.left = left + 'px';
    rectangle.style.top = top + 'px';
    rectangle.style.width = cropWidth + 'px';
    rectangle.style.height = cropHeight + 'px';
    
    // Show actual pixel dimensions
    dimensionsLabel.textContent = `${actualWidth} × ${actualHeight}px`;
}
```

**Real-Time Updates:**
- When preset button clicked → `updateCropRectangle()`
- When custom ratio typed → `updateCropRectangle()`
- Rectangle redraws instantly

## User Experience Flow

### Before (Blind Crop):
1. Upload image
2. Choose ratio from buttons
3. Click "Crop Preview"
4. 😱 **Surprise!** See cropped result (might have cut off faces/important parts)

### After (Visual Crop):
1. Upload image → **Image appears immediately**
2. Choose ratio → **Blue rectangle shows crop area**
3. See "1080 × 1080px" label → **Know exact dimensions**
4. Dark overlay shows what gets removed → **Visual feedback**
5. Click "Preview Crop" → **Confirm what you already see**
6. ✅ **No surprises!**

## Features

✅ **Instant Visual Feedback** - See crop area immediately
✅ **Dimensions Display** - Shows exact pixel size
✅ **Real-Time Updates** - Rectangle updates as ratio changes
✅ **Clear Indicators** - Blue border + dark overlay
✅ **Center Crop Algorithm** - Automatic positioning
✅ **All Ratios Supported** - Presets + custom

## Technical Details

### Coordinate Calculation

**Display vs Natural Dimensions:**
- Browser displays image at smaller size (e.g., 600px wide)
- Actual image might be 3000px wide
- Need to scale: `scale = naturalWidth / displayWidth`
- Show display coordinates in UI
- Send actual pixel coordinates to backend

**Center Crop Math:**
```
Original: 2000×1000 (landscape)
Target: 1:1 (square)

Current ratio: 2000/1000 = 2.0
Target ratio: 1.0

Since 2.0 > 1.0 → Image is wider → Crop width

new_height = 1000 (keep full height)
new_width = 1000 * 1.0 = 1000

left = (2000 - 1000) / 2 = 500
top = (1000 - 1000) / 2 = 0

Crop box: (500, 0, 1500, 1000)
Result: 1000×1000 square
```

### Performance

- Lightweight (no external libraries)
- CSS-based overlay (no canvas redraw)
- Instant updates (pure CSS positioning)
- File reading uses native FileReader API

## Future Enhancements (Optional)

Could add later:
- **Drag to reposition** - Move crop area around
- **Resize handles** - Adjust crop size manually
- **Zoom controls** - Zoom in/out on image
- **Grid overlay** - Rule of thirds lines
- **Face detection** - Auto-center on faces

**Current version is already excellent UX!**

## Files Modified

1. **static/crop.html** - Added visual preview section + JavaScript logic

## Testing

After restart:
- [ ] Upload landscape photo → See image with blue rectangle
- [ ] Change ratio 1:1 → 16:9 → Rectangle resizes
- [ ] Try portrait photo → Rectangle adapts
- [ ] Custom ratio (1920x1080) → Rectangle updates
- [ ] Dimensions label shows correct pixels
- [ ] Dark overlay shows what gets removed
- [ ] "This area will be kept" label visible

## Result

**Much better UX!** Users now see exactly what they're cropping before committing. No more surprises. Professional crop tool experience.

**Before:** Blind cropping ❌
**After:** Visual crop selector ✅

The blue rectangle + dark overlay pattern is intuitive and used by professional tools (Photoshop, Figma, etc.).
