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

## Implementation Details

### Changes Made

1. **Updated `build.py`**: Added post-processing step that automatically adds `<!DOCTYPE html>` to the generated HTML file
   - Checks if DOCTYPE is missing before adding it
   - Runs after pygbag completes the build
   - Also applies the Finnish translation ("Aloita kasvipeli!")

2. **Created HTML template in `web/index.html`**: For future use with proper DOCTYPE structure
   - Includes charset and viewport meta tags
   - Contains proper HTML5 structure
   - Can be used if pygbag's custom template system is configured

### Why This Works

Pygbag uses a default HTML template from its CDN that doesn't include DOCTYPE. Rather than trying to override pygbag's template system (which can be complex), the post-processing approach:
- Is simple and maintainable
- Doesn't interfere with pygbag's build process
- Works reliably every time
- Can be extended with other post-processing steps if needed

## Additional Fixes: Audio System Error Handling

Added comprehensive error handling to `main.py` for audio initialization:
- Wrapped `audio.initialize()` and `audio.load_sounds()` in try-except
- If audio fails, game continues without audio (graceful degradation)
- **All errors are printed to browser console** (F12 > Console tab)
- Full Python traceback is printed for debugging

This allows us to see what's actually failing when the game shows a black screen.

## Testing Checklist

- [x] Run `uv run python build.py` - DOCTYPE added, error handling added
- [x] Check that `docs/index.html` starts with `<!DOCTYPE html>`
- [ ] Test locally: `uv run python build.py --serve` to verify it still works
- [ ] Deploy to GitHub Pages
- [ ] Open https://your-username.github.io/greenwelt/
- [ ] Press F12 to open Developer Tools > Console tab
- [ ] Look for error messages starting with "ERROR:" or "AUDIO ERROR:"
- [ ] If you see errors, copy them and share them - that's what was causing the black screen
- [ ] If no errors and game loads with "Aloita kasvipeli" button, you can click it to play

## Local Testing

```bash
# Build and run local test server
uv run python build.py --serve

# Then open browser to http://localhost:8000
```

## Deploy to GitHub Pages

```bash
# After testing locally:
uv run python build.py

# Commit and push
git add docs/
git commit -m "Fix: Add DOCTYPE to web build for Standards Mode"
git push
```

Then enable GitHub Pages in repository Settings (if not already enabled):
- Settings > Pages
- Source: Deploy from a branch
- Branch: main, folder: /docs
