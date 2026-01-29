#!/usr/bin/env python3
# rename.py

import os
import re
import argparse
from collections import defaultdict

PLANT_ITEMS = [
    {"search":"Peikonlehti Monstera deliciosa","fi":"Peikonlehti","en":"Monstera"},
    {"search":"Posliinikukka Hoya","fi":"Posliinikukka","en":"Wax plant (Hoya)"},
    {"search":"Palmuvehka Zamioculcas zamiifolia","fi":"Palmuvehka","en":"ZZ plant"},
    {"search":"Anopinkieli Sansevieria","fi":"Anopinkieli","en":"Snake plant"},
    {"search":"Rahapuu Crassula ovata","fi":"Rahapuu","en":"Jade plant"},
    {"search":"Joulukaktus Schlumbergera","fi":"Joulukaktus","en":"Christmas cactus"},
    {"search":"Tulilatva Kalanchoe blossfeldiana","fi":"Tulilatva","en":"Kalanchoe"},
    {"search":"Viirivehka Spathiphyllum","fi":"Viirivehka","en":"Peace lily"},
    {"search":"Kultaköynnös Epipremnum aureum","fi":"Kultaköynnös","en":"Golden pothos"},
    {"search":"Muorinkukka Pilea","fi":"Muorinkukka","en":"Chinese money plant (Pilea)"},
    {"search":"monstera plant","fi":"Peikonlehti","en":"Monstera"},
    {"search":"hoya plant","fi":"Posliinikukka","en":"Wax plant (Hoya)"},
    {"search":"zz plant","fi":"Palmuvehka","en":"ZZ plant"},
    {"search":"snake plant","fi":"Anopinkieli","en":"Snake plant"},
    {"search":"jade plant","fi":"Rahapuu","en":"Jade plant"},
    {"search":"christmas cactus","fi":"Joulukaktus","en":"Christmas cactus"},
    {"search":"kalanchoe plant","fi":"Tulilatva","en":"Kalanchoe"},
    {"search":"peace lily","fi":"Viirivehka","en":"Peace lily"},
    {"search":"golden pothos","fi":"Kultaköynnös","en":"Golden pothos"},
    {"search":"pilea peperomioides","fi":"Muorinkukka","en":"Chinese money plant (Pilea)"},
    {"search":"fiddle leaf fig","fi":"Viulunlehtiviikuna","en":"Fiddle-leaf fig"},
    {"search":"rubber plant","fi":"Kumiviikuna","en":"Rubber plant"},
    {"search":"areca palm","fi":"Arekapalmu","en":"Areca palm"},
    {"search":"calathea plant","fi":"Kalathea","en":"Calathea"},
    {"search":"philodendron plant","fi":"Köynnösvehka","en":"Philodendron"},
]

def safe_fi_name(s: str) -> str:
    s = s.strip().lower().replace(" ", "-")
    out = []
    prev_dash = False
    for ch in s:
        ok = ch.isalnum() or ch in ("-", "ä", "ö", "å")
        if ok:
            if ch == "-":
                if not prev_dash:
                    out.append("-")
                prev_dash = True
            else:
                out.append(ch)
                prev_dash = False
        else:
            if not prev_dash:
                out.append("-")
            prev_dash = True
    return "".join(out).strip("-")

def parse_old_filename(filename: str):
    if not filename.lower().endswith(".jpg"):
        return None
    stem = filename[:-4]
    parts = stem.split("_")
    if len(parts) < 3:
        return None
    idx_str = parts[0]
    if not idx_str.isdigit():
        return None
    idx = int(idx_str)
    photo_id = parts[-1]
    safe_name = "_".join(parts[1:-1])
    return idx, safe_name, photo_id

def is_new_pattern(filename: str) -> bool:
    return re.fullmatch(r"[a-z0-9äöå-]+-\d{2}\.jpg", filename.lower()) is not None

def build_idx_to_fi_safe():
    m = {}
    for idx, item in enumerate(PLANT_ITEMS, start=1):
        m[idx] = safe_fi_name(item["fi"])
    return m

def unique_target_path(dir_path: str, base_name: str) -> str:
    candidate = os.path.join(dir_path, base_name)
    if not os.path.exists(candidate):
        return candidate
    stem, ext = os.path.splitext(base_name)
    k = 2
    while True:
        alt = os.path.join(dir_path, f"{stem}_{k}{ext}")
        if not os.path.exists(alt):
            return alt
        k += 1

def main():
    ap = argparse.ArgumentParser(description="Rename old Unsplash-downloaded plant images to <fi-name>-NN.jpg")
    ap.add_argument("--dir", default=".", help="Directory containing the images (default: current directory)")
    ap.add_argument("--dry-run", action="store_true", help="Print planned renames without changing anything")
    ap.add_argument("--include-index", action="store_true", help="Prefix with plant index: 01_fi-name-NN.jpg")
    args = ap.parse_args()

    dir_path = os.path.abspath(args.dir)
    if not os.path.isdir(dir_path):
        raise SystemExit(f"Not a directory: {dir_path}")

    idx_to_fi = build_idx_to_fi_safe()

    files = [f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))]
    files.sort(key=lambda s: s.lower())

    groups = defaultdict(list)
    skipped = []
    unknown = []

    for f in files:
        if f.lower().endswith(".jpg") and is_new_pattern(f):
            skipped.append((f, "already new pattern"))
            continue
        parsed = parse_old_filename(f)
        if not parsed:
            continue
        idx, safe_name, photo_id = parsed
        if idx not in idx_to_fi:
            unknown.append((f, f"idx {idx} not in PLANT_ITEMS"))
            continue
        groups[idx].append(f)

    planned = []
    for idx in sorted(groups.keys()):
        fi_safe = idx_to_fi[idx]
        counter = 1
        for old_name in groups[idx]:
            nn = f"{counter:02d}"
            if args.include_index:
                new_base = f"{idx:02d}_{fi_safe}-{nn}.jpg"
            else:
                new_base = f"{fi_safe}-{nn}.jpg"
            new_path = unique_target_path(dir_path, new_base)
            planned.append((old_name, os.path.basename(new_path)))
            counter += 1

    if not planned and not unknown:
        print("No matching old-pattern files found.")
        return

    for old_name, new_name in planned:
        print(f"{old_name} -> {new_name}")

    if unknown:
        print("\nUnmapped (idx not found):")
        for f, reason in unknown:
            print(f"  {f}  ({reason})")

    if skipped:
        print("\nSkipped:")
        for f, reason in skipped:
            print(f"  {f}  ({reason})")

    if args.dry_run:
        print("\nDry-run: no files renamed.")
        return

    for old_name, new_name in planned:
        src = os.path.join(dir_path, old_name)
        dst = os.path.join(dir_path, new_name)
        os.rename(src, dst)

    print(f"\nRenamed {len(planned)} file(s).")

if __name__ == "__main__":
    main()
