import os
import sys
import time
import json
import urllib.parse
import urllib.request

# load API key from config.yaml
import yaml

API_KEY = None

with open("config.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)
    API_KEY = config.get("API_KEY", None)

if not API_KEY:
    print("API_KEY not found in config.yaml")
    sys.exit(1)

PLANT_ITEMS  = [
#   {"search":"Peikonlehti Monstera deliciosa","fi":"Peikonlehti","en":"Monstera"},
#   {"search":"Posliinikukka Hoya","fi":"Posliinikukka","en":"Wax plant (Hoya)"},
#   {"search":"Palmuvehka Zamioculcas zamiifolia","fi":"Palmuvehka","en":"ZZ plant"},
#   {"search":"Anopinkieli Sansevieria","fi":"Anopinkieli","en":"Snake plant"},
#   {"search":"Rahapuu Crassula ovata","fi":"Rahapuu","en":"Jade plant"},
#   {"search":"Joulukaktus Schlumbergera","fi":"Joulukaktus","en":"Christmas cactus"},
#   {"search":"Tulilatva Kalanchoe blossfeldiana","fi":"Tulilatva","en":"Kalanchoe"},
#   {"search":"Viirivehka Spathiphyllum","fi":"Viirivehka","en":"Peace lily"},
#   {"search":"Kultaköynnös Epipremnum aureum","fi":"Kultaköynnös","en":"Golden pothos"},
#   {"search":"Muorinkukka Pilea","fi":"Muorinkukka","en":"Chinese money plant (Pilea)"},
#   {"search":"monstera plant","fi":"Peikonlehti","en":"Monstera"},
#   {"search":"hoya plant","fi":"Posliinikukka","en":"Wax plant (Hoya)"},
#   {"search":"zz plant","fi":"Palmuvehka","en":"ZZ plant"},
#   {"search":"snake plant","fi":"Anopinkieli","en":"Snake plant"},
#   {"search":"jade plant","fi":"Rahapuu","en":"Jade plant"},
#   {"search":"christmas cactus","fi":"Joulukaktus","en":"Christmas cactus"},
#   {"search":"kalanchoe plant","fi":"Tulilatva","en":"Kalanchoe"},
#   {"search":"peace lily","fi":"Viirivehka","en":"Peace lily"},
#  {"search":"golden pothos","fi":"Kultaköynnös","en":"Golden pothos"},
#  {"search":"pilea peperomioides","fi":"Muorinkukka","en":"Chinese money plant (Pilea)"},
#  {"search":"fiddle leaf fig","fi":"Viulunlehtiviikuna","en":"Fiddle-leaf fig"},
#  {"search":"rubber plant","fi":"Kumiviikuna","en":"Rubber plant"},
#  {"search":"areca palm","fi":"Arekapalmu","en":"Areca palm"},
#  {"search":"calathea plant","fi":"Kalathea","en":"Calathea"},
#  {"search":"philodendron plant","fi":"Köynnösvehka","en":"Philodendron"},
#  {"search":"Spiderwort plant","fi":"Juoru","en":"Spiderwort"},
  {"search":"Dwarf Umbrella Tree","fi":"Siroliuska-aralia","en":"Dwarf Umbrella Tree"}
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

PER_PLANT = 5
OUT_DIR = "downloads"
SEARCH_PER_PAGE = PER_PLANT

if API_KEY == "YOUR_UNSPLASH_ACCESS_KEY_HERE":
    print("Set your API_KEY in the script before running.")
    sys.exit(1)

os.makedirs(OUT_DIR, exist_ok=True)

def request_json(url, headers=None, timeout=30):
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.load(resp)

def download_bytes(url, headers=None, timeout=60):
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()

auth_header = {"Authorization": f"Client-ID {API_KEY}"}

downloaded = []
errors = []

for idx, item in enumerate(PLANT_ITEMS, start=1):
    plant_search = item["search"]
    fi_name = item["fi"]

    q = urllib.parse.quote(f"{plant_search} illustration")
    search_url = f"https://api.unsplash.com/search/photos?query={q}&per_page={SEARCH_PER_PAGE}"

    try:
        results = request_json(search_url, headers=auth_header)
    except Exception as e:
        errors.append((plant_search, f"search error: {e}"))
        time.sleep(1)
        continue

    photos = results.get("results") or []
    if not photos:
        errors.append((plant_search, "no results"))
        time.sleep(1)
        continue

    fi_safe = safe_fi_name(fi_name)

    for i, photo in enumerate(photos[:PER_PLANT], start=1):
        download_loc = photo.get("links", {}).get("download_location")
        image_url = photo.get("urls", {}).get("full") or photo.get("urls", {}).get("raw")
        if not download_loc or not image_url:
            errors.append((plant_search, photo.get("id"), "missing download_location or image url"))
            continue

        try:
            request_json(download_loc, headers=auth_header)
        except Exception as e:
            errors.append((plant_search, photo.get("id"), f"trigger download error: {e}"))
            time.sleep(1)
            continue

        try:
            img_bytes = download_bytes(image_url, headers=auth_header)
        except Exception as e:
            errors.append((plant_search, photo.get("id"), f"image download error: {e}"))
            time.sleep(1)
            continue

        fname = f"{fi_safe}-{i:02d}.jpg"
        path = os.path.join(OUT_DIR, fname)
        try:
            with open(path, "wb") as f:
                f.write(img_bytes)
            downloaded.append(path)
        except Exception as e:
            errors.append((plant_search, photo.get("id"), f"file write error: {e}"))

        time.sleep(1)

print("Downloaded:", len(downloaded), "files")
for p in downloaded:
    print(" ", p)
if errors:
    print("\nErrors:")
    for e in errors[:20]:
        print(" ", e)
