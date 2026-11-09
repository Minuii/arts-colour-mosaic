"""
Art Institute of Chicago colour scraper (public-domain paintings only).

Uses the open AIC API (https://api.artic.edu/docs/). Every artwork it keeps is
marked public domain by the museum, and its images are released under CC0.
Paintings are sorted into the same 12 colour groups as scraper.py, using the
dominant colour the API reports for each artwork.

Output (same CSV layout as scraper.py):
    datasets_pd/<COLOR>/images/*.jpg
    datasets_pd/<COLOR>/metadata.csv
    datasets_pd/all_colors.csv

Usage:
    python scraper_aic.py                 # every public-domain painting with an image
    python scraper_aic.py --limit 200     # quick test
"""
import argparse, colorsys, io, json, os, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
from scraper import COLOR_VALUES, COLOR_HEX, rgb, write_csv

API = "https://api.artic.edu/api/v1/artworks/search"
IIIF = "https://www.artic.edu/iiif/2"
# AIC asks API clients to identify themselves; its image server rejects Python's default agent.
HEADERS = {"AIC-User-Agent": "arts-colour-mosaic", "User-Agent": "arts-colour-mosaic/1.0",
           "Content-Type": "application/json"}
QUERY = {"bool": {"filter": [
    {"term": {"is_public_domain": True}},
    {"term": {"artwork_type_id": 1}},          # 1 = Painting
    {"exists": {"field": "image_id"}},
    {"exists": {"field": "color"}},
]}}
FIELDS = ["id", "title", "artist_title", "image_id", "color", "thumbnail", "date_display"]


def post(body, retries=4):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(API, json.dumps(body).encode(), HEADERS)
            return json.load(urllib.request.urlopen(req, timeout=30))
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(5 * (attempt + 1))


def colour_group(h, s, l):
    """Map the API's dominant HSL colour (h 0-360, s/l 0-100) to one of the 12 groups."""
    if l < 15:
        return "BLACK"
    if s < 12:
        return "WHITE" if l > 80 else "GRAY"
    if 15 <= h < 50 and l < 40:
        return "BROWN"
    if h < 15 or h >= 345:
        return "PINK" if l > 70 else "RED"
    for limit, name in ((50, "ORANGE"), (70, "YELLOW"), (165, "GREEN"), (195, "TEAL"),
                        (255, "BLUE"), (290, "PURPLE"), (345, "PINK")):
        if h < limit:
            return name


def hsl_hex(h, s, l):
    r, g, b = colorsys.hls_to_rgb(h / 360, l / 100, s / 100)
    return "#%02x%02x%02x" % (round(r * 255), round(g * 255), round(b * 255))


def fetch_all(limit):
    """Page by id (the search API refuses to go past its first 1,000 results)."""
    items, last_id = [], 0
    while True:
        q = json.loads(json.dumps(QUERY))
        q["bool"]["filter"].append({"range": {"id": {"gt": last_id}}})
        d = post({"query": q, "fields": FIELDS, "limit": 100, "sort": [{"id": "asc"}]})
        if not d["data"]:
            break
        items += d["data"]
        last_id = d["data"][-1]["id"]
        print(f"  {len(items)} paintings so far")
        if limit and len(items) >= limit:
            break
        time.sleep(0.5)
    return items[:limit] if limit else items


def to_row(it):
    c, th = it["color"], it.get("thumbnail") or {}
    label = colour_group(c["h"], c["s"], c["l"])
    dom = hsl_hex(c["h"], c["s"], c["l"])
    cr, cg, cb = rgb(COLOR_HEX[label])
    dr, dg, db = rgb(dom)
    w, h = th.get("width"), th.get("height")
    return {
        "filename": f"{it['id']}.jpg",
        "asset_id": it["id"],
        "title": it.get("title") or "Untitled",
        "artist": it.get("artist_title") or "Unknown",
        "museum": "Art Institute of Chicago",
        "asset_path": f"https://www.artic.edu/artworks/{it['id']}",
        "thumbnail_url": f"{IIIF}/{it['image_id']}/full/200,/0/default.jpg",
        "dominant_hex": dom, "dom_r": dr, "dom_g": dg, "dom_b": db,
        "aspect_ratio": round(w / h, 6) if w and h else "",
        "color_label": label, "color_hex": COLOR_HEX[label],
        "color_r": cr, "color_g": cg, "color_b": cb,
        "color_value": COLOR_VALUES[label],
    }


def download(args):
    """Fetch one image and save it as a centre-cropped square, like the Google tiles."""
    url, path, size = args
    if os.path.exists(path):
        return True
    for attempt in range(3):
        try:
            data = urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=30).read()
            im = Image.open(io.BytesIO(data)).convert("RGB")
            side = min(im.size)
            left, top = (im.width - side) // 2, (im.height - side) // 2
            im.crop((left, top, left + side, top + side)).resize((size, size), Image.LANCZOS).save(path, quality=90)
            return True
        except Exception:
            time.sleep(2 + attempt * 3)
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None, help="max paintings in total")
    ap.add_argument("--size", type=int, default=128, help="square tile px")
    ap.add_argument("--out", default="datasets_pd")
    ap.add_argument("--threads", type=int, default=4)
    a = ap.parse_args()

    print("Querying AIC for public-domain paintings ...")
    rows = [to_row(it) for it in fetch_all(a.limit)]
    by_colour = {c: [r for r in rows if r["color_label"] == c] for c in COLOR_VALUES}

    merged = []
    for name, group in by_colour.items():
        folder = os.path.join(a.out, name)
        os.makedirs(os.path.join(folder, "images"), exist_ok=True)
        jobs = [(r["thumbnail_url"], os.path.join(folder, "images", r["filename"]), a.size) for r in group]
        with ThreadPoolExecutor(a.threads) as ex:
            ok = list(ex.map(download, jobs))
        group = [r for r, good in zip(group, ok) if good]
        write_csv(os.path.join(folder, "metadata.csv"), group)
        merged += group
        print(f"== {name} (value={COLOR_VALUES[name]}): {len(group)} paintings")
    write_csv(os.path.join(a.out, "all_colors.csv"), merged)
    print(f"Done. {len(merged)} rows -> {a.out}/all_colors.csv")


if __name__ == "__main__":
    main()
