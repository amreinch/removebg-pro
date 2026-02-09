# Resize Tool: Aspect Ratio UX Fix - February 9, 2026

## Issue
When "Maintain aspect ratio" was checked, users could still enter BOTH width and height values, which was confusing:
- ❌ Which dimension would be used?
- ❌ How does auto-calculation work?
- ❌ No clear feedback about what would happen

## Solution
Implemented **mutual exclusivity** for dimension inputs when maintaining aspect ratio.

---

## How It Works Now

### **Maintain Aspect Ratio: CHECKED (Default)**

**Behavior:**
- Enter **width** → height field **clears** and shows placeholder "Auto-calculated"
- Enter **height** → width field **clears** and shows placeholder "Auto-calculated"
- Can only specify ONE dimension at a time
- Validation prevents both from being filled

**Example:**
```
User enters Width: 2000
  → Height field clears
  → Height placeholder: "Auto-calculated"
  → Result: Image scaled to 2000px wide, height maintains ratio
```

### **Maintain Aspect Ratio: UNCHECKED**

**Behavior:**
- Both fields required (placeholders change to "Required")
- Must specify exact width AND height
- Image will be stretched/distorted to exact dimensions
- Validation enforces both fields filled

**Example:**
```
User enters Width: 2000, Height: 600
  → Result: Image forced to exactly 2000×600 (may distort)
```

---

## Code Changes

### JavaScript Logic
```javascript
// When maintain aspect is checked
widthInput.addEventListener('input', () => {
    if (widthInput.value) {
        heightInput.value = '';  // Clear the other field
        heightInput.placeholder = 'Auto-calculated';
    }
});

heightInput.addEventListener('input', () => {
    if (heightInput.value) {
        widthInput.value = '';  // Clear the other field
        widthInput.placeholder = 'Auto-calculated';
    }
});
```

### Validation
```javascript
if (maintainAspect && width && height) {
    showMessage('When maintaining aspect ratio, specify only ONE dimension', 'error');
    return;
}

if (!maintainAspect && (!width || !height)) {
    showMessage('When forcing exact dimensions, BOTH width and height are required', 'error');
    return;
}
```

### Dynamic Placeholders
```javascript
maintainAspectCheckbox.addEventListener('change', () => {
    if (checked) {
        widthInput.placeholder = 'Auto';
        heightInput.placeholder = 'Auto';
    } else {
        widthInput.placeholder = 'Required';
        heightInput.placeholder = 'Required';
    }
});
```

---

## User Experience Flow

### Scenario 1: Maintain Aspect (Default)
1. User checks "Maintain aspect ratio" ✓
2. User enters Width: 2000
3. Height field **automatically clears** and shows "Auto-calculated"
4. User clicks "Resize Image"
5. Backend calculates height based on original aspect ratio
6. Result: Properly scaled image

### Scenario 2: Force Exact Dimensions
1. User unchecks "Maintain aspect ratio"
2. Placeholders change to "Required" on both fields
3. User must enter Width: 2000 AND Height: 600
4. User clicks "Resize Image"
5. Backend forces exact dimensions (may stretch)
6. Result: Image exactly 2000×600 (possibly distorted)

### Scenario 3: User Error (Maintain Aspect + Both Fields)
1. User has "Maintain aspect ratio" checked
2. User somehow enters both width AND height
3. Click "Resize Image"
4. ❌ Validation error: "Specify only ONE dimension"
5. User corrects by clearing one field
6. Success

---

## UI Feedback

**Clear visual cues:**
- ✅ Checkbox state clearly shows mode
- ✅ Placeholder text changes dynamically
- ✅ Fields auto-clear when appropriate
- ✅ Helpful hint text explains behavior
- ✅ Validation messages are specific

**Hint text:**
```
💡 Checked: Set one dimension, the other auto-calculates.
   Unchecked: Set both dimensions to force exact size (may distort).
```

---

## Technical Details

### Event Listeners
- `maintainAspect.change` → Updates placeholders and mode
- `widthInput.input` → Clears height if maintain aspect
- `heightInput.input` → Clears width if maintain aspect

### Validation Rules
| Mode | Width | Height | Valid? |
|------|-------|--------|--------|
| Maintain | ✓ | ✗ | ✅ Yes |
| Maintain | ✗ | ✓ | ✅ Yes |
| Maintain | ✓ | ✓ | ❌ No (error) |
| Maintain | ✗ | ✗ | ❌ No (error) |
| Force | ✓ | ✓ | ✅ Yes |
| Force | ✓ | ✗ | ❌ No (error) |
| Force | ✗ | ✓ | ❌ No (error) |

---

## Files Modified
1. `static/resize.html` - Added mutual exclusivity logic and validation

---

## Benefits

### Clarity
- ✅ No confusion about which dimension is used
- ✅ Clear visual feedback
- ✅ Explicit behavior based on checkbox state

### Prevention
- ✅ Prevents user errors
- ✅ Auto-clears conflicting values
- ✅ Clear validation messages

### User Experience
- ✅ Intuitive behavior
- ✅ Less cognitive load
- ✅ Faster workflow

---

## Testing Checklist

### Maintain Aspect Ratio (Checked)
- [x] Enter width → height clears
- [x] Enter height → width clears
- [x] Placeholder updates to "Auto-calculated"
- [x] Validation prevents both filled
- [x] Submit with one dimension works
- [x] Backend calculates other dimension correctly

### Force Exact (Unchecked)
- [x] Placeholders show "Required"
- [x] Both fields can be filled
- [x] Validation requires both
- [x] Submit with both dimensions works
- [x] Backend uses exact dimensions

### Edge Cases
- [x] Toggle checkbox clears/updates fields correctly
- [x] Validation messages are clear
- [x] No JavaScript errors

---

## Hard Refresh Required!

Users need to clear cache:
- **Windows/Linux:** `Ctrl + Shift + R`
- **Mac:** `Cmd + Shift + R`

Or use **Incognito/Private mode**.
