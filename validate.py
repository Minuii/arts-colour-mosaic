"""Validate (and with --fix, normalise) every <dataset>/<COLOR>/metadata.csv + all_colors.csv.
Usage: python validate.py [--fix] [datasets_pd | datasets]   (default: datasets_pd, the Chicago set)"""
import csv, os, sys, collections
from PIL import Image
from scraper import COLOR_VALUES, COLOR_HEX as HEX, FIELDS, rgb, write_csv

FIX = "--fix" in sys.argv
ROOT = next((a for a in sys.argv[1:] if not a.startswith("-")), "datasets_pd")
problems = collections.Counter()
seen_global = collections.defaultdict(set)
merged = []

def bad(kind, c, r):
    problems[kind] += 1
    if problems[kind] <= 3:
        print(f"  [{kind}] {c} {r.get('asset_id')}")

for c, v in COLOR_VALUES.items():
    p = os.path.join(ROOT, c, "metadata.csv")
    if not os.path.exists(p):
        print(f"{c}: no metadata (pending)"); continue
    with open(p, newline="", encoding="utf-8") as f:
        rd = csv.DictReader(f)
        if rd.fieldnames != FIELDS:
            problems["header"] += 1
        rows = list(rd)
    ids = set()
    for r in rows:
        for k in ("title", "artist", "museum"):
            n = " ".join((r[k] or "").split())          # strip newlines/double spaces
            if n != r[k]: bad("whitespace", c, r)
            r[k] = n
        if not r["title"]: bad("empty_title", c, r); r["title"] = "Untitled"
        if r["artist"] in ("", "unknown", "Unknown"):
            if r["artist"] == "": bad("empty_artist", c, r)
            r["artist"] = "Unknown"
        if not r["museum"]: bad("empty_museum", c, r); r["museum"] = "Unknown"
        if "\ufffd" in r["title"] + r["artist"] + r["museum"]: bad("mojibake", c, r)
        if r["filename"] != f"{r['asset_id']}.jpg".replace("/", "_"): bad("filename", c, r)
        if r["color_label"] != c or int(r["color_value"]) != v: bad("label/value", c, r)
        if r["color_hex"].upper() != HEX[c] or (int(r["color_r"]), int(r["color_g"]), int(r["color_b"])) != rgb(HEX[c]): bad("color_hex/rgb", c, r)
        if (int(r["dom_r"] or -1), int(r["dom_g"] or -1), int(r["dom_b"] or -1)) != rgb(r["dominant_hex"]): bad("dominant_rgb", c, r)
        if ROOT == "datasets" and not r["thumbnail_url"].endswith("=w128-h128-c"): bad("thumb_url", c, r)
        if r["asset_id"] in ids: bad("dup_in_colour", c, r)
        ids.add(r["asset_id"]); seen_global[r["asset_id"]].add(c)
        img = os.path.join(ROOT, c, "images", r["filename"])
        try:
            with Image.open(img) as im:
                im.verify()
            if Image.open(img).size != (128, 128): bad("img_size", c, r)
        except Exception:
            bad("img_missing/corrupt", c, r)
    extra = set(os.listdir(os.path.join(ROOT, c, "images"))) - {r["filename"] for r in rows}
    if extra: problems["extra_images"] += len(extra)
    print(f"{c}: {len(rows)} rows ok-checked")
    if FIX: write_csv(p, rows)
    merged += rows

cross = {k: v for k, v in seen_global.items() if len(v) > 1}
print("cross-colour duplicates:", len(cross))
print("PROBLEMS:", dict(problems) or "none")
if FIX: write_csv(os.path.join(ROOT, "all_colors.csv"), merged); print("rewrote all_colors.csv:", len(merged))
