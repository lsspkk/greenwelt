import os
import json
from PIL import Image, ImageFilter, ImageOps, ImageDraw

PALETTE_COLORS = [
    (0, 0, 0),
    (29, 43, 83),
    (126, 37, 83),
    (0, 135, 81),
    (171, 82, 54),
    (255, 119, 168),
    (255, 204, 102),
    (255, 255, 255)
]


PALETTE_COLORS_SOFTER_2 = [
    (0, 0, 0),
    (50, 50, 50),
    (90, 120, 90),
    (120, 140, 120),
    (160, 160, 160),
    (200, 200, 200),
    (235, 235, 235),
    (255, 255, 255)
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
    small = img.resize((max(1, w//pixel_size), max(1, h//pixel_size)), Image.NEAREST)
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

def cartoonize_retro(img, poster_bits=3, palette_colors=PALETTE_COLORS_SOFTER_2, pixel_size=4, edge_threshold=45, edge_thick=2, scan_spacing=3, scan_opacity=36):
    color = ImageOps.posterize(img, bits=poster_bits)
    color = color.filter(ImageFilter.SMOOTH_MORE)
    pal_img = make_palette_image(palette_colors)

    # pilkut pois
    #quant = color.quantize(palette=pal_img, dither=Image.NONE).convert("RGB")

    # blurria niin vähemmän pilkkuja
    color = color.filter(ImageFilter.GaussianBlur(0.6))
    quant = color.quantize(palette=pal_img, dither=Image.FLOYDSTEINBERG).convert("RGB")

    quant = quant.filter(ImageFilter.MedianFilter(3))

    quant = pixelate(quant, pixel_size)
    gray = img.convert("L").filter(ImageFilter.FIND_EDGES)
    edge = gray.point(lambda x: 255 if x > edge_threshold else 0, "L")
    edge = amplify_edges(edge, passes=edge_thick)
    edge_mask = edge.point(lambda x: 255 - x)
    final = quant.convert("RGBA")
    black_layer = Image.new("RGBA", final.size, (0, 0, 0, 255))
    final.paste(black_layer, mask=edge)
    final = final.convert("RGB")
    final = add_scanlines(final, spacing=scan_spacing, opacity=scan_opacity)
    return final

def process_images():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    with open('selected.json', 'r', encoding='utf-8') as f:
        files = json.load(f)
    src_dir = 'downloads'
    out_dir = 'modified'
    os.makedirs(out_dir, exist_ok=True)
    for fname in files:
        in_path = os.path.join(src_dir, fname)
        if not os.path.isfile(in_path):
            print("File not found:", in_path)
            continue
        try:
            img = Image.open(in_path).convert('RGB')
            w, h = img.size
            if h > 300:
                new_h = 300
                new_w = int(w * (300 / h))
                img = img.resize((new_w, new_h), Image.LANCZOS)
            out = cartoonize_retro(
                img,
                poster_bits=6,
                palette_colors=PALETTE_COLORS,
                pixel_size=4,
                edge_threshold=125,
                edge_thick=1,
                scan_spacing=3,
                scan_opacity=36
            )
            out_name = os.path.splitext(fname)[0] + '.png'
            out_path = os.path.join(out_dir, out_name)
            out.save(out_path, 'PNG')
            print("Saved:", out_path)
        except Exception as e:
            print("Error processing", fname, e)

if __name__ == '__main__':
    process_images()
