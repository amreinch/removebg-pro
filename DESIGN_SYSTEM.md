# QuickTools Design System

## Overview
Professional, modern design system built with consistency and user experience in mind.

## Brand Identity

### Colors
**Primary Palette:**
- Primary Blue: `#2563EB` (var(--brand-primary))
- Primary Dark: `#1D4ED8` (var(--brand-primary-dark))
- Secondary Purple: `#7C3AED` (var(--brand-secondary))

**Semantic Colors:**
- Success: `#10B981`
- Danger: `#EF4444`
- Warning: `#F59E0B`
- Info: `#3B82F6`

**Neutral Palette:**
- Gray scale from 50-900 (warmer tones)
- Background: `#FFFFFF` (primary), `#FAFAFA` (secondary)

### Typography
- **Font Family:** Inter (Google Fonts)
- **Weights:** 400 (regular), 500 (medium), 600 (semi-bold), 700 (bold), 800 (extra-bold)
- **Scale:** xs (12px) → 5xl (48px)

### Spacing
8px base grid system:
- 1 = 4px
- 2 = 8px
- 3 = 12px
- 4 = 16px
- 5 = 24px
- 6 = 32px
- 8 = 48px
- 10 = 64px
- 12 = 96px

### Shadows
Soft, refined shadows using rgba with low opacity:
- sm, base, md, lg, xl, 2xl variants
- Consistent drop shadows for depth

### Border Radius
- sm: 4px
- base: 8px
- lg: 12px
- xl: 16px
- 2xl: 24px
- full: 9999px (pills)

## Components

### Navigation Bar
**Structure:**
```
Logo | Tools | Pricing | Support | API | [User Menu] / [Auth Buttons]
```

**Consistent Across All Pages:**
- Sticky positioning
- 72px height
- Blur backdrop effect
- Same link structure everywhere

**Links:**
- Tools → `/static/index.html#tools`
- Pricing → `/static/index.html#pricing`
- Support → `/static/support.html`
- API → `/static/api-keys.html` (Pro/Business only)

### Buttons
**Variants:**
- Primary: Gradient blue/purple
- Secondary: White with border
- Text: Transparent with hover effect
- Danger: Red (for destructive actions)

**Sizes:**
- Small: 8px/16px padding
- Base: 12px/20px padding
- Large: 16px/24px padding

### Cards
**Tool Cards:**
- Rounded corners (2xl)
- Hover lift effect
- Icon gradient background
- Consistent padding (24px)
- Border on hover (primary color)

**Pricing Cards:**
- Similar structure to tool cards
- Featured card: scale + border highlight
- Clear hierarchy in pricing info

### Forms
**Inputs:**
- 2px border (gray-200)
- Focus: primary color + ring
- 12px padding
- Rounded (lg)
- Full width

**Validation:**
- Error: Red border + light red background
- Success: Green border + light green background

### Messages/Alerts
**Types:**
- Error (red)
- Success (green)
- Info (blue)
- Warning (yellow)

**Structure:**
- Colored left border
- Light tinted background
- Clear typography hierarchy

## Pages Structure

### Home (`index.html`)
1. Hero Section
2. Tools Grid
3. Tool Workspace (background removal)
4. Pricing Section
5. Footer

### Support (`support.html`)
- Navbar
- Support form
- Tier-based response time info

### API Keys (`api-keys.html`)
- Navbar
- Key creation form
- Key list with management
- Usage examples

## Responsive Design

### Breakpoints
- Mobile: < 768px
- Tablet: 768px - 1024px
- Desktop: > 1024px

### Mobile Adjustments
- Hide nav-links on mobile
- Stack tool/pricing cards
- Full-width buttons
- Smaller hero text
- Collapsible user info

## Best Practices

### Do's ✅
- Use CSS variables for colors
- Maintain consistent spacing
- Use semantic HTML
- Test on all breakpoints
- Keep accessibility in mind

### Don'ts ❌
- Don't use inline styles (use utility classes)
- Don't mix old/new branding
- Don't create custom colors (use palette)
- Don't forget hover/focus states
- Don't skip mobile testing

## Implementation Checklist

When creating a new page:
- [ ] Use `styles.css` stylesheet
- [ ] Include Inter font from Google Fonts
- [ ] Copy standard navbar structure
- [ ] Use consistent container widths
- [ ] Apply proper section spacing
- [ ] Add mobile responsive styles
- [ ] Test all interactive states
- [ ] Verify link consistency

## Future Improvements
- [ ] Dark mode support
- [ ] Animation library integration
- [ ] Component library (React/Vue)
- [ ] Design token system
- [ ] Storybook documentation
