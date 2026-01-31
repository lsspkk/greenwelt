import argparse
import json
import os
import re
import time
import zipfile
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from PIL import Image

BASE = "https://opengameart.org"

# CC0-focused starting points (collections/categories tend to change; you can add more with --start)
DEFAULT_START_URLS = [
    f"{BASE}/content/cc0-portraits",
    f"{BASE}/content/cc0-character-portraits",
]

UA = "Mozilla/5.0 (compatible; CC0AvatarScraper/1.0; +https://opengameart.org/)"

# raster only (we can measure/resize)
IMG_EXTS = {".png", ".jpg", ".jpeg", ".webp"}
ZIP_EXTS = {".zip"}


def slugify(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return re.sub(r"-+", "-", s).strip("-") or "item"


def norm_url(href: str) -> str:
    return urljoin(BASE, href)


def ext_of(url: str) -> str:
    return Path(urlparse(url).path.lower()).suffix


def request_html(session: requests.Session, url: str, timeout=30) -> str:
    r = session.get(url, timeout=timeout)
    r.raise_for_status()
    return r.text


def is_asset_link(href: str) -> bool:
    if not href:
        return False
    return href.startswith("/content/") and not href.startswith("/content/cc0-")


def is_next_link(a_tag) -> bool:
    txt = (a_tag.get_text() or "").strip().lower()
    href = a_tag.get("href") or ""
    return ("next" in txt or "›" in txt) and bool(href)


def collect_asset_pages(session: requests.Session, start_urls, max_pages=80, sleep=0.6):
    seen_pages = set()
    seen_assets = set()

    for start in start_urls:
        page_url = start
        pages = 0

        while page_url and page_url not in seen_pages and pages < max_pages:
            seen_pages.add(page_url)
            pages += 1

            soup = BeautifulSoup(request_html(
                session, page_url), "html.parser")

            for a in soup.select("a[href]"):
                href = a.get("href")
                if is_asset_link(href):
                    seen_assets.add(norm_url(href))

            next_url = None
            for a in soup.select("a[href]"):
                if is_next_link(a):
                    next_url = norm_url(a.get("href"))
                    break

            page_url = next_url
            time.sleep(sleep)

    return sorted(seen_assets)


def parse_asset_page(session: requests.Session, asset_url: str):
    soup = BeautifulSoup(request_html(session, asset_url), "html.parser")

    title = soup.select_one("h2") or soup.select_one("h1")
    title_text = title.get_text(strip=True) if title else asset_url

    licenses = []
    lic_block = soup.find(string=re.compile(r"License\(s\):", re.I))
    if lic_block:
        parent = lic_block.parent
        for a in parent.find_all("a", href=True):
            t = a.get_text(strip=True)
            if t:
                licenses.append(t)

    tags = []
    tags_block = soup.find(string=re.compile(r"Tags:", re.I))
    if tags_block:
        parent = tags_block.parent
        for a in parent.find_all("a", href=True):
            t = a.get_text(strip=True)
            if t:
                tags.append(t)

    file_urls = []
    file_header = soup.find(string=re.compile(r"File\(s\):", re.I))
    if file_header:
        parent = file_header.parent
        container = parent
        for _ in range(6):
            if container and container.find_all("a", href=True):
                break
            container = container.parent

        for a in container.find_all("a", href=True):
            href = a.get("href")
            if not href:
                continue
            u = norm_url(href) if href.startswith("/") else href
            e = ext_of(u)
            if e in IMG_EXTS or e in ZIP_EXTS:
                file_urls.append(u)

    return {
        "url": asset_url,
        "title": title_text,
        "licenses": sorted(set(licenses)),
        "tags": sorted(set(tags)),
        "files": sorted(set(file_urls)),
    }


def is_cc0_only(meta) -> bool:
    if not meta.get("licenses"):
        return False
    lic = " ".join(meta["licenses"]).lower()
    # accept common CC0 label variants
    return ("cc0" in lic or "cc-0" in lic or "cc 0" in lic) and ("by" not in lic)


def download_file(session: requests.Session, url: str, out_path: Path):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with session.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 256):
                if chunk:
                    f.write(chunk)


def extract_zip(zip_path: Path, out_dir: Path):
    extracted = []
    out_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as z:
        for info in z.infolist():
            if info.is_dir():
                continue
            suffix = Path(info.filename).suffix.lower()
            if suffix in IMG_EXTS:
                target = out_dir / Path(info.filename).name
                with z.open(info) as src, open(target, "wb") as dst:
                    dst.write(src.read())
                extracted.append(target)
    return extracted


def portrait_min_size_and_resize(file_path: Path, min_side: int, target_height: int) -> bool:
    """
    Returns True if kept (possibly resized), False if removed.
    Rules:
      - must be raster image (handled by caller)
      - must be portrait: height >= width
      - must have max(width,height) >= min_side
      - if kept, resize to target_height (height), keeping aspect ratio
    """
    try:
        with Image.open(file_path) as im:
            im.load()
            w, h = im.size

            if h < w:
                return False  # not portrait

            if max(w, h) < min_side:
                return False  # too small

            if h != target_height:
                new_w = max(1, int(round(w * (target_height / float(h)))))
                im2 = im.resize((new_w, target_height),
                                Image.Resampling.LANCZOS)

                # preserve format, but normalize JPEG alpha issues
                fmt = (im.format or "").upper()
                suffix = file_path.suffix.lower()

                if fmt in {"JPEG", "JPG"} or suffix in {".jpg", ".jpeg"}:
                    if im2.mode in ("RGBA", "LA"):
                        im2 = im2.convert("RGB")
                    im2.save(file_path, format="JPEG",
                             quality=95, optimize=True)
                else:
                    im2.save(file_path)

            return True
    except Exception:
        return False


def postprocess_images(root_dir: Path, min_side: int, target_height: int, delete_nonmatching: bool = True):
    kept = 0
    removed = 0

    for p in root_dir.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix.lower() not in IMG_EXTS:
            continue

        ok = portrait_min_size_and_resize(
            p, min_side=min_side, target_height=target_height)
        if ok:
            kept += 1
        else:
            removed += 1
            if delete_nonmatching:
                try:
                    p.unlink()
                except Exception:
                    pass

    # clean empty dirs
    for d in sorted([x for x in root_dir.rglob("*") if x.is_dir()], reverse=True):
        try:
            if not any(d.iterdir()):
                d.rmdir()
        except Exception:
            pass

    return kept, removed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="avatars_out")
    ap.add_argument("--start", action="append", help="Start URL (repeatable)")
    ap.add_argument("--sleep", type=float, default=0.6)
    ap.add_argument("--max-pages", type=int, default=80)
    ap.add_argument("--keep-zips", action="store_true")
    ap.add_argument("--min-side", type=int, default=150,
                    help="Min required max(width,height)")
    ap.add_argument("--target-height", type=int, default=300,
                    help="Resize kept images to this height")
    args = ap.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    start_urls = args.start or DEFAULT_START_URLS

    session = requests.Session()
    session.headers.update({"User-Agent": UA})

    asset_pages = collect_asset_pages(
        session,
        start_urls=start_urls,
        max_pages=args.max_pages,
        sleep=args.sleep,
    )

    meta_out = out_dir / "metadata.jsonl"
    downloads_out = out_dir / "downloads.jsonl"

    with open(meta_out, "w", encoding="utf-8") as mf, open(downloads_out, "w", encoding="utf-8") as df:
        for asset_url in asset_pages:
            meta = parse_asset_page(session, asset_url)
            mf.write(json.dumps(meta, ensure_ascii=False) + "\n")

            # CC0-only filter (skip anything not clearly CC0)
            if not is_cc0_only(meta):
                continue

            safe_title = slugify(meta["title"])
            asset_dir = out_dir / safe_title
            asset_dir.mkdir(parents=True, exist_ok=True)

            for f_url in meta["files"]:
                e = ext_of(f_url)
                fname = Path(urlparse(f_url).path).name
                target = asset_dir / fname

                try:
                    download_file(session, f_url, target)
                except Exception as ex:
                    df.write(json.dumps({"asset": asset_url, "file": f_url, "error": str(
                        ex)}, ensure_ascii=False) + "\n")
                    continue

                record = {"asset": asset_url,
                          "file": f_url, "saved_as": str(target)}

                if e in ZIP_EXTS:
                    extracted_dir = asset_dir / "extracted"
                    extracted = extract_zip(target, extracted_dir)
                    record["extracted"] = [str(p) for p in extracted]
                    if not args.keep_zips:
                        try:
                            target.unlink()
                        except Exception:
                            pass

                df.write(json.dumps(record, ensure_ascii=False) + "\n")

                time.sleep(args.sleep)

    # Post-process: remove non-portrait and too-small images, resize kept ones to target height
    kept, removed = postprocess_images(
        out_dir, min_side=args.min_side, target_height=args.target_height)

    print(f"Done.")
    print(f"Kept images: {kept}")
    print(f"Removed images (too small / not portrait / unreadable): {removed}")
    print(f"Metadata: {meta_out}")
    print(f"Downloads log: {downloads_out}")


if __name__ == "__main__":
    main()
