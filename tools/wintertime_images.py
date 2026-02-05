#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "ddgs",
#     "httpx",
#     "pillow",
# ]
# ///
"""
Download winter clothing images for kids dressing app.
Uses DuckDuckGo image search to find suitable images.

Usage:
    uv run tools/wintertime_images.py

Images will be saved to docs/wintertime/images/
"""

import asyncio
from pathlib import Path

import httpx
from ddgs import DDGS
from PIL import Image


# Clothing items to search for - tailored for 4-year-old Finnish girl
CLOTHING_ITEMS = [
    {
        "id": "01_long_sleeve_shirt",
        "query": "4 year old girl long sleeve shirt kids clothing product photo",
        "finnish": "pitkähihainen paita",
    },
    {
        "id": "02_indoor_pants",
        "query": "4 year old girl indoor pants leggings kids clothing product photo",
        "finnish": "sisähousut",
    },
    {
        "id": "03_socks",
        "query": "kids socks for 4 year old girl colorful children socks product",
        "finnish": "sukat",
    },
    {
        "id": "04a_wool_overalls",
        "query": "kids wool overalls 4 year old girl merino wool jumpsuit product",
        "finnish": "villahaalari",
    },
    {
        "id": "04b_wool_pants",
        "query": "kids wool pants 4 year old girl merino wool trousers product",
        "finnish": "villahousut",
    },
    {
        "id": "04c_wool_sweater",
        "query": "kids wool sweater 4 year old girl merino wool jumper product",
        "finnish": "villapaita",
    },
    {
        "id": "05a_winter_overalls",
        "query": "kids winter overalls snowsuit 4 year old girl Finnish winter clothing",
        "finnish": "talvihaalari",
    },
    {
        "id": "05b_winter_pants",
        "query": "children snow pants ski pants toddler girl winter trousers product",
        "finnish": "talvihousut",
    },
    {
        "id": "05c_winter_jacket",
        "query": "kids winter jacket 4 year old girl warm parka Finnish winter",
        "finnish": "talvitakki",
    },
    {
        "id": "06_neck_scarf",
        "query": "kids neck warmer scarf kauluri 4 year old girl fleece tube scarf",
        "finnish": "kauluri",
    },
    {
        "id": "07_skiing_cap",
        "query": "kids winter beanie hat 4 year old girl skiing cap warm",
        "finnish": "pipo",
    },
    {
        "id": "08_woollen_socks",
        "query": "kids wool socks thick 4 year old girl warm winter socks",
        "finnish": "villasukat",
    },
    {
        "id": "09_winter_boots",
        "query": "kids winter boots 4 year old girl snow boots warm Finnish",
        "finnish": "talvisaappaat",
    },
    {
        "id": "10_inner_wool_mittens",
        "query": "kids wool mittens liner gloves 4 year old girl inner mittens",
        "finnish": "sisälapaset",
    },
    {
        "id": "11_outer_gloves",
        "query": "kids winter gloves waterproof 4 year old girl outer mittens leather",
        "finnish": "ulkolapaset",
    },
]

# Output directory
OUTPUT_DIR = Path("wintertime-images")
IMAGES_PER_ITEM = 3


def search_images(query: str, max_results: int = 5) -> list[dict]:
    """Search for images using DuckDuckGo."""
    print(f"  Searching: {query}")
    try:
        with DDGS() as ddgs:
            results = list(ddgs.images(
                query,
                region="fi-fi",  # Finnish region
                safesearch="on",
                size="Medium",
                type_image="photo",
                max_results=max_results,
            ))
        return results
    except Exception as e:
        print(f"  Search error: {e}")
        return []


async def download_image(client: httpx.AsyncClient, url: str, filepath: Path) -> bool:
    """Download an image from URL and save it."""
    try:
        response = await client.get(url, timeout=15.0, follow_redirects=True)
        response.raise_for_status()
        
        content_type = response.headers.get("content-type", "")
        if "image" not in content_type:
            return False
        
        # Save temporarily
        temp_path = filepath.with_suffix(".tmp")
        temp_path.write_bytes(response.content)
        
        # Validate and convert to JPEG
        try:
            with Image.open(temp_path) as img:
                # Convert to RGB if needed (for PNG with transparency, etc.)
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                
                # Resize if too large (max 800px width for mobile)
                if img.width > 800:
                    ratio = 800 / img.width
                    new_size = (800, int(img.height * ratio))
                    img = img.resize(new_size, Image.Resampling.LANCZOS)
                
                # Save as JPEG
                img.save(filepath, "JPEG", quality=85, optimize=True)
            
            temp_path.unlink()
            return True
        except Exception as e:
            temp_path.unlink(missing_ok=True)
            print(f"    Image processing error: {e}")
            return False
            
    except Exception as e:
        print(f"    Download error: {e}")
        return False


async def download_images_for_item(item: dict) -> list[Path]:
    """Download images for a single clothing item."""
    print(f"\n📦 {item['id']} ({item['finnish']})")
    
    # Search for images
    results = search_images(item["query"], max_results=IMAGES_PER_ITEM * 2)
    
    if not results:
        print("  No results found")
        return []
    
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    downloaded = []
    async with httpx.AsyncClient() as client:
        for i, result in enumerate(results):
            if len(downloaded) >= IMAGES_PER_ITEM:
                break
                
            url = result.get("image")
            if not url:
                continue
            
            # Simple filename: id_index.jpg (e.g., 01_long_sleeve_shirt_1.jpg)
            filepath = OUTPUT_DIR / f"{item['id']}_{len(downloaded)+1}.jpg"
            
            if filepath.exists():
                print(f"  ✓ Already exists: {filepath.name}")
                downloaded.append(filepath)
                continue
            
            print(f"  ↓ Downloading: {url[:60]}...")
            if await download_image(client, url, filepath):
                print(f"  ✓ Saved: {filepath.name}")
                downloaded.append(filepath)
            
            # Small delay to be polite
            await asyncio.sleep(0.5)
    
    return downloaded


async def main():
    """Main entry point."""
    print("=" * 60)
    print("Winter Clothing Image Downloader")
    print("For 4-year-old Finnish girl dressing app")
    print("=" * 60)
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    all_downloaded = []
    for item in CLOTHING_ITEMS:
        downloaded = await download_images_for_item(item)
        all_downloaded.extend(downloaded)
    
    print("\n" + "=" * 60)
    print(f"✅ Downloaded {len(all_downloaded)} images total")
    print(f"📁 Saved to: {OUTPUT_DIR}")
    print("=" * 60)
    
    # Create an index file
    index_path = OUTPUT_DIR / "index.json"
    import json
    index_data = {
        "items": [
            {
                "id": item["id"],
                "finnish": item["finnish"],
                "query": item["query"],
            }
            for item in CLOTHING_ITEMS
        ]
    }
    index_path.write_text(json.dumps(index_data, indent=2, ensure_ascii=False))
    print(f"📄 Created index: {index_path}")


if __name__ == "__main__":
    asyncio.run(main())
