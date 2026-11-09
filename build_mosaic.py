"""Pack dataset tiles into an embedded JPEG atlas + average RGB for the mosaic page.

Each source gets its own file, and mosaic/index.html lets you pick between them:
    datasets_pd -> mosaic/atlas_chicago.js  (Art Institute of Chicago, CC0 public-domain paintings; default)
    datasets    -> mosaic/atlas_google.js   (Google Arts & Culture; some images are still under copyright)

Usage:
    python build_mosaic.py                    # Chicago
    python build_mosaic.py --source datasets  # Google Arts
"""
import argparse, base64, csv, io, json, os
from PIL import Image

NAMES = {"datasets_pd": "chicago", "datasets": "google"}

ap = argparse.ArgumentParser()
ap.add_argument("--source", default="datasets_pd", choices=NAMES, help="dataset folder to pack")
ap.add_argument("--tile-size", type=int, default=48, help="pixel size of each tile in the atlas")
ap.add_argument("--cols", type=int, default=60, help="columns in the atlas sprite sheet")
args = ap.parse_args()

T, COLS, name = args.tile_size, args.cols, NAMES[args.source]
with open(os.path.join(args.source, "all_colors.csv"), newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))
rows = [r for r in rows if os.path.exists(os.path.join(args.source, r["color_label"], "images", r["filename"]))]

atlas = Image.new("RGB", (COLS * T, -(-len(rows) // COLS) * T))
tiles = []
for i, r in enumerate(rows):
    im = Image.open(os.path.join(args.source, r["color_label"], "images", r["filename"])).convert("RGB")
    im = im.resize((T, T), Image.LANCZOS)
    atlas.paste(im, ((i % COLS) * T, (i // COLS) * T))
    tiles.append([*im.resize((1, 1), Image.BOX).getpixel((0, 0)), r["color_label"]])

buf = io.BytesIO()
atlas.save(buf, "JPEG", quality=80)
out = f"mosaic/atlas_{name}.js"
os.makedirs("mosaic", exist_ok=True)
with open(out, "w") as f:
    f.write(f"(window.ATLASES=window.ATLASES||{{}}).{name}={{T:{T},COLS:{COLS},"
            f"TILES:{json.dumps(tiles, separators=(',', ':'))},"
            f"ATLAS:'data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode()}'}};\n")

print(f"Packed {len(tiles)} tiles from {args.source} into {out} ({os.path.getsize(out) // 1024} KB)")
