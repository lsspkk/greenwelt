# Plant Courier Web Build Fix

## Problem Analysis

When deploying the Plant Courier game to web, the browser console shows this critical warning:

```
This page is in Quirks Mode. Page layout may be impacted. For Standards Mode use "<!DOCTYPE html>".
```

This happens because the generated `docs/index.html` file is missing the `<!DOCTYPE html>` declaration at the very beginning.

### Root Cause

Pygbag uses a default HTML template that doesn't include the DOCTYPE declaration. When no custom template is provided, it generates HTML that starts directly with `<html>` instead of `<!DOCTYPE html>`.

### Impact of Quirks Mode

- Page layout rendering may be inconsistent
- CSS may not work as expected
- JavaScript compatibility issues
- Poor performance
- Non-standard HTML parsing

## Solution

Create a proper HTML template in the `web/` directory that:
1. Includes the `<!DOCTYPE html>` declaration
2. Specifies proper HTML structure and metadata
3. Follows pygbag's template format requirements
4. Adds proper charset and viewport settings for web deployment

## Implementation Steps

### 1. Create/Update `web/index.html`

The file should include:
- `<!DOCTYPE html>` at the very beginning
- Proper HTML5 structure
- Meta tags for charset and viewport (important for responsive design)
- Valid HTML structure with `<head>` and `<body>` elements
- The pygbag-required `<script>` tag with the correct attributes

### 2. Update `build.py` (Optional)

The current build process already handles post-processing, so no changes are needed unless we want to add additional DOCTYPE validation.

## Expected Result

After this fix:
- The generated `docs/index.html` will start with `<!DOCTYPE html>`
- Browser will render in Standards Mode
- All Feature Policy warnings will still appear (these are from pygbag's script, harmless)
- The game will render more consistently across browsers
- Performance may improve slightly

## Testing Checklist

- [ ] Run `uv run python build.py`
- [ ] Check that `docs/index.html` starts with `<!DOCTYPE html>`
- [ ] Deploy to GitHub Pages
- [ ] Open the game in browser
- [ ] Check console - "Quirks Mode" warning should be gone
- [ ] Verify game runs correctly
- [ ] Test on multiple browsers (Chrome, Firefox, Safari)
