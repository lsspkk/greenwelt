import os
from PIL import Image, ImageFilter, ImageOps, ImageDraw, ImageChops
from collections import deque

# Output size for sprites
SPRITE_SIZE = 44

# Retro effect blend: 0.0 = fully original, 1.0 = fully retro
RETRO_BLEND = 0.10

# Palette for the retro effect (from modify.py)
PALETTE_COLORS = [
    (0, 0, 0),
    (29, 43, 83),
    (126, 37, 83),
    (0, 135, 81),
    (171, 82, 54),
    (255, 119, 168),
    (255, 204, 102),
    (255, 255, 255),
]


def make_palette_image(colors):
    palette = []
    for (r, g, b) in colors:
        palette += [r, g, b]
    while len(palette) < 768:
        palette += [0, 0, 0]
    pal = Image.new("P", (16, 16))
    pal.putpalette(palette)
    return pal


def amplify_edges(edge, passes=2):
    for _ in range(passes):
        edge = edge.filter(ImageFilter.MaxFilter(3))
    return edge


def pixelate(img, pixel_size):
    if pixel_size <= 1:
        return img
    w, h = img.size
    small = img.resize(
        (max(1, w // pixel_size), max(1, h // pixel_size)), Image.NEAREST
    )
    return small.resize((w, h), Image.NEAREST)


def add_scanlines(img, spacing=2, opacity=48):
    if spacing <= 1 or opacity <= 0:
        return img
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    w, h = img.size
    for y in range(0, h, spacing):
        draw.line([(0, y), (w, y)], fill=(0, 0, 0, opacity))
    base = img.convert("RGBA")
    return Image.alpha_composite(base, overlay).convert("RGB")


def cartoonize_retro(img, poster_bits=6, pixel_size=4,
                     edge_threshold=125, edge_thick=1,
                     scan_spacing=3, scan_opacity=36):
    """The retro game graphics effect from modify.py."""
    color = ImageOps.posterize(img, bits=poster_bits)
    color = color.filter(ImageFilter.SMOOTH_MORE)
    pal_img = make_palette_image(PALETTE_COLORS)

    color = color.filter(ImageFilter.GaussianBlur(0.6))
    quant = color.quantize(
        palette=pal_img, dither=Image.FLOYDSTEINBERG
    ).convert("RGB")
    quant = quant.filter(ImageFilter.MedianFilter(3))
    quant = pixelate(quant, pixel_size)

    gray = img.convert("L").filter(ImageFilter.FIND_EDGES)
    edge = gray.point(lambda x: 255 if x > edge_threshold else 0, "L")
    edge = amplify_edges(edge, passes=edge_thick)

    final = quant.convert("RGBA")
    black_layer = Image.new("RGBA", final.size, (0, 0, 0, 255))
    final.paste(black_layer, mask=edge)
    final = final.convert("RGB")
    final = add_scanlines(final, spacing=scan_spacing, opacity=scan_opacity)
    return final


def remove_gray_background(img, tolerance=40):
    """Flood-fill white background from edges to transparent."""
    print("--- floodfill start ---")

    img = img.convert("RGBA")
    pixels = img.load()
    w, h = img.size
    fill_color = (255, 0, 255, 0)
    bg_r, bg_g, bg_b = 255, 255, 255
    visited = set()

    print(f"  {w}x{h}, bg=({bg_r},{bg_g},{bg_b}), tolerance={tolerance}")

    # Sample edge colors before overwriting
    edge_colors = [pixels[x, 0] for x in range(0, w, max(1, w // 4))][:5]
    print(f"  edge colors (top row): {edge_colors}")

    def is_bg(x, y):
        r, g, b, a = pixels[x, y]
        return (abs(r - bg_r) < tolerance and
                abs(g - bg_g) < tolerance and
                abs(b - bg_b) < tolerance)

    # Fill outermost 2px border unconditionally (handles gray edges)
    border_thickness = 2
    for thick in range(border_thickness):
        for x in range(w):
            for y in [thick, h - 1 - thick]:
                if 0 <= y < h and (x, y) not in visited:
                    visited.add((x, y))
                    pixels[x, y] = fill_color
        for y in range(h):
            for x in [thick, w - 1 - thick]:
                if 0 <= x < w and (x, y) not in visited:
                    visited.add((x, y))
                    pixels[x, y] = fill_color

    # Seed flood fill from inner edges (offset inward past gray border)
    inner_offset = 5
    queue = deque()
    seed_colors = []

    for x in range(w):
        for y_inner in [inner_offset, h - 1 - inner_offset]:
            if 0 <= y_inner < h and is_bg(x, y_inner) and (x, y_inner) not in visited:
                if len(seed_colors) < 5:
                    seed_colors.append(pixels[x, y_inner])
                queue.append((x, y_inner))
                visited.add((x, y_inner))

    for y in range(h):
        for x_inner in [inner_offset, w - 1 - inner_offset]:
            if 0 <= x_inner < w and is_bg(x_inner, y) and (x_inner, y) not in visited:
                if len(seed_colors) < 5:
                    seed_colors.append(pixels[x_inner, y])
                queue.append((x_inner, y))
                visited.add((x_inner, y))

    print(f"  seeds={len(queue)}, seed colors: {seed_colors}")

    # BFS flood fill
    filled = 0
    while queue:
        cx, cy = queue.popleft()
        pixels[cx, cy] = fill_color
        filled += 1
        for nx, ny in [(cx-1, cy), (cx+1, cy), (cx, cy-1), (cx, cy+1)]:
            if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in visited:
                visited.add((nx, ny))
                if is_bg(nx, ny):
                    queue.append((nx, ny))

    pct = filled / (w * h) * 100 if w * h else 0
    print(f"  filled={filled} ({pct:.1f}%)")
    print("--- floodfill end ---")
    return img


def soften_dark_pixels(img, dark_threshold=60, lighten_amount=80):
    """Lighten very dark pixels to reduce harsh black outlines.
    Run this BEFORE resizing so the outlines don't dominate at small size."""
    img = img.copy()
    pixels = img.load()
    w, h = img.size

    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            if a == 0:
                continue
            # If pixel is very dark, lighten it
            brightness = (r + g + b) / 3
            if brightness < dark_threshold:
                r = min(255, r + lighten_amount)
                g = min(255, g + lighten_amount)
                b = min(255, b + lighten_amount)
                pixels[x, y] = (r, g, b, a)

    return img


def erode_dark_edges(img, passes=1):
    """Thin dark outlines at content edges only (not interior dark pixels)."""
    img = img.copy()
    pixels = img.load()
    w, h = img.size

    eroded = 0
    for _ in range(passes):
        to_clear = []
        for y in range(h):
            for x in range(w):
                r, g, b, a = pixels[x, y]
                if a == 0:
                    continue
                brightness = (r + g + b) / 3
                if brightness >= 80:
                    continue
                # Only erode if adjacent to a transparent pixel
                has_transparent_neighbor = False
                for nx, ny in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]:
                    if 0 <= nx < w and 0 <= ny < h:
                        if pixels[nx, ny][3] == 0:
                            has_transparent_neighbor = True
                            break
                    else:
                        has_transparent_neighbor = True
                        break
                if has_transparent_neighbor:
                    to_clear.append((x, y))
        for x, y in to_clear:
            r, g, b, _ = pixels[x, y]
            pixels[x, y] = (r, g, b, 0)
            eroded += 1

    print(f"  erode_dark_edges: {eroded} edge pixels eroded ({passes} passes)")
    return img


def crop_to_content(img, padding=4):
    """Crop image to its non-transparent content with some padding."""
    bbox = img.getbbox()
    if bbox is None:
        return img

    left, top, right, bottom = bbox
    left = max(0, left - padding)
    top = max(0, top - padding)
    right = min(img.width, right + padding)
    bottom = min(img.height, bottom + padding)

    return img.crop((left, top, right, bottom))


def resize_to_square(img, size):
    """Resize image to fit inside a square, keeping aspect ratio,
    centered on a transparent background."""
    w, h = img.size

    # Scale to fit inside the target square
    scale = min(size / w, size / h)
    new_w = int(w * scale)
    new_h = int(h * scale)
    resized = img.resize((new_w, new_h), Image.LANCZOS)

    # Center on transparent square
    result = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    offset_x = (size - new_w) // 2
    offset_y = (size - new_h) // 2
    result.paste(resized, (offset_x, offset_y), resized)

    return result


def blend_retro_effect(original_rgba, blend_amount=0.05):
    """Blend the cartoonize_retro effect onto the original at low opacity.
    original_rgba: RGBA image with transparency.
    Returns RGBA image: 90% original + 10% retro effect."""

    # Extract alpha to preserve transparency
    r, g, b, a = original_rgba.split()
    rgb_original = Image.merge("RGB", (r, g, b))

    # Apply the retro effect to the RGB part
    retro_rgb = cartoonize_retro(rgb_original)

    # Blend: result = original * (1 - blend) + retro * blend
    blended_rgb = Image.blend(rgb_original, retro_rgb, blend_amount)

    # Re-attach the original alpha channel
    result = blended_rgb.convert("RGBA")
    result.putalpha(a)
    return result


def create_pedal_frame(img, spread=3):
    """Create frame2 by spreading small circular areas left/right of center up/down."""
    import math
    w, h = img.size
    frame = img.copy()
    pixels = img.load()
    out = frame.load()

    cx, cy = w // 2, h // 2

    for x in range(w):
        for y in range(h):
            dx, dy = x - cx, y - cy
            r = math.sqrt(dx * dx + dy * dy)
            if r < 4 or r > 10:
                continue
            angle = math.degrees(math.atan2(dy, dx)) % 360
            # Right side: 0-20 deg or 340-360 deg
            right = angle <= 20 or angle >= 340
            # Left side: 160-200 deg
            left = 160 <= angle <= 200
            if right:
                # Spread up and down
                for sy in [y - spread, y + spread]:
                    if 0 <= sy < h:
                        out[x, sy] = pixels[x, y]
            elif left:
                for sy in [y - spread, y + spread]:
                    if 0 <= sy < h:
                        out[x, sy] = pixels[x, y]
    return frame


def resize_fit(img, max_size=512):
    """Resize to fit within max_size x max_size, keep aspect ratio."""
    w, h = img.size
    scale = min(max_size / w, max_size / h, 1.0)
    if scale >= 1.0:
        return img
    return img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)


def process_characters():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    src_dir = "characters"
    out_dir = "characters-modified"
    os.makedirs(out_dir, exist_ok=True)

    source_files = [
        "cargocycle-one.png",
        "cargocycle-two.png",
    ]

    for fname in source_files:
        in_path = os.path.join(src_dir, fname)
        if not os.path.isfile(in_path):
            print("File not found:", in_path)
            continue

        base_name = os.path.splitext(fname)[0]
        print(f"Processing {fname}...")

        try:
            img = Image.open(in_path).convert("RGB")

            # Remove background
            img_rgba = remove_gray_background(img, tolerance=40)

            # Save original (bg removed, max 512px)
            img_orig = resize_fit(crop_to_content(img_rgba))
            orig_name = f"{base_name}-original.png"
            img_orig.save(os.path.join(out_dir, orig_name), "PNG")
            print(f"  Saved: {orig_name} ({img_orig.size})")

            # Crop to content for sprite pipeline
            img_cropped = crop_to_content(img_rgba)

            # Reduce dark outlines before resizing
            img_thinned = erode_dark_edges(img_cropped, passes=3)
            img_thinned = soften_dark_pixels(img_thinned,
                                             dark_threshold=60,
                                             lighten_amount=30)
            r, g, b, a = img_thinned.split()
            rgb = Image.merge("RGB", (r, g, b))
            rgb = rgb.filter(ImageFilter.SMOOTH)
            img_thinned = rgb.convert("RGBA")
            img_thinned.putalpha(a)

            img_blended = blend_retro_effect(img_thinned, blend_amount=RETRO_BLEND)
            sprite = resize_to_square(img_blended, SPRITE_SIZE)

            # Create two animation frames
            frame1 = sprite.copy()
            frame2 = create_pedal_frame(sprite)

            # Save both frames
            name1 = f"{base_name}-frame1.png"
            name2 = f"{base_name}-frame2.png"

            frame1.save(os.path.join(out_dir, name1), "PNG")
            frame2.save(os.path.join(out_dir, name2), "PNG")

            print(f"  Saved: {name1} ({frame1.size})")
            print(f"  Saved: {name2} ({frame2.size})")

        except Exception as e:
            print(f"Error processing {fname}: {e}")

    print("Done! Output in:", out_dir)


if __name__ == "__main__":
    process_characters()
