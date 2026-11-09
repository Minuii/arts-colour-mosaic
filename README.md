# Arts Colour Mosaic

A toolkit that collects artworks grouped by colour, organizes them into labelled colour datasets with numeric values, and packages them into a browser-based photomosaic generator that runs entirely offline.

It has two tile sources:

| Source | Folder | What's in it | Licence |
|---|---|---|---|
| **Art Institute of Chicago** (default) | `datasets_pd/` | 1,837 public-domain paintings | CC0, free to reuse |
| Google Arts & Culture | `datasets/` | 2,791 artworks | Mixed. **Some are still under copyright**, so this set is for educational use only |

![Sample mosaic output](mosaic/sample_output.png)

## Contents

- [Features](#features)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [Using the Mosaic App](#using-the-mosaic-app)
- [Building the Chicago Dataset](#building-the-chicago-dataset)
- [Building the Google Arts Dataset](#building-the-google-arts-dataset)
- [Datasets](#datasets)
- [Testing](#testing)

## Features

**Colour datasets**
- 12 colour groups: White, Gray, Pink, Purple, Blue, Teal, Green, Yellow, Orange, Red, Brown and Black
- Each group carries a numeric value for use in machine learning training
- A merged `all_colors.csv` per source covers every group in one file

**Photomosaic app**
- Runs as a single HTML file in any modern browser, with no server or installation
- Choose the tile source: Art Institute of Chicago (default) or Google Arts & Culture
- Upload your own image and build a mosaic from the bundled tile atlas
- Control grid density from 20 to 160 tiles across
- Adjust tile variety so repeated tiles are reduced or allowed
- Blend the original image into the mosaic for stronger recognition
- Zoom with the mouse wheel and pan by dragging
- Inspect details with a hover magnifier, where magnification strength is adjustable
- Download the finished mosaic as a full-resolution PNG

## Project Structure

```text
arts-colour-mosaic/
├── datasets_pd/           # Art Institute of Chicago, public-domain paintings (CC0)
│   ├── WHITE/ … BLACK/    # One folder per colour: images/ + metadata.csv
│   └── all_colors.csv
├── datasets/              # Google Arts & Culture (mixed rights)
│   ├── WHITE/ … RED/
│   └── all_colors.csv
├── mosaic/
│   ├── index.html         # Standalone mosaic creator
│   ├── atlas_chicago.js   # Tile atlas built from datasets_pd/
│   ├── atlas_google.js    # Tile atlas built from datasets/
│   ├── sample_output.png
│   └── sample_magnifier.png
├── scraper_aic.py         # Downloads AIC public-domain paintings by colour
├── scraper.py             # Scrapes Google Arts & Culture by colour
├── build_mosaic.py        # Packs a dataset into mosaic/atlas_<source>.js
├── validate.py            # Validates and normalizes a dataset
├── summarize.py           # Trims the Google dataset and reports counts
├── test_mosaic.py         # Automated tests for the mosaic viewer
├── plan.md                # Technical specification and colour value map
└── progress.md            # Implementation log
```

## Quick Start

1. Clone or download this repository.
2. Open `mosaic/index.html` in a modern web browser (Chrome, Firefox, Safari, or Edge).
3. Upload an image and adjust the settings.

No web server or build step is required for the mosaic app.

## Using the Mosaic App

1. **Pick the tile source** in the "Tiles from" menu. Art Institute of Chicago is selected by default. Switch to Google Arts & Culture if you want that set instead.
2. **Upload** a source image using the upload control.
3. **Set the grid** to choose how many tiles span the width. More tiles give more detail but take longer to render.
4. **Set variety** to limit how often the same tile repeats.
5. **Adjust blending** to mix the original image into the tiles. This keeps the subject recognizable.
6. **Explore** the result with the mouse wheel to zoom, drag to pan, and hover to open the magnifier.
7. **Download** the full-resolution PNG when you're satisfied.

If you publish mosaics (a portfolio site, social media), use the Chicago source. Every tile in it is public domain.

## Building the Chicago Dataset

The [Art Institute of Chicago API](https://api.artic.edu/docs/) is open and needs no key. `scraper_aic.py` asks it for artworks that are:

- **paintings** (`artwork_type_id = 1`), so no prints, photos, textiles or sculpture
- marked **public domain** by the museum (`is_public_domain = true`), whose images AIC releases under CC0
- with an image and a dominant colour on record

Each painting is put in one of the 12 colour groups from the dominant colour the API reports, then saved as a 128×128 centre-cropped tile.

```bash
pip install pillow
python scraper_aic.py              # 1. Download every public-domain painting (~1,900, a few minutes)
python validate.py datasets_pd     # 2. Check the CSVs and images
python build_mosaic.py             # 3. Rebuild mosaic/atlas_chicago.js
python test_mosaic.py              # 4. Optional: test the viewer
```

Useful options:

```bash
python scraper_aic.py --limit 200  # Quick test with 200 paintings
python scraper_aic.py --size 256   # Bigger tiles
```

Re-running is safe: images already on disk are skipped. To change how colours are grouped, edit `colour_group()` in `scraper_aic.py`, delete `datasets_pd/` and run it again.

## Building the Google Arts Dataset

```bash
python scraper.py                      # 1. Collect images and metadata by colour
python validate.py datasets            # 2. Check and normalize
python summarize.py                    # 3. Optionally trim and print counts
python build_mosaic.py --source datasets   # 4. Rebuild mosaic/atlas_google.js
```

Scraping Google Arts & Culture is subject to that site's terms of service, and it rate-limits heavy use. Many of its images are not public domain, so don't redistribute this set or mosaics built from it.

## Datasets

Both sources use the same CSV columns: `filename, asset_id, title, artist, museum, asset_path, thumbnail_url, dominant_hex, dom_r, dom_g, dom_b, aspect_ratio, color_label, color_hex, color_r, color_g, color_b, color_value`.

For Chicago rows, `asset_id` is the AIC artwork id and `asset_path` links to the artwork page on artic.edu. See `plan.md` for the colour value map.

### Tiles per colour

| Colour | Value | Chicago | Google Arts |
|---|---|---:|---:|
| White | 0 | 8 | 300 |
| Gray | 1 | 380 | 300 |
| Pink | 2 | 6 | 169 |
| Purple | 3 | 0 | 222 |
| Blue | 4 | 88 | 300 |
| Teal | 5 | 22 | 300 |
| Green | 6 | 15 | 300 |
| Yellow | 7 | 90 | 300 |
| Orange | 8 | 883 | 300 |
| Red | 9 | 181 | 300 |
| Brown | 10 | 155 | 0 |
| Black | 11 | 9 | 0 |
| **Total** | | **1,837** | **2,791** |

Chicago paintings are grouped by the dominant colour the museum records, and old varnish pushes most of them toward orange and gray. Google Arts was capped at 300 per colour, and Brown and Black were never collected because Google rate-limited the scraper.

## Testing

```bash
python test_mosaic.py
```

The suite checks the mosaic viewer's behaviour. Run it after changing `index.html` or an atlas file.
