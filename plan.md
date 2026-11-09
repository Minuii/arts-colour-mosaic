# Arts Colour Mosaic — Plan

(full history in [progress.md](progress.md))

## Goal
1. Build one dataset per colour, each colour with its own numeric value, for ML training. Two sources:
   - **Art Institute of Chicago** (`datasets_pd/`, default): public-domain paintings only, CC0 images, via the open AIC API.
   - **Google Arts & Culture** (`datasets/`): from `artsandculture.google.com/color`. Mixed rights, educational use only.
2. Use the small artwork thumbnails as tiles for a photo-mosaic page for a portfolio site.

Caps: 300 per colour, 500 for BROWN and BLACK (all available if fewer).

## Pipeline
| Step | File | Status |
|---|---|---|
| Chicago public-domain paintings by colour | `scraper_aic.py` | done (1,837 paintings, all 12 colours) |
| Scrape Google (API + pagination, thumbnails, CSV) | `scraper.py` | done for 10 of 12 colours |
| Validate / normalise CSVs | `validate.py` | done, 0 problems |
| Pack tiles into one atlas per source | `build_mosaic.py` | `atlas_chicago.js`, `atlas_google.js` |
| Mosaic generator page with source picker | `mosaic/index.html` | done, Chicago default, tested in headless Edge |
| Google BROWN and BLACK (500 each) | `scraper.py --colors BROWN BLACK` | **pending**: Google 429 block |

## Colour values
WHITE 0, GRAY 1, PINK 2, PURPLE 3, BLUE 4, TEAL 5, GREEN 6, YELLOW 7, ORANGE 8, RED 9, BROWN 10, BLACK 11. Edit `COLOR_VALUES` in `scraper.py` to change.

## Google result right now
| Colour | Value | Rows = images |
|---|---|---|
| WHITE | 0 | 300 |
| GRAY | 1 | 300 |
| PINK | 2 | 169 (all available) |
| PURPLE | 3 | 222 (all available) |
| BLUE | 4 | 300 |
| TEAL | 5 | 300 |
| GREEN | 6 | 300 |
| YELLOW | 7 | 300 |
| ORANGE | 8 | 300 |
| RED | 9 | 300 |
| BROWN | 10 | 0 pending |
| BLACK | 11 | 0 pending |
| **Total** | | **2,791** |

## Finishing the last two colours
Google temporarily blocked this IP (HTTP 429 and a captcha page). Wait a few hours or switch network, then run:
```
python scraper.py --colors BROWN BLACK
python validate.py --fix datasets
python build_mosaic.py --source datasets
```
Run one scraper at a time. The third command rebuilds the mosaic tiles so the dark colours are included.

## Using the mosaic
Open `mosaic/index.html` directly (double-click, no server needed). Pick the tile source ("Tiles from", Chicago by default), then choose any image. Sliders:
- **Tiles across**: more tiles means finer detail and a bigger PNG.
- **Variety**: higher means fewer repeats of the same artwork.
- **Original blend**: overlays the original photo for sharper likeness.

Then press Download PNG.

## Known limits and notes
- Weak colours: PINK (169) and PURPLE (222) will repeat more. Dark areas are thin until BROWN and BLACK are added.
- Matching uses weighted RGB distance, not Lab, which is fine for this purpose.
- Each atlas file is a few MB, which suits a portfolio page. Lower `T` in `build_mosaic.py` to shrink it.
- Google images have mixed rights. Use the Chicago source for anything public.
