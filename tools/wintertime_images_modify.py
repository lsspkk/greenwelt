#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pillow",
# ]
# ///
"""
Modify wintertime clothing images to be kid-friendly and visually cohesive.
Adds subtle girly effects while keeping images clearly identifiable.

Usage:
    uv run tools/wintertime_images_modify.py

Input: tools/wintertime-images/
Output: docs/wintertime/images/
"""

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter


# Paths
INPUT_DIR = Path(__file__).parent / "wintertime-images"
OUTPUT_DIR = Path(__file__).parent.parent / "docs" / "wintertime" / "images"

# Target size for portrait mobile (width x height)
TARGET_WIDTH = 400
TARGET_HEIGHT = 500


def enhance_colors(img: Image.Image) -> Image.Image:
    """Boost saturation for more vibrant, kid-friendly colors."""
    # Boost saturation for more vivid colors
    enhancer = ImageEnhance.Color(img)
    img = enhancer.enhance(1.2)
    
    # Slight brightness boost
    enhancer = ImageEnhance.Brightness(img)
    img = enhancer.enhance(1.05)
    
    return img


def add_bokeh_bubbles(img: Image.Image, count: int = 15, seed: int = None) -> Image.Image:
    """Add soft, dreamy bokeh bubble effects around the edges."""
    if seed is not None:
        random.seed(seed)
    
    result = img.convert("RGBA")
    w, h = img.size
    
    # Create overlay for bubbles
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    
    # Pastel colors for bubbles
    bubble_colors = [
        (255, 182, 193),  # Light pink
        (255, 218, 233),  # Pale pink
        (230, 190, 255),  # Light lavender
        (200, 230, 255),  # Light blue
        (255, 255, 200),  # Pale yellow
        (200, 255, 220),  # Mint
    ]
    
    for _ in range(count):
        # Place bubbles mostly around edges (not covering center)
        edge_zone = random.choice(['top', 'bottom', 'left', 'right', 'corner'])
        
        if edge_zone == 'top':
            x = random.randint(0, w)
            y = random.randint(0, int(h * 0.25))
        elif edge_zone == 'bottom':
            x = random.randint(0, w)
            y = random.randint(int(h * 0.75), h)
        elif edge_zone == 'left':
            x = random.randint(0, int(w * 0.2))
            y = random.randint(0, h)
        elif edge_zone == 'right':
            x = random.randint(int(w * 0.8), w)
            y = random.randint(0, h)
        else:  # corner
            corner = random.choice([(0, 0), (w, 0), (0, h), (w, h)])
            x = corner[0] + random.randint(-50, 50)
            y = corner[1] + random.randint(-50, 50)
        
        # Bubble size varies
        radius = random.randint(15, 45)
        
        # Create a single bubble with gradient
        bubble = create_bokeh_bubble(radius, random.choice(bubble_colors))
        
        # Paste bubble onto overlay
        paste_x = x - radius
        paste_y = y - radius
        
        # Only paste if within bounds
        if 0 <= paste_x < w - radius and 0 <= paste_y < h - radius:
            overlay.paste(bubble, (paste_x, paste_y), bubble)
    
    # Composite overlay onto image
    result = Image.alpha_composite(result, overlay)
    return result.convert("RGB")


def create_bokeh_bubble(radius: int, color: tuple) -> Image.Image:
    """Create a single soft bokeh bubble with gradient transparency."""
    size = radius * 2
    bubble = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    
    # Draw gradient circles from outside to inside
    for i in range(radius, 0, -1):
        # Opacity increases toward center, but stays soft
        # Max opacity around 40-60 for dreamy effect
        progress = 1 - (i / radius)
        opacity = int(25 + 35 * math.sin(progress * math.pi))
        
        draw = ImageDraw.Draw(bubble)
        draw.ellipse(
            [radius - i, radius - i, radius + i, radius + i],
            fill=(*color, opacity)
        )
    
    # Add a subtle bright spot (highlight) near top-left
    highlight_x = radius - radius // 3
    highlight_y = radius - radius // 3
    highlight_r = radius // 4
    draw = ImageDraw.Draw(bubble)
    draw.ellipse(
        [highlight_x - highlight_r, highlight_y - highlight_r,
         highlight_x + highlight_r, highlight_y + highlight_r],
        fill=(255, 255, 255, 50)
    )
    
    return bubble


def add_soft_glow(img: Image.Image) -> Image.Image:
    """Add a subtle dreamy glow effect by blending with blurred version."""
    # Create a brightened blurred version
    blurred = img.filter(ImageFilter.GaussianBlur(radius=12))
    
    # Brighten the blur slightly
    enhancer = ImageEnhance.Brightness(blurred)
    blurred = enhancer.enhance(1.1)
    
    # Blend with original (soft light effect)
    result = Image.blend(img, blurred, alpha=0.12)
    return result


def add_gradient_overlay(img: Image.Image) -> Image.Image:
    """Add a very subtle pink-to-transparent gradient at top and bottom."""
    w, h = img.size
    result = img.convert("RGBA")
    
    # Create gradient overlay
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    # Top gradient (subtle pink fading down)
    for y in range(int(h * 0.15)):
        opacity = int(20 * (1 - y / (h * 0.15)))
        draw.line([(0, y), (w, y)], fill=(255, 200, 220, opacity))
    
    # Bottom gradient (subtle pink fading up)
    for y in range(int(h * 0.85), h):
        opacity = int(20 * ((y - h * 0.85) / (h * 0.15)))
        draw.line([(0, y), (w, y)], fill=(255, 200, 220, opacity))
    
    result = Image.alpha_composite(result, overlay)
    return result.convert("RGB")


def add_rounded_corners(img: Image.Image, radius: int = 20) -> Image.Image:
    """Add rounded corners to the image."""
    mask = Image.new("L", img.size, 0)
    draw = ImageDraw.Draw(mask)
    
    w, h = img.size
    draw.rounded_rectangle([(0, 0), (w, h)], radius=radius, fill=255)
    
    result = img.convert("RGBA")
    result.putalpha(mask)
    
    # Create white background
    background = Image.new("RGBA", img.size, (255, 255, 255, 255))
    background.paste(result, mask=result.split()[3])
    
    return background.convert("RGB")


def resize_for_mobile(img: Image.Image) -> Image.Image:
    """Resize and crop image for portrait mobile display."""
    w, h = img.size
    target_ratio = TARGET_WIDTH / TARGET_HEIGHT
    current_ratio = w / h
    
    if current_ratio > target_ratio:
        # Image is wider - crop sides
        new_w = int(h * target_ratio)
        left = (w - new_w) // 2
        img = img.crop((left, 0, left + new_w, h))
    else:
        # Image is taller - crop top/bottom
        new_h = int(w / target_ratio)
        top = (h - new_h) // 2
        img = img.crop((0, top, w, top + new_h))
    
    # Resize to target dimensions
    img = img.resize((TARGET_WIDTH, TARGET_HEIGHT), Image.LANCZOS)
    return img


def add_decorative_border(img: Image.Image) -> Image.Image:
    """Add a cute decorative border with pastel colors."""
    w, h = img.size
    border_width = 8
    
    # Create border with gradient effect
    new_w = w + border_width * 2
    new_h = h + border_width * 2
    
    # Pastel pink border
    border_color = (255, 210, 220)
    result = Image.new("RGB", (new_w, new_h), border_color)
    
    # Add inner white line for depth
    inner = Image.new("RGB", (w + 4, h + 4), (255, 255, 255))
    result.paste(inner, (border_width - 2, border_width - 2))
    
    # Paste original image
    result.paste(img, (border_width, border_width))
    
    return result


def process_image(input_path: Path, output_path: Path, index: int) -> bool:
    """Process a single image with all effects."""
    try:
        img = Image.open(input_path).convert("RGB")
        
        # 1. Resize for mobile portrait
        img = resize_for_mobile(img)
        
        # 2. Enhance colors (more vibrant but natural)
        img = enhance_colors(img)
        
        # 3. Add soft dreamy glow
        img = add_soft_glow(img)
        
        # 4. Add subtle gradient overlay at top/bottom
        img = add_gradient_overlay(img)
        
        # 5. Add bokeh bubbles around edges (use filename hash as seed)
        bubble_seed = hash(input_path.stem) % 10000
        img = add_bokeh_bubbles(img, count=12, seed=bubble_seed)
        
        # 6. Add rounded corners
        img = add_rounded_corners(img, radius=20)
        
        # 7. Add decorative border
        img = add_decorative_border(img)
        
        # Save as JPEG
        img.save(output_path, "JPEG", quality=90, optimize=True)
        return True
        
    except Exception as e:
        print(f"  Error: {e}")
        return False


def main():
    """Process all wintertime images."""
    print("=" * 60)
    print("Wintertime Images Modifier")
    print("Making images kid-friendly with soft bokeh effects")
    print("=" * 60)
    
    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Find all jpg files
    input_files = sorted(INPUT_DIR.glob("*.jpg"))
    
    if not input_files:
        print(f"No images found in {INPUT_DIR}")
        return
    
    print(f"Found {len(input_files)} images to process\n")
    
    success_count = 0
    for i, input_path in enumerate(input_files):
        output_path = OUTPUT_DIR / input_path.name
        print(f"Processing: {input_path.name}")
        
        if process_image(input_path, output_path, i):
            print(f"  ✓ Saved: {output_path.name}")
            success_count += 1
        else:
            print(f"  ✗ Failed")
    
    print("\n" + "=" * 60)
    print(f"✅ Processed {success_count}/{len(input_files)} images")
    print(f"📁 Output: {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
